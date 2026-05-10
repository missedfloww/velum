"""Tests for the ModelRegistry state machine."""

from __future__ import annotations

import pytest

from tests.conftest import MockRedactor
from velum.engine.registry import ModelRegistry


class TestEmptyRegistry:
    def test_get_active_raises_when_empty(self):
        registry = ModelRegistry()
        with pytest.raises(RuntimeError, match="No redaction model registered"):
            registry.get_active()

    def test_list_models_empty(self):
        registry = ModelRegistry()
        assert registry.list_models() == []


class TestRegister:
    def test_first_register_becomes_active(self, mock_redactor):
        registry = ModelRegistry()
        registry.register("first", mock_redactor)
        assert registry.get_active() is mock_redactor

    def test_second_register_does_not_change_active(self, mock_redactor):
        registry = ModelRegistry()
        second = MockRedactor()
        registry.register("first", mock_redactor)
        registry.register("second", second)
        # First-registered wins for the active slot.
        assert registry.get_active() is mock_redactor

    def test_register_same_name_overwrites_entry_but_keeps_active(self, mock_redactor):
        registry = ModelRegistry()
        replacement = MockRedactor()
        registry.register("only", mock_redactor)
        registry.register("only", replacement)
        # Active still points at the original (first registration sets active).
        assert registry.get_active() is mock_redactor
        # But the registry now lists exactly one entry.
        assert len(registry.list_models()) == 1


class TestSetActive:
    def test_set_active_switches_model(self, mock_redactor):
        registry = ModelRegistry()
        second = MockRedactor()
        registry.register("first", mock_redactor)
        registry.register("second", second)
        registry.set_active("second")
        assert registry.get_active() is second

    def test_set_active_unknown_raises_keyerror(self, mock_redactor):
        registry = ModelRegistry()
        registry.register("first", mock_redactor)
        with pytest.raises(KeyError, match="missing"):
            registry.set_active("missing")

    def test_set_active_unknown_on_empty_registry_raises(self):
        registry = ModelRegistry()
        with pytest.raises(KeyError):
            registry.set_active("anything")


class TestListModels:
    def test_list_models_contains_info_fields(self, mock_redactor):
        registry = ModelRegistry()
        registry.register("alpha", mock_redactor)
        models = registry.list_models()
        assert len(models) == 1
        entry = models[0]
        # Each entry contains a "name" key plus the model_info() fields.
        # NOTE: model_info()'s own "name" overrides the registry key in the
        # dict spread `{"name": name, **redactor.model_info()}`, so the
        # surfaced name is the model's internal identity, not the registry
        # key. The /models endpoint relies on this (see backend/routes.py).
        assert "name" in entry
        assert entry["name"] == "mock-redactor"  # from MockRedactor.model_info()
        assert entry["version"] == "0.0.1"
        assert entry["device"] == "cpu"
        assert "private_person" in entry["categories"]

    def test_list_models_returns_one_entry_per_registration(self, mock_redactor):
        registry = ModelRegistry()
        second = MockRedactor()
        registry.register("alpha", mock_redactor)
        registry.register("beta", second)
        models = registry.list_models()
        # Two distinct registrations => two entries (even if they share a model_info name).
        assert len(models) == 2
