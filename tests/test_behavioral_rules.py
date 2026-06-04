import pytest
from app.utils.behavioral_rules import (
    compute_essential,
    classify_trip,
    derive_behavioral_tags,
    detect_habits,
    compute_savings_opportunities,
)
from app.utils.merchant_memory import build_merchant_profiles, merchant_key


def _line(name, category, total):
    return {
        'name': name,
        'category': category,
        'line_total': total,
        'is_discount': False,
    }


def test_compute_essential_grocery_high():
    lines = [_line('Milk', 'groceries', 8), _line('Bread', 'groceries', 4)]
    result = compute_essential(lines)
    assert result['essential_score'] >= 0.7
    assert result['classification'] in ('essential', 'mixed', 'discretionary')


def test_compute_essential_entertainment_low():
    lines = [_line('Movie ticket', 'entertainment', 15)]
    result = compute_essential(lines)
    assert result['essential_score'] <= 0.4
    assert result['classification'] in ('non_essential', 'discretionary', 'unknown')


def test_classify_trip_convenience():
    header = {'merchant': '7-Eleven', 'total': '12.00'}
    lines = [_line('Snacks', 'shopping', 12)]
    trip = classify_trip(header, lines, {})
    assert trip['trip_type'] == 'convenience_run'


def test_classify_trip_grocery_restock():
    header = {'merchant': 'Kroger Grocery', 'total': '85.00'}
    lines = [
        _line(f'Item {i}', 'groceries', 10) for i in range(6)
    ]
    trip = classify_trip(header, lines, {})
    assert trip['trip_type'] == 'grocery_restock'


def test_merchant_profiles_and_habits():
    txs = [
        {
            'source': 'receipt',
            'merchant': 'Kroger',
            'amount': '40.00',
            'receipt_id': 'r1',
            'behavioral_meta': {
                'trip': {'trip_type': 'grocery_restock'},
                'essential': {'essential_score': 0.8},
            },
        },
        {
            'source': 'receipt',
            'merchant': 'Kroger',
            'amount': '35.00',
            'receipt_id': 'r2',
            'behavioral_meta': {
                'trip': {'trip_type': 'refill_trip'},
                'essential': {'essential_score': 0.75},
            },
        },
    ]
    profiles = build_merchant_profiles(txs, exclude_receipt_id='r3')
    key = merchant_key('Kroger')
    assert profiles[key]['visit_count'] == 2
    assert profiles[key]['avg_basket'] == 37.5

    habits = detect_habits(
        {'merchant': 'Kroger'},
        [_line('Milk', 'groceries', 5)],
        profiles[key],
        txs,
        'r3',
    )
    assert habits['repeat_merchant'] is True


def test_savings_convenience_flag():
    header = {'merchant': '7-Eleven', 'total': '10'}
    lines = [_line('Candy', 'shopping', 10)]
    trip = {'trip_type': 'convenience_run', 'reason_codes': ['convenience_merchant']}
    essential = {'classification': 'non_essential', 'essential_score': 0.2}
    tags = derive_behavioral_tags(header, lines, trip, essential, {}, {'repeat_merchant': False})
    savings = compute_savings_opportunities(header, lines, trip, tags, essential)
    assert savings['convenience_spend_detected'] is True
    assert len(savings['opportunities']) >= 1
