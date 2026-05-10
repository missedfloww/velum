"""Deterministic regex backstop for credentials with distinctive prefixes.

This layer runs *after* the primary (model-based) redactor. Patterns here are
intentionally narrow — only credential formats with prefixes specific enough
that false positives are negligible. Context-based PII (names, addresses,
free-form dates) is the model's job, not ours.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from velum.engine.base import RedactionSpan

# (name, compiled pattern, category)
_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    # AWS
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "secret"),
    # GitHub personal access tokens (classic)
    ("github_pat_classic", re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "secret"),
    # GitHub fine-grained PATs
    (
        "github_pat_finegrained",
        re.compile(r"\bgithub_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}\b"),
        "secret",
    ),
    # GitHub other tokens (oauth, server-to-server, refresh, user-to-server)
    ("github_token_other", re.compile(r"\bgh[osur]_[A-Za-z0-9]{36}\b"), "secret"),
    # OpenAI / Anthropic-style secret keys
    ("openai_anthropic_sk", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "secret"),
    # Google API keys
    ("google_api_key", re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b"), "secret"),
    # Slack tokens
    ("slack_token", re.compile(r"\bxox[bpoars]-[A-Za-z0-9-]{10,}\b"), "secret"),
]


def find_backstop_spans(text: str) -> list[RedactionSpan]:
    """Return all credential matches in the text as ``RedactionSpan``s.

    Spans are returned in match order; deduplication and overlap handling
    is done by ``merge_spans``.

    Args:
        text: Input text to scan.

    Returns:
        List of detected credential spans (may be empty).
    """
    spans: list[RedactionSpan] = []
    for _name, pattern, category in _PATTERNS:
        for match in pattern.finditer(text):
            spans.append(
                RedactionSpan(
                    start=match.start(),
                    end=match.end(),
                    category=category,
                    text=match.group(),
                    score=1.0,
                )
            )
    return spans


def merge_spans(
    primary: Sequence[RedactionSpan],
    secondary: Sequence[RedactionSpan],
) -> tuple[RedactionSpan, ...]:
    """Merge two span sets, dropping any secondary span that overlaps a primary.

    Use case: ``primary`` is the model's output (rich, context-aware);
    ``secondary`` is the regex backstop. Any backstop hit that the model
    already caught is redundant — keep the model's. Any backstop hit the
    model missed is added. The result is sorted by start offset.

    Args:
        primary: Authoritative spans (e.g. from the upstream model).
        secondary: Candidate spans to merge in if they don't overlap primary.

    Returns:
        Sorted, non-overlapping tuple of spans.
    """
    primary_ranges = [(s.start, s.end) for s in primary]
    kept: list[RedactionSpan] = list(primary)
    for span in secondary:
        if any(
            _overlaps(span.start, span.end, p_start, p_end)
            for p_start, p_end in primary_ranges
        ):
            continue
        kept.append(span)
    kept.sort(key=lambda s: (s.start, s.end))
    return tuple(kept)


def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end
