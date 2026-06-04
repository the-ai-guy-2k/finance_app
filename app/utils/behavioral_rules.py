"""Deterministic behavioral rules for Receipt Intelligence v2."""

import re
from app.utils.config_manager import config
from app.utils.behavioral_normalize import (
    clamp_score,
    normalize_trip_type,
    normalize_essential_classification,
)

# Category priors (essential score 0-1)
CATEGORY_ESSENTIAL_PRIOR = {
    'groceries': 0.85,
    'health': 0.9,
    'utilities': 0.95,
    'housing': 0.95,
    'transport': 0.7,
    'fuel': 0.75,
    'insurance': 0.9,
    'education': 0.75,
    'personal_care': 0.65,
    'dining': 0.35,
    'entertainment': 0.15,
    'shopping': 0.25,
    'subscriptions': 0.4,
    'gifts': 0.3,
    'other': 0.5,
}

ESSENTIAL_KEYWORDS = re.compile(
    r'\b(medicine|medical|pharmacy|prescription|rent|mortgage|utility|electric|'
    r'water|gas bill|insurance|diaper|baby formula|milk|bread|eggs|rice|'
    r'fuel|gasoline|diesel|repair|maintenance|toilet paper)\b',
    re.I,
)
NON_ESSENTIAL_KEYWORDS = re.compile(
    r'\b(candy|toy|game|luxury|jewelry|cosmetic|perfume|soda|chips|'
    r'lottery|alcohol|wine|beer|streaming|subscription entertainment)\b',
    re.I,
)

CONVENIENCE_MERCHANTS = re.compile(
    r'\b(7-?eleven|circle k|wawa|sheetz|quik.?trip|speedway|'
    r'corner store|gas station mart)\b',
    re.I,
)
GROCERY_MERCHANTS = re.compile(
    r'\b(walmart|kroger|safeway|aldi|costco|whole foods|trader joe|'
    r'publix|heb|grocery|supermarket|food lion)\b',
    re.I,
)

LUXURY_KEYWORDS = re.compile(r'\b(luxury|premium|designer|spa|jewelry)\b', re.I)
SOCIAL_KEYWORDS = re.compile(r'\b(restaurant|cafe|bar|pub|grill|pizza)\b', re.I)
HEALTH_KEYWORDS = re.compile(r'\b(pharmacy|vitamin|medicine|clinic|dental)\b', re.I)
PRODUCTIVITY_KEYWORDS = re.compile(r'\b(office|software|stationery|printer)\b', re.I)
IMPULSE_KEYWORDS = re.compile(r'\b(candy|snack|magazine|lottery|impulse)\b', re.I)
MAINTENANCE_KEYWORDS = re.compile(r'\b(oil change|filter|bulb|repair|parts|hardware)\b', re.I)


def _bi_cfg():
    return config.get('behavioral_intelligence') or {}


def _line_amount(line):
    try:
        return abs(float(line.get('line_total') or 0))
    except (TypeError, ValueError):
        return 0.0


def score_line_essential(line):
    """Return essential_score 0-1 for one line item."""
    cat = (line.get('category') or 'other').lower().replace(' ', '_')
    base = CATEGORY_ESSENTIAL_PRIOR.get(cat, 0.5)
    name = line.get('name') or ''
    if ESSENTIAL_KEYWORDS.search(name):
        base = max(base, 0.85)
    if NON_ESSENTIAL_KEYWORDS.search(name):
        base = min(base, 0.2)
    return clamp_score(base)


def compute_essential(line_items):
    """Receipt-level essential scoring."""
    cfg = _bi_cfg()
    high_th = float(cfg.get('essential_threshold_high', 0.75))
    low_th = float(cfg.get('essential_threshold_low', 0.35))
    spread_th = float(cfg.get('mixed_spread_threshold', 0.40))

    if not line_items:
        return {
            'essential_score': 0.5,
            'non_essential_score': 0.5,
            'classification': 'unknown',
            'reason_codes': ['no_line_items'],
        }

    line_scores = []
    weighted_sum = 0.0
    total_weight = 0.0
    for line in line_items:
        if line.get('is_discount'):
            continue
        score = score_line_essential(line)
        amt = _line_amount(line) or 1.0
        line_scores.append(score)
        weighted_sum += score * amt
        total_weight += amt

    essential_score = clamp_score(weighted_sum / total_weight if total_weight else 0.5)
    non_essential_score = clamp_score(1.0 - essential_score)
    spread = (max(line_scores) - min(line_scores)) if len(line_scores) > 1 else 0.0

    reason_codes = ['category_priors']
    if spread > spread_th:
        classification = 'mixed'
        reason_codes.append('mixed_spread')
    elif essential_score >= high_th:
        classification = 'essential'
        reason_codes.append('threshold_high')
    elif essential_score <= low_th:
        classification = 'non_essential'
        reason_codes.append('threshold_low')
    else:
        classification = 'discretionary'
        reason_codes.append('threshold_mid')

    return {
        'essential_score': essential_score,
        'non_essential_score': non_essential_score,
        'classification': normalize_essential_classification(classification),
        'reason_codes': reason_codes,
        'line_spread': round(spread, 2),
    }


