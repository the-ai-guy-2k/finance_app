"""Orchestrate Receipt Intelligence v2 behavioral layer."""

from datetime import datetime, timezone

from app.utils.config_manager import config
from app.utils.merchant_memory import build_merchant_profiles, profile_for_merchant
from app.utils.behavioral_rules import (
    compute_essential,
    classify_trip,
    derive_behavioral_tags,
    detect_habits,
    compute_savings_opportunities,
    build_merchant_intelligence,
    build_behavioral_summary,
)
from app.utils.behavioral_normalize import normalize_confidence
from app.utils.logging_service import log_info


class BehavioralReceiptIntelligenceService:
    """Attach behavioral_meta to receipt transactions after v1 data is ready."""

    def analyze(self, transaction, all_transactions=None):
        """
        Compute behavioral_meta for a receipt parent transaction.

        Returns behavioral_meta dict (does not mutate transaction unless caller merges).
        """
        if not transaction or transaction.get('source') != 'receipt':
            return None

        line_items = transaction.get('line_items') or []
        header = {
            'merchant': transaction.get('merchant'),
            'date': transaction.get('date'),
            'total': transaction.get('amount'),
            'receipt_id': transaction.get('receipt_id'),
        }
        receipt_id = transaction.get('receipt_id')
        history = all_transactions if all_transactions is not None else []
        window = int((config.get('behavioral_intelligence') or {}).get('history_window_days', 90))

        profiles = build_merchant_profiles(
            history,
            exclude_receipt_id=receipt_id,
            window_days=window,
        )
        merchant_profile = profile_for_merchant(profiles, header['merchant'])

        essential = compute_essential(line_items)
        trip = classify_trip(header, line_items, merchant_profile)
        habits = detect_habits(header, line_items, merchant_profile, history, receipt_id)
        tags = derive_behavioral_tags(header, line_items, trip, essential, merchant_profile, habits)
        savings = compute_savings_opportunities(header, line_items, trip, tags, essential)
        merchant_intel = build_merchant_intelligence(header, merchant_profile, trip)
        summary = build_behavioral_summary(
            header, essential, trip, tags, savings, habits, merchant_intel
        )

        rule_confidence = normalize_confidence(trip.get('confidence'), 'medium')
        if essential.get('classification') == 'unknown':
            rule_confidence = 'low'

        tags_list = [
            {
                'tag': tag,
                'strength': strength,
                'confidence': rule_confidence,
            }
            for tag, strength in sorted(tags.items(), key=lambda x: -x[1])
        ]
        essential['confidence'] = rule_confidence
        trip['trip_confidence'] = rule_confidence

        behavioral_meta = {
            'version': '2.0',
            'computed_at': datetime.now(timezone.utc).isoformat(),
            'essential': essential,
            'trip': trip,
            'behavioral_tags': tags_list,
            'savings': savings,
            'merchant_intelligence': merchant_intel,
            'habits': habits,
            'summary': summary,
            'confidence': rule_confidence,
            'reason_codes': list(
                dict.fromkeys(
                    (essential.get('reason_codes') or [])
                    + (trip.get('reason_codes') or [])
                )
            ),
        }
        behavioral_meta['essential_score'] = essential.get('essential_score')
        log_info(
            f"Behavioral analysis {receipt_id}: trip={trip.get('trip_type')} "
            f"essential={essential.get('classification')}"
        )
        return behavioral_meta

    def enrich_transaction(self, transaction, all_transactions=None):
        """Return copy of transaction with behavioral_meta attached."""
        tx = dict(transaction)
        meta = self.analyze(tx, all_transactions=all_transactions)
        if meta:
            tx['behavioral_meta'] = meta
        return tx
