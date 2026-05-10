"""Tests for span post-processing utilities."""

from __future__ import annotations

from velum.engine.base import RedactionSpan
from velum.engine.span_utils import render_redacted, trim_span_punctuation


def _span(start: int, end: int, text: str, category: str = "secret") -> RedactionSpan:
    return RedactionSpan(start=start, end=end, category=category, text=text, score=1.0)


class TestTrimSpanPunctuation:
    def test_trims_trailing_quote(self) -> None:
        text = 'password is "Eleanor1956!" and was changed'
        spans = (_span(12, 26, '"Eleanor1956!"'),)
        trimmed = trim_span_punctuation(text, spans)
        assert len(trimmed) == 1
        assert trimmed[0].start == 13
        assert trimmed[0].end == 25
        assert trimmed[0].text == "Eleanor1956!"

    def test_trims_trailing_period(self) -> None:
        text = "email me at a@b.com. Thanks"
        spans = (_span(12, 20, "a@b.com.", category="private_email"),)
        trimmed = trim_span_punctuation(text, spans)
        assert trimmed[0].end == 19
        assert trimmed[0].text == "a@b.com"

    def test_no_trim_when_clean(self) -> None:
        text = "Alice Smith works"
        spans = (_span(0, 11, "Alice Smith", category="private_person"),)
        trimmed = trim_span_punctuation(text, spans)
        assert trimmed == spans

    def test_preserves_category_and_score(self) -> None:
        text = '"X"'
        spans = (RedactionSpan(start=0, end=3, category="secret", text='"X"', score=0.87),)
        trimmed = trim_span_punctuation(text, spans)
        assert trimmed[0].category == "secret"
        assert trimmed[0].score == 0.87

    def test_does_not_empty_a_span(self) -> None:
        text = '"."'
        spans = (_span(0, 3, '"."'),)
        trimmed = trim_span_punctuation(text, spans)
        assert trimmed[0].end > trimmed[0].start

    def test_handles_empty_input(self) -> None:
        assert trim_span_punctuation("any text", ()) == ()


class TestRenderRedacted:
    def test_no_spans_returns_input_unchanged(self) -> None:
        assert render_redacted("hello world", ()) == "hello world"

    def test_single_span(self) -> None:
        text = "Hi Alice Smith there"
        spans = (_span(3, 14, "Alice Smith", category="private_person"),)
        assert render_redacted(text, spans) == "Hi <PRIVATE_PERSON> there"

    def test_multiple_spans_in_order(self) -> None:
        text = "Alice met Bob at noon"
        spans = (
            _span(0, 5, "Alice", category="private_person"),
            _span(10, 13, "Bob", category="private_person"),
        )
        assert render_redacted(text, spans) == "<PRIVATE_PERSON> met <PRIVATE_PERSON> at noon"

    def test_unsorted_input_is_handled(self) -> None:
        text = "Alice met Bob"
        spans = (
            _span(10, 13, "Bob", category="private_person"),
            _span(0, 5, "Alice", category="private_person"),
        )
        assert render_redacted(text, spans) == "<PRIVATE_PERSON> met <PRIVATE_PERSON>"

    def test_overlapping_spans_drops_later(self) -> None:
        text = "abcdefghij"
        spans = (_span(2, 6, "cdef"), _span(4, 8, "efgh"))
        assert render_redacted(text, spans) == "ab<SECRET>ghij"

    def test_category_uppercased_with_prefix(self) -> None:
        text = "x@y.com"
        spans = (_span(0, 7, "x@y.com", category="private_email"),)
        assert render_redacted(text, spans) == "<PRIVATE_EMAIL>"
