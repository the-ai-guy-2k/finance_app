import pytest
from app.services.behavioral_receipt_intelligence_service import (
    BehavioralReceiptIntelligenceService,
)
from app.services.receipt_intelligence_service import ReceiptIntelligenceService


def _receipt_tx(merchant='Walmart', total='50.00', receipt_id='rx-1'):
    return {
        'id': 'tx-1',
        'source': 'receipt',
        'receipt_id': receipt_id,
        'merchant': merchant,
        'amount': total,
        'date': '2026-06-01',
        'category': 'groceries',
        'line_items': [
            {
                'line_id': 'l1',
                'name': 'Milk',
                'line_total': '4.00',
                'category': 'groceries',
                'is_discount': False,
            },
            {
                'line_id': 'l2',
                'name': 'Bread',
                'line_total': '3.00',
                'category': 'groceries',
                'is_discount': False,
            },
            {
                'line_id': 'l3',
                'name': 'Eggs',
                'line_total': '5.00',
                'category': 'groceries',
                'is_discount': False,
            },
            {
                'line_id': 'l4',
                'name': 'Rice',
                'line_total': '6.00',
                'category': 'groceries',
                'is_discount': False,
            },
            {
                'line_id': 'l5',
                'name': 'Chicken',
                'line_total': '32.00',
                'category': 'groceries',
                'is_discount': False,
            },
        ],
        'receipt_meta': {'parse_status': 'confirmed'},
    }


def test_analyze_attaches_full_behavioral_meta():
    svc = BehavioralReceiptIntelligenceService()
    meta = svc.analyze(_receipt_tx())
    assert meta is not None
    assert meta['version'] == '2.0'
    assert 'essential' in meta
    assert meta['essential']['essential_score'] is not None
    assert meta['trip']['trip_type'] in (
        'grocery_restock',
        'refill_trip',
        'mixed_basket',
        'unknown',
    )
    assert isinstance(meta['behavioral_tags'], list)
    assert 'summary' in meta
    assert meta['summary']['what_happened']
    assert 'merchant_intelligence' in meta
    assert 'habits' in meta
    assert 'savings' in meta


def test_enrich_transaction_adds_behavioral_meta():
    svc = BehavioralReceiptIntelligenceService()
    tx = svc.enrich_transaction(_receipt_tx())
    assert 'behavioral_meta' in tx
    assert tx['behavioral_meta']['essential_score'] == tx['behavioral_meta']['essential']['essential_score']


def test_non_receipt_returns_none():
    svc = BehavioralReceiptIntelligenceService()
    assert svc.analyze({'source': 'manual', 'amount': '10'}) is None


def test_receipt_intelligence_attach_behavioral():
    ri = ReceiptIntelligenceService()
    tx = _receipt_tx()
    enriched = ri.attach_behavioral(tx, [])
    assert enriched.get('behavioral_meta')


def test_backward_compat_transaction_without_meta():
    """Transactions without behavioral_meta remain valid dicts."""
    legacy = {
        'id': 'old-1',
        'merchant': 'Store',
        'amount': '20.00',
        'source': 'receipt',
        'line_items': [],
    }
    assert 'behavioral_meta' not in legacy
    from app.utils.dashboard_stats import compute_dashboard_summaries

    summaries = compute_dashboard_summaries([legacy])
    assert summaries['receipt_count'] == 1
    assert summaries['behavioral_receipt_count'] == 0
