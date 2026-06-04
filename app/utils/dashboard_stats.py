from app.utils.receipt_categories import category_label


def compute_dashboard_summaries(transactions):
    """Aggregate spend, receipt metrics, and category totals."""
    total_spend = 0.0
    receipt_spend = 0.0
    receipt_count = 0
    category_totals = {}
    line_category_totals = {}

    for tx in transactions or []:
        if not isinstance(tx, dict):
            continue
        try:
            amt = float(tx.get('amount') or 0)
        except (TypeError, ValueError):
            amt = 0.0
        total_spend += amt

        cat = tx.get('category') or 'uncategorized'
        category_totals[cat] = category_totals.get(cat, 0.0) + amt

        if tx.get('source') == 'receipt':
            receipt_count += 1
            receipt_spend += amt
            for item in tx.get('line_items') or []:
                line_cat = item.get('category') or cat
                try:
                    line_amt = float(item.get('line_total') or 0)
                except (TypeError, ValueError):
                    line_amt = 0.0
                line_category_totals[line_cat] = (
                    line_category_totals.get(line_cat, 0.0) + line_amt
                )

    category_rows = [
        {
            'slug': slug,
            'label': category_label(slug),
            'total': round(total, 2),
        }
        for slug, total in sorted(category_totals.items(), key=lambda x: -x[1])
    ]

    behavioral_rows = _behavioral_aggregate_rows(transactions)

    return {
        'total_spend': round(total_spend, 2),
        'receipt_spend': round(receipt_spend, 2),
        'receipt_count': receipt_count,
        'category_totals': category_totals,
        'category_rows': category_rows,
        'line_category_totals': line_category_totals,
        'behavioral_rows': behavioral_rows,
        'behavioral_receipt_count': len(behavioral_rows),
    }


def _behavioral_aggregate_rows(transactions):
    """Summarize receipts that have behavioral_meta for insights/dashboard."""
    rows = []
    for tx in transactions or []:
        if tx.get('source') != 'receipt':
            continue
        meta = tx.get('behavioral_meta') or {}
        if not meta:
            continue
        essential = meta.get('essential') or {}
        trip = meta.get('trip') or {}
        summary = meta.get('summary') or {}
        savings = meta.get('savings') or {}
        rows.append(
            {
                'merchant': tx.get('merchant'),
                'amount': tx.get('amount'),
                'trip_type': trip.get('trip_type', 'unknown'),
                'essential_classification': essential.get('classification', 'unknown'),
                'essential_score': essential.get('essential_score'),
                'narrative_short': summary.get('narrative_short'),
                'savings_opportunity_count': len(savings.get('opportunities') or []),
                'tags': [t.get('tag') for t in (meta.get('behavioral_tags') or [])[:5]],
            }
        )
    return rows


def build_insights_context(transactions):
    """Compact context for insights generation."""
    summaries = compute_dashboard_summaries(transactions)
    receipt_summaries = []
    for tx in transactions or []:
        if tx.get('source') != 'receipt':
            continue
        entry = {
            'merchant': tx.get('merchant'),
            'amount': tx.get('amount'),
            'category': tx.get('category'),
            'line_count': len(tx.get('line_items') or []),
            'lines': [
                {
                    'name': li.get('name'),
                    'line_total': li.get('line_total'),
                    'category': li.get('category'),
                }
                for li in (tx.get('line_items') or [])[:10]
            ],
        }
        meta = tx.get('behavioral_meta') or {}
        if meta:
            entry['behavioral'] = {
                'trip_type': (meta.get('trip') or {}).get('trip_type'),
                'essential_classification': (meta.get('essential') or {}).get('classification'),
                'essential_score': meta.get('essential_score'),
                'tags': [t.get('tag') for t in (meta.get('behavioral_tags') or [])],
                'summary_short': (meta.get('summary') or {}).get('narrative_short'),
                'savings_flags': (meta.get('savings') or {}).get('avoidable_spend_indicators'),
                'habits': (meta.get('habits') or {}).get('spending_pattern_indicators'),
            }
        receipt_summaries.append(entry)
    return {
        'transactions': transactions,
        'category_totals': summaries['category_totals'],
        'line_category_totals': summaries['line_category_totals'],
        'receipt_count': summaries['receipt_count'],
        'receipt_summaries': receipt_summaries[:15],
        'behavioral_summaries': summaries.get('behavioral_rows', [])[:15],
        'total_spend': summaries['total_spend'],
    }
