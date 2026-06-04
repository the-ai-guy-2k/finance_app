"""Canonical receipt categories and alias normalization."""

CATEGORY_SLUGS = (
    'groceries',
    'dining',
    'gas',
    'entertainment',
    'utilities',
    'healthcare',
    'shopping',
    'transport',
    'subscriptions',
    'other',
    'uncategorized',
)

CATEGORY_LABELS = {
    'groceries': 'Groceries',
    'dining': 'Dining',
    'gas': 'Gas / Fuel',
    'entertainment': 'Entertainment',
    'utilities': 'Utilities',
    'healthcare': 'Healthcare',
    'shopping': 'Shopping',
    'transport': 'Transport',
    'subscriptions': 'Subscriptions',
    'other': 'Other',
    'uncategorized': 'Uncategorized',
}

CATEGORY_ALIASES = {
    'food': 'dining',
    'restaurant': 'dining',
    'cafe': 'dining',
    'coffee': 'dining',
    'fuel': 'gas',
    'gasoline': 'gas',
    'grocery': 'groceries',
    'supermarket': 'groceries',
    'pharmacy': 'healthcare',
    'medical': 'healthcare',
    'retail': 'shopping',
    'clothing': 'shopping',
    'parking': 'transport',
    'transit': 'transport',
    'subscription': 'subscriptions',
    'unknown': 'other',
}


def normalize_category(value):
    """Map arbitrary category text to a canonical slug."""
    if not value:
        return 'uncategorized'
    slug = str(value).strip().lower().replace(' ', '_')
    slug = CATEGORY_ALIASES.get(slug, slug)
    if slug not in CATEGORY_SLUGS:
        return 'other'
    return slug


def category_label(slug):
    return CATEGORY_LABELS.get(slug, slug.replace('_', ' ').title())
