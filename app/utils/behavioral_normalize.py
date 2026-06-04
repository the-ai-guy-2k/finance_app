"""Normalize and validate behavioral intelligence enums and scores."""

from datetime import datetime, timezone

ESSENTIAL_CLASSIFICATIONS = (
    'essential',
    'non_essential',
    'discretionary',
    'mixed',
    'unknown',
)

TRIP_TYPES = (
    'grocery_restock',
    'convenience_run',
    'refill_trip',
    'impulse_purchase',
    'maintenance_purchase',
    'emergency_purchase',
    'mixed_basket',
    'unknown',
)

BEHAVIORAL_TAGS = (
    'convenience',
    'impulse',
    'recurring',
    'luxury',
    'maintenance',
    'social',
    'health',
    'productivity',
)

CONFIDENCE_LEVELS = ('high', 'medium', 'low')


def clamp_score(value, default=0.5):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, round(v, 2)))


def normalize_confidence(value, default='medium'):
    if not value:
        return default
    level = str(value).strip().lower()
    return level if level in CONFIDENCE_LEVELS else default


def normalize_trip_type(value):
    if not value:
        return 'unknown'
    slug = str(value).strip().lower()
    return slug if slug in TRIP_TYPES else 'unknown'


def normalize_essential_classification(value):
    if not value:
        return 'unknown'
    slug = str(value).strip().lower()
    return slug if slug in ESSENTIAL_CLASSIFICATIONS else 'unknown'


def trip_type_label(trip_type):
    return trip_type.replace('_', ' ').title() if trip_type else 'Unknown'


def essential_label(classification):
    labels = {
        'essential': 'Essential',
        'non_essential': 'Non-essential',
        'discretionary': 'Discretionary',
        'mixed': 'Mixed',
        'unknown': 'Unknown',
    }
    return labels.get(classification, 'Unknown')
