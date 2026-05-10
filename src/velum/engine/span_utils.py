"""Pure span post-processing utilities (no model dependencies)."""

from __future__ import annotations

from collections.abc import Sequence

from velum.engine.base import RedactionSpan

# Punctuation that opf occasionally absorbs at span boundaries.
_TRIM_CHARS = frozenset(' "\'.,:;')


def trim_span_punctuation(
    text: str, spans: Sequence[RedactionSpan]
) -> tuple[RedactionSpan, ...]:
    """Shrink spans whose start or end is a trim-eligible punctuation char.

    Never produces an empty or inverted span.

    Args:
        text: The original input text the spans index into.
        spans: Spans as returned by an upstream redactor.

    Returns:
        New tuple of spans with trimmed boundaries; identity is preserved
        for spans that didn't need trimming.
    """
    result: list[RedactionSpan] = []
    for span in spans:
        start, end = span.start, span.end
        while end - 1 > start and text[end - 1] in _TRIM_CHARS:
            end -= 1
        while start < end - 1 and text[start] in _TRIM_CHARS:
            start += 1
        if (start, end) == (span.start, span.end):
            result.append(span)
        else:
            result.append(
                RedactionSpan(
                    start=start,
                    end=end,
                    category=span.category,
                    text=text[start:end],
                    score=span.score,
                )
            )
    return tuple(result)


def render_redacted(text: str, spans: Sequence[RedactionSpan]) -> str:
    """Build redacted text by replacing each span with ``<CATEGORY_UPPERCASE>``.

    Matches opf's native placeholder format (e.g. ``<PRIVATE_PERSON>``,
    ``<SECRET>``). Overlapping spans are resolved by first-wins on ascending
    start; later spans whose start is before the running cursor are skipped.

    Args:
        text: Original input text.
        spans: Detected spans (any order).

    Returns:
        Text with spans substituted by category placeholders.
    """
    if not spans:
        return text

    sorted_spans = sorted(spans, key=lambda s: (s.start, s.end))
    parts: list[str] = []
    cursor = 0
    for span in sorted_spans:
        if span.start < cursor:
            continue  # overlap: keep the earlier span, drop this one
        parts.append(text[cursor : span.start])
        parts.append(f"<{span.category.upper()}>")
        cursor = span.end
    parts.append(text[cursor:])
    return "".join(parts)
