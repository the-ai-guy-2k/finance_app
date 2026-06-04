from app.utils.dashboard_stats import compute_dashboard_summaries, build_insights_context


def test_behavioral_rows_in_summaries():
    txs = [
        {
            'source': 'receipt',
            'merchant': 'Mart',
            'amount': '10',
            'behavioral_meta': {
                'essential': {'classification': 'essential', 'essential_score': 0.9},
                'trip': {'trip_type': 'refill_trip'},
                'summary': {'narrative_short': 'Refill · Essential'},
                'savings': {'opportunities': []},
                'behavioral_tags': [{'tag': 'recurring', 'strength': 0.8}],
            },
        }
    ]
    s = compute_dashboard_summaries(txs)
    assert s['behavioral_receipt_count'] == 1
    assert s['behavioral_rows'][0]['trip_type'] == 'refill_trip'

    ctx = build_insights_context(txs)
    assert ctx['behavioral_summaries']
    assert ctx['receipt_summaries'][0].get('behavioral')
