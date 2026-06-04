from app.utils.dashboard_stats import compute_dashboard_summaries, build_insights_context


def test_compute_dashboard_summaries_mixed_transactions():
    txs = [
        {'amount': '10.00', 'category': 'groceries', 'source': 'receipt', 'line_items': [
            {'line_total': '6.00', 'category': 'groceries'},
            {'line_total': '4.00', 'category': 'dining'},
        ]},
        {'amount': '5.00', 'category': 'gas'},
    ]
    s = compute_dashboard_summaries(txs)
    assert s['total_spend'] == 15.0
    assert s['receipt_count'] == 1
    assert s['receipt_spend'] == 10.0
    assert s['category_totals']['groceries'] == 10.0
    assert s['line_category_totals']['dining'] == 4.0


def test_backward_compatible_old_transactions():
    txs = [{'amount': '3.00', 'category': 'food', 'merchant': 'Legacy'}]
    s = compute_dashboard_summaries(txs)
    assert s['total_spend'] == 3.0
    assert s['receipt_count'] == 0
    ctx = build_insights_context(txs)
    assert ctx['receipt_count'] == 0
