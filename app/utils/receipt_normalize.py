import uuid
from app.utils.config_manager import config
from app.utils.receipt_categories import normalize_category, category_label


def _money(value, default='0.00'):
    if value is None or value == '':
        return default
    try:
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        return f"{float(cleaned):.2f}"
    except (TypeError, ValueError):
        return default


def _confidence(value, default='low'):
    if not value:
        return default
    level = str(value).strip().lower()
    if level in ('high', 'medium', 'low'):
        return level
    return default


def _payment_method(value):
    if not value:
        return 'unknown'
    method = str(value).strip().lower()
    if method in ('cash', 'credit', 'debit', 'unknown'):
        return method
    if 'credit' in method:
        return 'credit'
    if 'debit' in method:
        return 'debit'
    if 'cash' in method:
        return 'cash'
    return 'unknown'


def line_items_total(line_items):
    total = 0.0
    for item in line_items or []:
        try:
            total += float(item.get('line_total') or 0)
        except (TypeError, ValueError):
            continue
    return total


def amount_mismatch(header_total, line_items, tolerance=None):
    tol = tolerance
    if tol is None:
        tol = config.get('receipt_intelligence.amount_mismatch_tolerance', 0.05)
    try:
        header_amt = float(header_total or 0)
    except (TypeError, ValueError):
        return True
    lines_amt = line_items_total(line_items)
    if not line_items:
        return False
    return abs(header_amt - lines_amt) > float(tol)


def weighted_receipt_category(line_items):
    weights = {}
    for item in line_items or []:
        cat = item.get('category') or 'uncategorized'
        try:
            weight = abs(float(item.get('line_total') or 0))
        except (TypeError, ValueError):
            weight = 0.0
        weights[cat] = weights.get(cat, 0.0) + weight
    if not weights:
        return 'uncategorized'
    return max(weights, key=weights.get)


def normalize_line_item(raw, receipt_id):
    line_id = raw.get('line_id') or str(uuid.uuid4())
    line_total = _money(raw.get('line_total', raw.get('total', raw.get('price', 0))))
    qty = raw.get('quantity', 1)
    try:
        qty = float(qty)
        if qty <= 0:
            qty = 1
    except (TypeError, ValueError):
        qty = 1
    unit_price = raw.get('unit_price')
    unit_price_str = _money(unit_price) if unit_price not in (None, '') else ''
    is_discount = bool(raw.get('is_discount', False))
    if not is_discount:
        try:
            is_discount = float(line_total) < 0
        except (TypeError, ValueError):
            is_discount = False
    return {
        'line_id': line_id,
        'receipt_id': receipt_id,
        'name': str(raw.get('name') or raw.get('description') or 'Item').strip() or 'Item',
        'quantity': qty,
        'unit_price': unit_price_str,
        'line_total': line_total,
        'category': normalize_category(raw.get('category')),
        'category_confidence': _confidence(raw.get('category_confidence'), 'medium'),
        'is_discount': is_discount,
    }


def normalize_receipt_header(raw, source_image, receipt_id=None, parse_status='parsed', is_fallback=False):
    receipt_id = receipt_id or str(uuid.uuid4())
    merchant = str(raw.get('merchant') or '').strip()
    if not merchant and source_image:
        merchant = source_image.split('/')[-1]
    total = _money(raw.get('total', raw.get('amount', 0)))
    status = 'fallback' if is_fallback else parse_status
    return {
        'receipt_id': receipt_id,
        'merchant': merchant or 'Unknown merchant',
        'date': str(raw.get('date') or '').strip(),
        'subtotal': _money(raw.get('subtotal'), ''),
        'tax': _money(raw.get('tax'), ''),
        'tip': _money(raw.get('tip'), ''),
        'total': total,
        'payment_method': _payment_method(raw.get('payment_method')),
        'currency': str(raw.get('currency') or 'USD').strip().upper() or 'USD',
        'confidence': _confidence(raw.get('confidence'), 'low' if is_fallback else 'medium'),
        'parse_status': status,
        'source_image': source_image,
        'raw_summary': str(raw.get('raw_summary') or raw.get('note') or '').strip(),
    }


def build_line_items(raw_items, receipt_id, header_total, is_fallback=False):
    items = []
    for raw in raw_items or []:
        if isinstance(raw, dict):
            items.append(normalize_line_item(raw, receipt_id))
    if not items and header_total:
        items.append(
            normalize_line_item(
                {
                    'name': 'Receipt total',
                    'line_total': header_total,
                    'category': 'uncategorized',
                    'category_confidence': 'low' if is_fallback else 'medium',
                },
                receipt_id,
            )
        )
    return items


def evaluate_review_required(header, line_items, is_fallback=False):
    """Return True when user must confirm on review screen."""
    if is_fallback:
        return True
    min_auto = str(
        config.get('receipt_intelligence.auto_create_min_confidence', 'high')
    ).lower()
    review_levels = config.get(
        'receipt_intelligence.review_required_confidence', ['low', 'medium']
    )
    if not isinstance(review_levels, list):
        review_levels = ['low', 'medium']
    review_levels = [str(v).lower() for v in review_levels]

    confidence = header.get('confidence', 'low')
    if confidence in review_levels:
        return True
    if confidence != min_auto:
        return True
    if not header.get('merchant') or header.get('merchant') == 'Unknown merchant':
        return True
    if amount_mismatch(header.get('total'), line_items):
        return True
    for item in line_items:
        if item.get('category_confidence') == 'low':
            return True
    return False


def build_transaction_note(header, line_items):
    parts = []
    if line_items:
        parts.append(f"Receipt: {len(line_items)} item(s)")
    tax = header.get('tax')
    if tax and tax != '0.00':
        parts.append(f"Tax ${tax}")
    summary = header.get('raw_summary')
    if summary:
        parts.append(summary[:120])
    return ' | '.join(parts) if parts else 'Receipt transaction'


def build_parent_transaction(header, line_items, tx_id=None):
    """Build one parent transaction with line_items[] and receipt_meta."""
    from app.utils.normalize import normalize_transaction

    category = weighted_receipt_category(line_items)
    base = {
        'id': tx_id or str(uuid.uuid4()),
        'merchant': header.get('merchant', ''),
        'amount': header.get('total', '0.00'),
        'date': header.get('date') or '',
        'category': category,
        'note': build_transaction_note(header, line_items),
        'source': 'receipt',
        'receipt_id': header.get('receipt_id'),
        'line_items': line_items,
        'receipt_meta': {
            'subtotal': header.get('subtotal') or '',
            'tax': header.get('tax') or '',
            'tip': header.get('tip') or '',
            'payment_method': header.get('payment_method', 'unknown'),
            'currency': header.get('currency', 'USD'),
            'confidence': header.get('confidence', 'low'),
            'parse_status': header.get('parse_status', 'parsed'),
            'source_image': header.get('source_image', ''),
        },
    }
    tx = normalize_transaction(base)
    tx['source'] = 'receipt'
    tx['receipt_id'] = header.get('receipt_id')
    tx['line_items'] = line_items
    tx['receipt_meta'] = base['receipt_meta']
    tx['category'] = category
    return tx
