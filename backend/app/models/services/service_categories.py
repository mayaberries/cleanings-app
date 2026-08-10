"""
Service category normalization + validation.

Categories are currently stored as free text on the `services` table.
This module is the single place that decides what "valid" means, so that
if we later move categories into a proper `service_categories` table
(clinic-owned, FK-referenced), only this file needs to change — Service
models, repos, and routes stay untouched.
"""
import re

SUGGESTED_SERVICE_CATEGORIES = [
    "wellness_exam",
    "vaccination",
    "microchipping",
    "nail_trim",
    "bloodwork",
    "imaging",
    "lab_testing",
    "sick_visit",
    "dental_cleaning",
    "spay_neuter",
    "surgery",
    "wound_care",
    "grooming",
    "boarding",
    "end_of_life",
]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def normalize_category(raw: str) -> str:
    """
    Canonicalize a category string so 'Wellness Exam ', 'wellness exam',
    and 'WELLNESS_EXAM' all collapse to the same stored value.
    """
    if not raw or not raw.strip():
        raise ValueError("Service category cannot be empty.")

    slug = _SLUG_RE.sub("_", raw.strip().lower()).strip("_")

    if not slug:
        raise ValueError("Service category must contain at least one letter or number.")

    return slug


def is_suggested(category: str) -> bool:
    """Used by the UI layer to decide whether to show a category as a
    'known' pill vs. a custom one. Not used for validation."""
    return category in SUGGESTED_SERVICE_CATEGORIES