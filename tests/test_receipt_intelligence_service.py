import pytest
from unittest.mock import MagicMock
from app.services.receipt_intelligence_service import ReceiptIntelligenceService


@pytest.fixture
def high_confidence_parse():
    return {
        'receipt_id': 'rid-1',
        'merchant': 'Test Mart',
        'date': '2026-06-01',
        'subtotal': 9.0,
        'tax': 1.0,
        'tip': 0.0,
        'total': 10.0,
        'payment_method': 'credit',
        'currency': 'USD',
        'category': 'groceries',
        'confidence': 'high',
        'raw_summary': 'Parsed ok',
        'items': [
            {
                'name': 'Milk',
                'quantity': 1,
                'line_total': 10.0,
                'category': 'groceries',
                'category_confidence': 'high',
            }
        ],
        'is_fallback': False,
    }


@pytest.fixture
def low_confidence_parse():
    return {
        'receipt_id': 'rid-2',
        'merchant': '',
        'total': 5.0,
        'confidence': 'low',
        'items': [],
        'is_fallback': True,
    }


def test_process_upload_auto_commit(high_confidence_parse):
    parser = MagicMock()
    parser.parse_receipt_structured.return_value = high_confidence_parse
    svc = ReceiptIntelligenceService(parser=parser)
    result = svc.process_upload('/tmp/r.png', 'uploads/r.png')
    assert result['auto_commit'] is True
    assert result['transaction']['source'] == 'receipt'
    assert len(result['line_items']) >= 1


def test_process_upload_requires_review(low_confidence_parse):
    parser = MagicMock()
    parser.parse_receipt_structured.return_value = low_confidence_parse
    svc = ReceiptIntelligenceService(parser=parser)
    result = svc.process_upload('/tmp/r.png', 'uploads/r.png')
    assert result['auto_commit'] is False
    assert result['pending']['receipt_id'] == 'rid-2'
    assert result['pending']['transaction_draft']['source'] == 'receipt'


def test_confirm_pending_builds_transaction(high_confidence_parse):
    parser = MagicMock()
    svc = ReceiptIntelligenceService(parser=parser)
    pending = {
        'receipt_id': 'rid-1',
        'header': {
            'receipt_id': 'rid-1',
            'merchant': 'Test Mart',
            'date': '2026-06-01',
            'total': '10.00',
            'subtotal': '',
            'tax': '',
            'tip': '',
            'payment_method': 'credit',
            'currency': 'USD',
            'confidence': 'medium',
            'parse_status': 'review_pending',
            'source_image': 'uploads/r.png',
            'raw_summary': '',
        },
        'line_items': [
            {
                'line_id': 'l1',
                'receipt_id': 'rid-1',
                'name': 'Milk',
                'quantity': 1,
                'unit_price': '',
                'line_total': '10.00',
                'category': 'groceries',
                'category_confidence': 'medium',
                'is_discount': False,
            }
        ],
        'transaction_draft': {'id': 'tx-draft-1'},
    }
    from werkzeug.datastructures import ImmutableMultiDict

    form = ImmutableMultiDict(
        [
            ('merchant', 'Test Mart Updated'),
            ('date', '2026-06-02'),
            ('total', '10.00'),
            ('line_id', 'l1'),
            ('line_name', 'Milk'),
            ('line_total', '10.00'),
            ('line_category', 'groceries'),
        ]
    )
    header, tx = svc.confirm_pending(pending, form)
    assert header['merchant'] == 'Test Mart Updated'
    assert tx['merchant'] == 'Test Mart Updated'
    assert tx['receipt_meta']['parse_status'] == 'confirmed'
