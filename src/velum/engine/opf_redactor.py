"""OPF-based redactor wrapping the official openai/privacy-filter package."""

from __future__ import annotations

import logging

from velum.engine.base import BaseRedactor, RedactionResult, RedactionSpan
from velum.engine.regex_backstop import find_backstop_spans, merge_spans
from velum.engine.span_utils import render_redacted, trim_span_punctuation

logger = logging.getLogger(__name__)


class OPFRedactor(BaseRedactor):
    """Redactor using the official `opf` package (openai/privacy-filter).

    Lazy-loads the model on first call to `redact()` or when `ensure_loaded()` is called.
    """

    def __init__(self, device: str = "cpu") -> None:
        self._device = device
        self._opf_instance = None

    def ensure_loaded(self) -> None:
        """Pre-load the model. Called during backend startup."""
        if self._opf_instance is None:
            logger.info("Loading OPF model on device=%s...", self._device)
            from velum._vendor.opf._api import OPF

            self._opf_instance = OPF(device=self._device)
            # Trigger runtime initialization (downloads model if needed)
            self._opf_instance.get_runtime()
            logger.info("OPF model loaded successfully.")

    def redact(self, text: str) -> RedactionResult:
        """Run redaction using the OPF model with trim + backstop post-processing."""
        self.ensure_loaded()
        assert self._opf_instance is not None

        opf_result = self._opf_instance.redact(text)

        # 1. Convert opf spans to our format
        raw_spans = tuple(
            RedactionSpan(
                start=span.start,
                end=span.end,
                category=span.label,
                text=span.text,
                score=1.0,  # opf doesn't expose per-span confidence
            )
            for span in opf_result.detected_spans
        )

        # 2. Trim punctuation absorbed at span boundaries
        trimmed = trim_span_punctuation(text, raw_spans)

        # 3. Layer in deterministic credential backstop
        backstop = find_backstop_spans(text)
        merged = merge_spans(trimmed, backstop)

        # 4. Re-render redacted_text from the post-processed spans
        redacted = render_redacted(text, merged)

        return RedactionResult(
            original_text=text,
            spans=merged,
            redacted_text=redacted,
        )

    def is_ready(self) -> bool:
        """Whether the OPF model is loaded."""
        return self._opf_instance is not None

    def model_info(self) -> dict[str, str]:
        """Return metadata about the OPF model."""
        return {
            "name": "openai/privacy-filter",
            "version": "0.1.0",
            "device": self._device,
            "categories": (
                "private_person,private_email,private_phone,private_address,"
                "private_date,private_url,account_number,secret"
            ),
        }
