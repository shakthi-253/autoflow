"""
Deterministic service-priority classification, derived entirely from the
issue description text. Never user-settable - see app/schemas/service.py
(ServiceCreate has no priority field) and app/routers/services.py (the
only place a Service's priority is ever assigned).

Matching is case-insensitive and word-boundary-aware, so short keywords
like "AC" only match as a standalone word/phrase and don't accidentally
fire inside unrelated text.
"""
import re

from app.models.service import ServicePriority

# Order matters only in that HIGH is checked before MEDIUM; there is no
# overlap between the two keyword sets as specified.
HIGH_KEYWORDS = [
    "engine failure",
    "engine problem",
    "brake failure",
    "brake problem",
    "brake",
    "battery dead",
    "vehicle won't start",
    "vehicle will not start",
    "overheating",
]

MEDIUM_KEYWORDS = [
    "ac",
    "air conditioning",
    "cooling",
    "electrical",
    "tyre",
    "tire",
    "suspension",
]


def _contains_keyword(text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text, re.IGNORECASE) is not None


def calculate_priority(issue_description: str) -> ServicePriority:
    """Derive a service's priority from its issue description. Pure
    function: same input always produces the same output."""
    for keyword in HIGH_KEYWORDS:
        if _contains_keyword(issue_description, keyword):
            return ServicePriority.HIGH

    for keyword in MEDIUM_KEYWORDS:
        if _contains_keyword(issue_description, keyword):
            return ServicePriority.MEDIUM

    return ServicePriority.LOW
