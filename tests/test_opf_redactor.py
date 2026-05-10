"""Smoke tests for OPFRedactor.

The smoke tests intentionally never call `redact()` or `ensure_loaded()` —
loading the real `openai/privacy-filter` model is far too expensive (and
downloads weights) for the unit-test gate.

The pipeline tests at the bottom of this file inject a `_FakeOPF` directly
into the redactor's private attribute so we can exercise the full
trim + backstop + re-render path without touching the real model.
"""

from __future__ import annotations

from dataclasses import dataclass

from velum.engine.opf_redactor import OPFRedactor


class TestConstruction:
    def test_constructs_with_default_device(self):
        redactor = OPFRedactor()
        assert redactor is not None

    def test_constructs_with_explicit_cpu(self):
        redactor = OPFRedactor(device="cpu")
        assert redactor is not None


class TestIsReady:
    def test_is_ready_false_before_load(self):
        # Lazy loading: model is NOT loaded at construction time.
        redactor = OPFRedactor(device="cpu")
        assert redactor.is_ready() is False


class TestModelInfo:
    def test_model_info_keys(self):
        info = OPFRedactor(device="cpu").model_info()
        for key in ("name", "version", "device", "categories"):
            assert key in info, f"missing key: {key}"

    def test_model_info_device_reflects_constructor(self):
        info = OPFRedactor(device="cpu").model_info()
        assert info["device"] == "cpu"

    def test_model_info_name_is_openai_privacy_filter(self):
        info = OPFRedactor(device="cpu").model_info()
        assert info["name"] == "openai/privacy-filter"


# ---------------------------------------------------------------------------
# Pipeline tests — exercise OPFRedactor.redact() with a fake opf instance,
# verifying that trim_span_punctuation + find_backstop_spans + merge_spans +
# render_redacted are wired into the post-processing pipeline.
# ---------------------------------------------------------------------------


@dataclass
class _FakeDetectedSpan:
    start: int
    end: int
    label: str
    text: str


@dataclass
class _FakeOPFResult:
    text: str
    detected_spans: list[_FakeDetectedSpan]
    redacted_text: str  # never used by our pipeline post-Task-4


class _FakeOPF:
    """Stand-in for opf._api.OPF used to exercise OPFRedactor without downloads."""

    def __init__(self, spans_for_text: dict[str, list[_FakeDetectedSpan]]) -> None:
        self._table = spans_for_text

    def redact(self, text: str) -> _FakeOPFResult:
        spans = self._table.get(text, [])
        return _FakeOPFResult(text=text, detected_spans=spans, redacted_text="(unused)")

    def get_runtime(self) -> None:
        pass


def _install_fake(redactor: OPFRedactor, fake: _FakeOPF) -> None:
    """Bypass ensure_loaded by injecting the fake directly."""
    redactor._opf_instance = fake  # type: ignore[attr-defined]


class TestOPFRedactorPipeline:
    def test_trims_punctuation_from_opf_spans(self) -> None:
        text = 'password "Eleanor1956!" set'
        # opf returns a span that includes the surrounding quotes
        fake = _FakeOPF({text: [_FakeDetectedSpan(9, 23, "secret", '"Eleanor1956!"')]})
        redactor = OPFRedactor()
        _install_fake(redactor, fake)

        result = redactor.redact(text)

        assert len(result.spans) == 1
        assert result.spans[0].text == "Eleanor1956!"
        assert result.spans[0].start == 10
        assert result.spans[0].end == 22
        # Re-rendered redacted text preserves the quotes
        assert result.redacted_text == 'password "<SECRET>" set'

    def test_backstop_catches_credential_opf_missed(self) -> None:
        text = "AWS key AKIAIOSFODNN7EXAMPLE in config"
        # opf returns nothing
        fake = _FakeOPF({text: []})
        redactor = OPFRedactor()
        _install_fake(redactor, fake)

        result = redactor.redact(text)

        assert len(result.spans) == 1
        assert result.spans[0].text == "AKIAIOSFODNN7EXAMPLE"
        assert result.spans[0].category == "secret"
        assert result.redacted_text == "AWS key <SECRET> in config"

    def test_backstop_does_not_double_redact(self) -> None:
        # opf already caught the credential; backstop should not duplicate.
        # Token is `ghp_` + 36 alphanumeric chars (canonical classic-PAT format,
        # matching the regex `ghp_[A-Za-z0-9]{36}` and the fixture used in
        # tests/test_regex_backstop.py). Assembled at runtime so GitHub Push
        # Protection doesn't false-positive on the literal.
        token = "ghp" + "_aBcDeFgHiJkLmNoPqRsTuVwXyZ012345abcd"
        text = f"token {token} end"
        opf_span = _FakeDetectedSpan(6, 46, "secret", token)
        fake = _FakeOPF({text: [opf_span]})
        redactor = OPFRedactor()
        _install_fake(redactor, fake)

        result = redactor.redact(text)

        assert len(result.spans) == 1
        assert result.redacted_text == "token <SECRET> end"

    def test_combined_trim_and_backstop(self) -> None:
        text = 'name "Alice" key AKIAIOSFODNN7EXAMPLE end'
        fake = _FakeOPF(
            {text: [_FakeDetectedSpan(5, 12, "private_person", '"Alice"')]}
        )
        redactor = OPFRedactor()
        _install_fake(redactor, fake)

        result = redactor.redact(text)

        # Two spans: trimmed person + backstop AWS key
        assert len(result.spans) == 2
        assert result.redacted_text == 'name "<PRIVATE_PERSON>" key <SECRET> end'