def classify_trip(header, line_items, merchant_profile):
    """Classify trip type from basket shape and merchant context."""
    merchant = header.get('merchant') or ''
    categories = {(li.get('category') or 'other').lower() for li in line_items if not li.get('is_discount')}
    n_lines = len([li for li in line_items if not li.get('is_discount')])
    total = 0.0
    try:
        total = float(header.get('total') or 0)
    except (TypeError, ValueError):
        pass

    reason_codes = []
    trip_type = 'unknown'

    if GROCERY_MERCHANTS.search(merchant) or 'groceries' in categories:
        if n_lines >= 5:
            trip_type = 'grocery_restock'
            reason_codes.append('many_grocery_lines')
        else:
            trip_type = 'refill_trip'
            reason_codes.append('grocery_merchant_small_basket')
    elif CONVENIENCE_MERCHANTS.search(merchant):
        trip_type = 'convenience_run'
        reason_codes.append('convenience_merchant')
    elif n_lines <= 2 and total < 25:
        trip_type = 'impulse_purchase'
        reason_codes.append('small_basket')
    elif 'health' in categories or HEALTH_KEYWORDS.search(merchant):
        trip_type = 'emergency_purchase' if total > 80 else 'refill_trip'
        reason_codes.append('health_signal')
    elif MAINTENANCE_KEYWORDS.search(merchant) or 'transport' in categories:
        trip_type = 'maintenance_purchase'
        reason_codes.append('maintenance_signal')
    elif len(categories) >= 3:
        trip_type = 'mixed_basket'
        reason_codes.append('multi_category')
    elif merchant_profile.get('dominant_trip_type') and merchant_profile.get('visit_count', 0) >= 2:
        trip_type = merchant_profile['dominant_trip_type']
        reason_codes.append('merchant_history_prior')

    avg_basket = merchant_profile.get('avg_basket')
    if avg_basket and total > avg_basket * 1.5 and trip_type == 'unknown':
        trip_type = 'grocery_restock'
        reason_codes.append('above_avg_basket')

    confidence = 'high' if len(reason_codes) >= 2 else ('medium' if reason_codes else 'low')
    return {
        'trip_type': normalize_trip_type(trip_type),
        'confidence': confidence,
        'reason_codes': reason_codes or ['insufficient_signal'],
    }


def derive_behavioral_tags(header, line_items, trip, essential, merchant_profile, habits):
    """Assign behavioral tags with weights."""
    tags = {}
    merchant = header.get('merchant') or ''
    trip_type = trip.get('trip_type', 'unknown')

    if trip_type in ('convenience_run',):
        tags['convenience'] = 0.9
    if trip_type == 'impulse_purchase' or IMPULSE_KEYWORDS.search(
        ' '.join(li.get('name', '') for li in line_items)
    ):
        tags['impulse'] = 0.75
    if habits.get('repeat_merchant') or merchant_profile.get('visit_count', 0) >= 3:
        tags['recurring'] = 0.8
    if LUXURY_KEYWORDS.search(merchant) or essential.get('classification') == 'non_essential':
        if any(LUXURY_KEYWORDS.search(li.get('name', '')) for li in line_items):
            tags['luxury'] = 0.7
    if trip_type == 'maintenance_purchase' or MAINTENANCE_KEYWORDS.search(merchant):
        tags['maintenance'] = 0.85
    if SOCIAL_KEYWORDS.search(merchant) or 'dining' in {
        (li.get('category') or '').lower() for li in line_items
    }:
        tags['social'] = 0.7
    if 'health' in {(li.get('category') or '').lower() for li in line_items} or HEALTH_KEYWORDS.search(
        merchant
    ):
        tags['health'] = 0.85
    if PRODUCTIVITY_KEYWORDS.search(merchant):
        tags['productivity'] = 0.65

    return tags


def detect_habits(header, line_items, merchant_profile, all_transactions, receipt_id):
    """Repeat merchant/category/item patterns."""
    merchant = header.get('merchant') or ''
    visit_count = merchant_profile.get('visit_count', 0)
    repeat_merchant = visit_count >= 2

    cat_counts = {}
    item_counts = {}
    for tx in all_transactions or []:
        if tx.get('source') != 'receipt':
            continue
        if tx.get('receipt_id') == receipt_id:
            continue
        if (tx.get('merchant') or '').lower() == merchant.lower():
            for li in tx.get('line_items') or []:
                c = (li.get('category') or 'other').lower()
                cat_counts[c] = cat_counts.get(c, 0) + 1
                name = (li.get('name') or '').lower().strip()
                if name:
                    item_counts[name] = item_counts.get(name, 0) + 1

    current_cats = {(li.get('category') or 'other').lower() for li in line_items}
    repeat_categories = [c for c in current_cats if cat_counts.get(c, 0) >= 2]
    current_names = {(li.get('name') or '').lower().strip() for li in line_items if li.get('name')}
    repeat_items = [n for n in current_names if item_counts.get(n, 0) >= 1]

    pattern_indicators = []
    if repeat_merchant:
        pattern_indicators.append('frequent_merchant')
    if repeat_categories:
        pattern_indicators.append('repeat_category_mix')
    if repeat_items:
        pattern_indicators.append('repeat_items')

    return {
        'repeat_merchant': repeat_merchant,
        'repeat_categories': repeat_categories[:5],
        'repeat_items': repeat_items[:5],
        'spending_pattern_indicators': pattern_indicators,
        'merchant_visit_count_prior': visit_count,
    }


