import pytest
from app.utils.receipt_normalize import (
    normalize_line_item,
    normalize_receipt_header,
    build_line_items,
    build_parent_transaction,
    evaluate_review_required,
    amount_mismatch,
    weighted_receipt_category,
)
from app.utils.receipt_categories import normalize_category as cat_norm


def test_normalize_category_aliases():
    assert cat_norm('food') == 'dining'
    assert cat_norm('fuel') == 'gas'
    assert cat_norm('unknown_cat') == 'other'


def test_build_line_items_synthetic_when_empty():
    header_id = 'r-test-1'
    items = build_line_items([], header_id, '12.50', is_fallback=False)
    assert len(items) == 1
    assert items[0]['name'] == 'Receipt total'
    assert items[0]['line_total'] == '12.50'


def test_amount_mismatch_detected():
    header_total = '10.00'
    lines = [
        normalize_line_item({'name': 'A', 'line_total': '3.00', 'category': 'groceries'}, 'r1'),
        normalize_line_item({'name': 'B', 'line_total': '4.00', 'category': 'groceries'}, 'r1'),
    ]
    assert amount_mismatch(header_total, lines, tolerance=0.05) is True


def test_weighted_receipt_category():
    lines = [
        {'category': 'dining', 'line_total': '5.00'},
        {'category': 'groceries', 'line_total': '20.00'},
    ]
    assert weighted_receipt_category(lines) == 'groceries'


def test_build_parent_transaction_shape():
    header = normalize_receipt_header(
        {'merchant': 'Store', 'total': 15.0, 'confidence': 'high', 'tax': 1.0},
        'uploads/test.png',
        receipt_id='rec-1',
    )
    lines = build_line_items(
        [{'name': 'Item', 'line_total': 15.0, 'category': 'shopping'}],
        'rec-1',
        '15.00',
    )
    tx = build_parent_transaction(header, lines)
    assert tx['source'] == 'receipt'
    assert tx['receipt_id'] == 'rec-1'
    assert len(tx['line_items']) == 1
    assert tx['receipt_meta']['tax'] == '1.00'
    assert tx['amount'] == '15.00'


def test_evaluate_review_required_fallback():
    header = normalize_receipt_header({}, 'uploads/x.png', is_fallback=True)
    assert evaluate_review_required(header, [], is_fallback=True) is True


def test_evaluate_review_required_high_confidence_ok():
    header = normalize_receipt_header(
        {'merchant': 'Shop', 'total': 10.0, 'confidence': 'high'},
        'uploads/x.png',
    )
    lines = build_line_items(
        [{'name': 'Item', 'line_total': 10.0, 'category': 'groceries', 'category_confidence': 'high'}],
        header['receipt_id'],
        '10.00',
    )
    assert evaluate_review_required(header, lines, is_fallback=False) is False
