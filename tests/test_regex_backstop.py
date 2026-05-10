"""Tests for the regex credential backstop."""

from __future__ import annotations

from velum.engine.base import RedactionSpan
from velum.engine.regex_backstop import find_backstop_spans, merge_spans


class TestFindBackstopSpans:
    def test_aws_access_key_id(self) -> None:
        text = "key is AKIAIOSFODNN7EXAMPLE for the bucket"
        spans = find_backstop_spans(text)
        assert any(s.text == "AKIAIOSFODNN7EXAMPLE" for s in spans)
        assert all(s.category == "secret" for s in spans)

    def test_github_pat_classic(self) -> None:
        # ghp_ + 36 alphanumeric chars per GitHub's classic PAT format. Built
        # at runtime so push-protection secret scanners don't false-positive
        # on the literal.
        token = "ghp" + "_aBcDeFgHiJkLmNoPqRsTuVwXyZ012345abcd"
        text = f"token: {token} and"
        spans = find_backstop_spans(text)
        assert len(spans) == 1
        assert spans[0].text.startswith("ghp_")

    def test_github_pat_finegrained(self) -> None:
        token = "github_pat_" + "A" * 22 + "_" + "B" * 59
        text = f"using {token} for repo access"
        spans = find_backstop_spans(text)
        assert len(spans) == 1
        assert spans[0].text == token

    def test_openai_secret_key(self) -> None:
        # Synthetic, runtime-assembled so secret scanners don't match the literal.
        key = "sk" + "-abcdefghij1234567890ABCDEFGHIJklmnopqrstuvwx"
        text = f"OPENAI_API_KEY={key}"
        spans = find_backstop_spans(text)
        assert any(s.text.startswith("sk-") for s in spans)

    def test_google_api_key(self) -> None:
        key = "AIza" + "X" * 35
        text = f"Maps key: {key} ok"
        spans = find_backstop_spans(text)
        assert any(s.text == key for s in spans)

    def test_slack_bot_token(self) -> None:
        # Runtime-assembled so GitHub Push Protection's Slack-token detector
        # doesn't false-positive on the synthetic literal (this triggered the
        # initial v0.1.0 push and is documented in CHANGELOG/STATUS).
        token = "xo" + "xb-1234567890-0987654321-AbCdEfGhIjKlMnOpQrStUvWx"
        text = f"slack: {token} end"
        spans = find_backstop_spans(text)
        assert any(s.text.startswith("xoxb-") for s in spans)

    def test_no_match_returns_empty(self) -> None:
        text = "this is just a normal sentence with no credentials"
        assert find_backstop_spans(text) == []

    def test_does_not_match_lookalikes(self) -> None:
        # AKIA needs 16 trailing chars; this has 14.
        text = "fake AKIA12345678901234 nope"
        assert find_backstop_spans(text) == []


class TestMergeSpans:
    def test_no_overlap_keeps_both(self) -> None:
        primary = (
            RedactionSpan(start=0, end=5, category="private_person", text="Alice", score=1.0),
        )
        secondary = [
            RedactionSpan(start=10, end=14, category="secret", text="ghp_", score=1.0),
        ]
        merged = merge_spans(primary, secondary)
        assert len(merged) == 2

    def test_overlap_drops_secondary(self) -> None:
        # Primary already covers 5..15; secondary at 10..20 overlaps -> drop.
        primary = (
            RedactionSpan(start=5, end=15, category="secret", text="x" * 10, score=1.0),
        )
        secondary = [
            RedactionSpan(start=10, end=20, category="secret", text="y" * 10, score=1.0),
        ]
        merged = merge_spans(primary, secondary)
        assert len(merged) == 1
        assert merged[0].start == 5

    def test_returns_sorted_tuple(self) -> None:
        primary = (
            RedactionSpan(start=20, end=25, category="secret", text="z" * 5, score=1.0),
        )
        secondary = [
            RedactionSpan(start=0, end=5, category="secret", text="a" * 5, score=1.0),
        ]
        merged = merge_spans(primary, secondary)
        assert isinstance(merged, tuple)
        assert merged[0].start == 0
        assert merged[1].start == 20
