import os
from app.services.openai_receipt_service import OpenAIReceiptParsingService
from app.services.behavioral_receipt_intelligence_service import (
    BehavioralReceiptIntelligenceService,
)
from app.utils.receipt_normalize import (
    normalize_receipt_header,
    build_line_items,
    build_parent_transaction,
    evaluate_review_required,
    amount_mismatch,
)
from app.utils.config_manager import config
from app.utils.logging_service import log_info


class ReceiptIntelligenceService:
    """Orchestrate receipt parse, categorization, confidence gate, and transaction build."""

    def __init__(self, parser=None, behavioral=None):
        self.parser = parser or OpenAIReceiptParsingService()
        self.behavioral = behavioral or BehavioralReceiptIntelligenceService()

    def attach_behavioral(self, transaction, all_transactions=None):
        """Apply v2 behavioral_meta before persisting a receipt transaction."""
        return self.behavioral.enrich_transaction(transaction, all_transactions=all_transactions)

    def process_upload(self, file_path, source_image):
        """
        Parse receipt image and decide auto-commit vs review.

        Returns dict:
          auto_commit: bool
          receipt_id: str
          transaction: dict (parent tx with line_items) when auto_commit
          pending: dict bundle for review queue when not auto_commit
          header: receipt header dict
          line_items: list
        """
        parsed = self.parser.parse_receipt_structured(file_path)
        is_fallback = parsed.get('is_fallback', False)
        receipt_id = parsed.get('receipt_id')

        header = normalize_receipt_header(
            parsed,
            source_image=source_image,
            receipt_id=receipt_id,
            parse_status='parsed',
            is_fallback=is_fallback,
        )
        line_items = build_line_items(
            parsed.get('items') or [],
            header['receipt_id'],
            header['total'],
            is_fallback=is_fallback,
        )

        if amount_mismatch(header['total'], line_items):
            if header['confidence'] == 'high':
                header['confidence'] = 'medium'

        needs_review = evaluate_review_required(header, line_items, is_fallback=is_fallback)
        transaction = build_parent_transaction(header, line_items)

        if needs_review:
            header['parse_status'] = 'review_pending'
            transaction['receipt_meta']['parse_status'] = 'review_pending'
            pending = {
                'receipt_id': header['receipt_id'],
                'source_image': source_image,
                'header': header,
                'line_items': line_items,
                'transaction_draft': transaction,
            }
            log_info(f"Receipt {header['receipt_id']} queued for review (confidence={header['confidence']})")
            return {
                'auto_commit': False,
                'receipt_id': header['receipt_id'],
                'transaction': None,
                'pending': pending,
                'header': header,
                'line_items': line_items,
            }

        header['parse_status'] = 'confirmed'
        transaction['receipt_meta']['parse_status'] = 'confirmed'
        log_info(
            f"Receipt {header['receipt_id']} auto-committed: "
            f"{header['merchant']} ${header['total']} ({len(line_items)} items)"
        )
        return {
            'auto_commit': True,
            'receipt_id': header['receipt_id'],
            'transaction': transaction,
            'pending': None,
            'header': header,
            'line_items': line_items,
        }

    def confirm_pending(self, pending_bundle, form_data):
        """Apply user edits from review form and return final transaction + header."""
        header = dict(pending_bundle.get('header') or {})
        line_items = [dict(li) for li in (pending_bundle.get('line_items') or [])]

        header['merchant'] = (form_data.get('merchant') or header.get('merchant', '')).strip()
        header['date'] = (form_data.get('date') or header.get('date', '')).strip()
        header['total'] = form_data.get('total') or header.get('total', '0.00')
        header['subtotal'] = form_data.get('subtotal') or header.get('subtotal', '')
        header['tax'] = form_data.get('tax') or header.get('tax', '')
        header['tip'] = form_data.get('tip') or header.get('tip', '')
        header['payment_method'] = form_data.get('payment_method') or header.get('payment_method', 'unknown')
        header['confidence'] = 'high'
        header['parse_status'] = 'confirmed'

        names = form_data.getlist('line_name') if hasattr(form_data, 'getlist') else []
        if not names and isinstance(form_data, dict):
            names = form_data.get('line_name', [])
            if isinstance(names, str):
                names = [names]
        totals = form_data.getlist('line_total') if hasattr(form_data, 'getlist') else form_data.get('line_total', [])
        categories = form_data.getlist('line_category') if hasattr(form_data, 'getlist') else form_data.get('line_category', [])
        line_ids = form_data.getlist('line_id') if hasattr(form_data, 'getlist') else form_data.get('line_id', [])

        if names:
            updated_lines = []
            for idx, name in enumerate(names):
                if not str(name).strip():
                    continue
                line = line_items[idx] if idx < len(line_items) else {}
                updated_lines.append({
                    'line_id': line_ids[idx] if idx < len(line_ids) else line.get('line_id'),
                    'receipt_id': header['receipt_id'],
                    'name': name,
                    'quantity': line.get('quantity', 1),
                    'unit_price': line.get('unit_price', ''),
                    'line_total': totals[idx] if idx < len(totals) else line.get('line_total'),
                    'category': categories[idx] if idx < len(categories) else line.get('category'),
                    'category_confidence': 'high',
                    'is_discount': line.get('is_discount', False),
                })
            from app.utils.receipt_normalize import normalize_line_item

            line_items = [
                normalize_line_item(raw, header['receipt_id']) for raw in updated_lines
            ]

        tx_id = pending_bundle.get('transaction_draft', {}).get('id')
        transaction = build_parent_transaction(header, line_items, tx_id=tx_id)
        return header, transaction