def compute_savings_opportunities(header, line_items, trip, tags, essential):
    """Convenience, recurring awareness, category concentration, avoidable spend."""
    opportunities = []
    indicators = []
    merchant = header.get('merchant') or ''
    try:
        total = float(header.get('total') or 0)
    except (TypeError, ValueError):
        total = 0.0

    if trip.get('trip_type') == 'convenience_run' or tags.get('convenience', 0) >= 0.7:
        opportunities.append({
            'type': 'convenience_premium',
            'severity': 'medium',
            'message': 'Convenience trips often carry higher per-item prices than planned grocery runs.',
        })
        indicators.append('convenience_spend')

    if tags.get('recurring', 0) >= 0.7:
        opportunities.append({
            'type': 'recurring_review',
            'severity': 'low',
            'message': 'Recurring merchant pattern — review whether subscriptions or habits still fit goals.',
        })
        indicators.append('recurring_pattern')

    cats = {}
    for li in line_items:
        if li.get('is_discount'):
            continue
        c = li.get('category') or 'other'
        cats[c] = cats.get(c, 0) + _line_amount(li)
    if cats and total > 0:
        top_cat, top_amt = max(cats.items(), key=lambda x: x[1])
        if top_amt / total >= 0.7:
            opportunities.append({
                'type': 'category_concentration',
                'severity': 'low',
                'message': f'Spend concentrated in {top_cat} ({int(top_amt / total * 100)}% of basket).',
            })
            indicators.append('category_concentration')

    if essential.get('classification') in ('non_essential', 'discretionary') and tags.get('impulse', 0) >= 0.6:
        opportunities.append({
            'type': 'avoidable_discretionary',
            'severity': 'medium',
            'message': 'Discretionary or impulse signals — consider a 24-hour pause rule for similar trips.',
        })
        indicators.append('avoidable_discretionary')

    return {
        'opportunities': opportunities,
        'avoidable_spend_indicators': indicators,
        'convenience_spend_detected': 'convenience_spend' in indicators,
    }


def build_merchant_intelligence(header, merchant_profile, trip):
    """Merchant visit stats and behavior summary."""
    visits = merchant_profile.get('visit_count', 0) + 1  # include current
    return {
        'merchant_key': merchant_profile.get('merchant_key'),
        'visit_count': visits,
        'avg_basket': merchant_profile.get('avg_basket'),
        'dominant_trip_type': trip.get('trip_type') or merchant_profile.get('dominant_trip_type'),
        'behavior_summary': _merchant_behavior_summary(header, merchant_profile, trip),
    }


def _merchant_behavior_summary(header, profile, trip):
    merchant = header.get('merchant') or 'this merchant'
    visits = profile.get('visit_count', 0)
    if visits == 0:
        return f'First tracked visit to {merchant}.'
    dom = profile.get('dominant_trip_type', 'unknown').replace('_', ' ')
    return (
        f'You have visited {merchant} {visits} time(s) before; '
        f'typical trip type: {dom}. Current trip: {trip.get("trip_type", "unknown").replace("_", " ")}.'
    )


def build_behavioral_summary(header, essential, trip, tags, savings, habits, merchant_intel):
    """Five-part narrative: what, why, normal, beneficial, improve."""
    merchant = header.get('merchant') or 'Unknown merchant'
    trip_label = trip.get('trip_type', 'unknown').replace('_', ' ')
    ess_class = essential.get('classification', 'unknown')
    tag_list = ', '.join(sorted(tags.keys())) if tags else 'none'

    what = (
        f'{merchant}: ${header.get("total", "0")} purchase classified as {trip_label} '
        f'({ess_class} spend).'
    )
    why_codes = trip.get('reason_codes', [])
    why = (
        f'Trip shaped by {", ".join(why_codes[:3])}. '
        f'Behavioral tags: {tag_list}.'
    )
    normal = (
        'This looks consistent with your past pattern at this merchant.'
        if habits.get('repeat_merchant')
        else 'Limited history — treat as baseline for future comparisons.'
    )
    beneficial = (
        'Likely supports core needs (essential-leaning basket).'
        if essential.get('essential_score', 0) >= 0.7
        else 'Mostly discretionary — align with goals before repeating.'
    )
    improve_parts = [o.get('message') for o in savings.get('opportunities', [])[:2]]
    improve = (
        ' '.join(improve_parts)
        if improve_parts
        else 'No strong savings flags; maintain current shopping rhythm.'
    )

    return {
        'what_happened': what,
        'why': why,
        'is_it_normal': normal,
        'is_it_beneficial': beneficial,
        'could_it_improve': improve,
        'narrative_short': f'{trip_label.title()} · {ess_class.replace("_", " ")}',
    }
