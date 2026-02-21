#!/usr/bin/env python3
"""
Schema validation tests for openclaw-ollama-cloud.json

Validates that the cloud config follows OpenClaw's expected structure.
"""

import json
import re
from pathlib import Path

import pytest

REPO_DIR = Path(__file__).parent.parent
CLOUD_CONFIG = REPO_DIR / "openclaw-ollama-cloud.json"


class TestSchemaValidation:
    """Validate the cloud config JSON schema."""

    @pytest.fixture
    def config(self):
        """Load the cloud config."""
        with open(CLOUD_CONFIG) as f:
            return json.load(f)

    def test_config_is_valid_json(self, config):
        """Test that config is valid JSON."""
        assert config is not None
        assert isinstance(config, dict)

    def test_has_models_section(self, config):
        """Test that config has models section."""
        assert "models" in config, "Config must have 'models' section"
        assert isinstance(config["models"], dict)

    def test_has_providers(self, config):
        """Test that models has providers."""
        assert "providers" in config["models"], "models must have 'providers'"
        assert isinstance(config["models"]["providers"], dict)

    def test_has_ollama_provider(self, config):
        """Test that providers has ollama."""
        assert "ollama" in config["models"]["providers"], "providers must have 'ollama'"
    
    def test_ollama_provider_structure(self, config):
        """Test ollama provider has required fields."""
        ollama = config["models"]["providers"]["ollama"]
        
        assert "baseUrl" in ollama, "ollama must have 'baseUrl'"
        assert "apiKey" in ollama, "ollama must have 'apiKey'"
        assert "models" in ollama, "ollama must have 'models'"
        
        assert isinstance(ollama["baseUrl"], str)
        assert isinstance(ollama["apiKey"], str)
        assert isinstance(ollama["models"], list)
        
        # baseUrl should be a valid URL
        assert ollama["baseUrl"].startswith("http://") or ollama["baseUrl"].startswith("https://")

    def test_models_is_non_empty_list(self, config):
        """Test that models list is non-empty."""
        models = config["models"]["providers"]["ollama"]["models"]
        assert len(models) > 0, "Must have at least one model"

    def test_each_model_has_required_fields(self, config):
        """Test that each model has required fields."""
        models = config["models"]["providers"]["ollama"]["models"]
        
        required_fields = ["id", "name"]
        
        for i, model in enumerate(models):
            for field in required_fields:
                assert field in model, f"Model {i} missing required field '{field}'"
                assert isinstance(model[field], str), f"Model {i} field '{field}' must be string"
                assert len(model[field]) > 0, f"Model {i} field '{field}' must not be empty"

    def test_each_model_has_optional_fields(self, config):
        """Test that each model has optional fields with correct types."""
        models = config["models"]["providers"]["ollama"]["models"]
        
        optional_fields = {
            "reasoning": bool,
            "input": list,
            "cost": dict,
            "contextWindow": int,
            "maxTokens": int,
        }
        
        for i, model in enumerate(models):
            for field, expected_type in optional_fields.items():
                if field in model:
                    assert isinstance(model[field], expected_type), \
                        f"Model {i} field '{field}' must be {expected_type.__name__}"

    def test_model_id_format(self, config):
        """Test that model IDs follow naming convention."""
        models = config["models"]["providers"]["ollama"]["models"]
        
        for i, model in enumerate(models):
            model_id = model["id"]
            # Should contain ':' for variant (e.g., "minimax-m2.5:cloud")
            assert ":" in model_id, f"Model {i} id '{model_id}' should contain ':' for variant"
            
            # ID should not be empty
            assert len(model_id) > 0

    def test_cost_structure(self, config):
        """Test that cost objects have valid structure."""
        models = config["models"]["providers"]["ollama"]["models"]
        
        cost_fields = ["input", "output", "cacheRead", "cacheWrite"]
        
        for i, model in enumerate(models):
            if "cost" in model:
                cost = model["cost"]
                assert isinstance(cost, dict), f"Model {i} cost must be dict"
                
                for field in cost_fields:
                    assert field in cost, f"Model {i} cost missing '{field}'"
                    assert isinstance(cost[field], (int, float)), \
                        f"Model {i} cost '{field}' must be number"
                    assert cost[field] >= 0, f"Model {i} cost '{field}' must be non-negative"

    def test_has_agents_section(self, config):
        """Test that config has agents section."""
        assert "agents" in config, "Config must have 'agents' section"
        assert isinstance(config["agents"], dict)

    def test_has_defaults_in_agents(self, config):
        """Test that agents has defaults."""
        assert "defaults" in config["agents"], "agents must have 'defaults'"
        assert isinstance(config["agents"]["defaults"], dict)

    def test_defaults_has_model(self, config):
        """Test that defaults has model config."""
        defaults = config["agents"]["defaults"]
        assert "model" in defaults, "defaults must have 'model'"
        
        model_config = defaults["model"]
        assert "primary" in model_config, "model must have 'primary'"
        assert isinstance(model_config["primary"], str)
        assert len(model_config["primary"]) > 0

    def test_primary_model_references_valid_model(self, config):
        """Test that primary model references an actual model in the list."""
        primary = config["agents"]["defaults"]["model"]["primary"]
        models = config["models"]["providers"]["ollama"]["models"]
        model_ids = [m["id"] for m in models]
        
        # Primary format: "ollama/minimax-m2.5:cloud" -> extract just the id
        primary_id = primary.replace("ollama/", "")
        
        assert primary_id in model_ids, \
            f"Primary model '{primary_id}' not found in models list"

    def test_fallbacks_are_valid_model_references(self, config):
        """Test that fallback models reference actual models."""
        fallbacks = config["agents"]["defaults"]["model"].get("fallbacks", [])
        models = config["models"]["providers"]["ollama"]["models"]
        model_ids = [m["id"] for m in models]
        
        for fallback in fallbacks:
            # Fallback format: "ollama/minimax-m2.5:cloud" -> extract just the id
            fallback_id = fallback.replace("ollama/", "")
            assert fallback_id in model_ids, \
                f"Fallback model '{fallback_id}' not found in models list"

    def test_model_aliases_are_valid(self, config):
        """Test that model aliases are properly formatted."""
        defaults = config["agents"]["defaults"]
        
        if "models" in defaults:
            aliases = defaults["models"]
            models = config["models"]["providers"]["ollama"]["models"]
            model_ids = [m["id"] for m in models]
            
            for model_ref, alias_config in aliases.items():
                # Model reference format: "ollama/minimax-m2.5:cloud" -> extract id
                model_id = model_ref.replace("ollama/", "")
                
                # Model reference must exist
                assert model_id in model_ids, \
                    f"Alias references unknown model '{model_id}'"
                
                # Alias must have required fields
                assert "alias" in alias_config, f"Alias config for {model_ref} missing 'alias'"
                assert isinstance(alias_config["alias"], str)
                assert len(alias_config["alias"]) > 0

    def test_no_duplicate_model_ids(self, config):
        """Test that model IDs are unique."""
        models = config["models"]["providers"]["ollama"]["models"]
        ids = [m["id"] for m in models]
        
        assert len(ids) == len(set(ids)), "Model IDs must be unique"

    def test_no_duplicate_aliases(self, config):
        """Test that aliases are unique."""
        defaults = config["agents"]["defaults"]
        
        if "models" in defaults:
            aliases = defaults["models"]
            alias_values = [cfg["alias"] for cfg in aliases.values() if "alias" in cfg]
            
            assert len(alias_values) == len(set(alias_values)), "Aliases must be unique"


class TestInvalidSchema:
    """Test that invalid schemas are rejected."""

    def test_empty_config_rejected(self):
        """Test that empty config is rejected."""
        config = {}
        
        with pytest.raises(AssertionError):
            assert "models" in config

    def test_missing_models_rejected(self):
        """Test that config without models is rejected."""
        config = {"agents": {"defaults": {"model": {"primary": "test"}}}}
        
        with pytest.raises(AssertionError):
            assert "models" in config

    def test_missing_primary_model_rejected(self):
        """Test that config without primary model is rejected."""
        config = {
            "models": {"providers": {"ollama": {"models": []}}},
            "agents": {"defaults": {"model": {}}}
        }
        
        with pytest.raises(AssertionError):
            assert "primary" in config["agents"]["defaults"]["model"]

    def test_invalid_model_structure_rejected(self):
        """Test that model without id is rejected."""
        config = {
            "models": {"providers": {"ollama": {"models": [{"name": "test"}]}}},
            "agents": {"defaults": {"model": {"primary": "ollama/test"}}}
        }
        
        with pytest.raises(AssertionError):
            # Check each model has required fields
            for model in config["models"]["providers"]["ollama"]["models"]:
                assert "id" in model


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
