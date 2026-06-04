"""Rolling merchant statistics from transaction history."""

import re


def merchant_key(name):
    if not name:
        return 'unknown_merchant'
    slug = re.sub(r'[^a-z0-9]+', '_', str(name).lower()).strip('_')
    return slug[:64] or 'unknown_merchant'


def _tx_amount(tx):
    try:
        return float(tx.get('amount') or 0)
    except (TypeError, ValueError):
        return 0.0


def build_merchant_profiles(transactions, exclude_receipt_id=None, window_days=90):
    """Aggregate per-merchant stats from receipt-sourced transactions."""
    profiles = {}
    for tx in transactions or []:
        if tx.get('source') != 'receipt':
            continue
        if exclude_receipt_id and tx.get('receipt_id') == exclude_receipt_id:
            continue
        key = merchant_key(tx.get('merchant'))
        amt = _tx_amount(tx)
        trip = (tx.get('behavioral_meta') or {}).get('trip', {}).get('trip_type', 'unknown')
        essential = (tx.get('behavioral_meta') or {}).get('essential', {}).get('essential_score', 0.5)
        entry = profiles.setdefault(
            key,
            {
                'merchant_key': key,
                'visit_count': 0,
                'total_spend': 0.0,
                'trip_counts': {},
                'essential_scores': [],
            },
        )
        entry['visit_count'] += 1
        entry['total_spend'] += amt
        entry['trip_counts'][trip] = entry['trip_counts'].get(trip, 0) + 1
        entry['essential_scores'].append(essential)
    for entry in profiles.values():
        visits = entry['visit_count'] or 1
        entry['avg_basket'] = round(entry['total_spend'] / visits, 2)
        if entry['trip_counts']:
            entry['dominant_trip_type'] = max(entry['trip_counts'], key=entry['trip_counts'].get)
        else:
            entry['dominant_trip_type'] = 'unknown'
        scores = entry['essential_scores']
        entry['essential_bias'] = round(sum(scores) / len(scores), 2) if scores else 0.5
    return profiles


def profile_for_merchant(profiles, merchant_name):
    return profiles.get(merchant_key(merchant_name), {})
