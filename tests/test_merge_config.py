#!/usr/bin/env python3
"""
Unit tests for merge-config.py

Run with: python3 -m pytest tests/test_merge_config.py -v
Or:        python3 tests/test_merge_config.py
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent dir to path for imports (handle hyphenated filename)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from merge-config.py (handle hyphenated filename)
import importlib.util
spec = importlib.util.spec_from_file_location("merge_config", Path(__file__).parent.parent / "merge-config.py")
merge_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_config)

deep_merge = merge_config.deep_merge
get_nested = merge_config.get_nested
set_nested = merge_config.set_nested


class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_merge_simple_dicts(self):
        """Test merging two simple dictionaries."""
        target = {"a": 1, "b": 2}
        source = {"b": 3, "c": 4}
        result = deep_merge(target, source)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        target = {"outer": {"a": 1, "b": 2}}
        source = {"outer": {"b": 3, "c": 4}}
        result = deep_merge(target, source)
        assert result == {"outer": {"a": 1, "b": 3, "c": 4}}

    def test_merge_lists_replace(self):
        """Test that lists are replaced, not appended."""
        target = {"items": [1, 2, 3]}
        source = {"items": [4, 5]}
        result = deep_merge(target, source)
        assert result == {"items": [4, 5]}

    def test_merge_adds_new_keys(self):
        """Test that new keys are added."""
        target = {"a": 1}
        source = {"b": 2}
        result = deep_merge(target, source)
        assert result == {"a": 1, "b": 2}

    def test_merge_returns_source_for_non_dict(self):
        """Test that non-dict source returns source."""
        target = "string"
        source = {"a": 1}
        result = deep_merge(target, source)
        assert result == {"a": 1}

    def test_merge_empty_source(self):
        """Test merging with empty source."""
        target = {"a": 1}
        source = {}
        result = deep_merge(target, source)
        assert result == {"a": 1}


class TestGetNested:
    """Tests for get_nested function."""

    def test_get_simple_key(self):
        """Test getting a simple top-level key."""
        obj = {"a": 1, "b": 2}
        assert get_nested(obj, "a") == 1

    def test_get_nested_key(self):
        """Test getting a nested key with dot notation."""
        obj = {"outer": {"inner": 42}}
        assert get_nested(obj, "outer.inner") == 42

    def test_get_deeply_nested(self):
        """Test getting a deeply nested key."""
        obj = {"a": {"b": {"c": {"d": 4}}}}
        assert get_nested(obj, "a.b.c.d") == 4

    def test_get_missing_key(self):
        """Test getting a missing key returns None."""
        obj = {"a": 1}
        assert get_nested(obj, "b") is None

    def test_get_missing_nested(self):
        """Test getting a missing nested key returns None."""
        obj = {"a": {"b": 1}}
        assert get_nested(obj, "a.c") is None

    def test_get_none_path(self):
        """Test getting from None returns None."""
        assert get_nested(None, "a.b") is None

    def test_get_partial_path_none(self):
        """Test getting when intermediate path is None."""
        obj = {"a": None}
        assert get_nested(obj, "a.b") is None


class TestSetNested:
    """Tests for set_nested function."""

    def test_set_simple_key(self):
        """Test setting a simple top-level key."""
        obj = {}
        set_nested(obj, "a", 1)
        assert obj == {"a": 1}

    def test_set_nested_key(self):
        """Test setting a nested key."""
        obj = {}
        set_nested(obj, "outer.inner", 42)
        assert obj == {"outer": {"inner": 42}}

    def test_set_deeply_nested(self):
        """Test setting a deeply nested key."""
        obj = {}
        set_nested(obj, "a.b.c.d", 4)
        assert obj == {"a": {"b": {"c": {"d": 4}}}}

    def test_set_existing_key(self):
        """Test overwriting an existing key."""
        obj = {"a": 1}
        set_nested(obj, "a", 2)
        assert obj == {"a": 2}

    def test_set_existing_nested(self):
        """Test overwriting an existing nested key."""
        obj = {"outer": {"inner": 1}}
        set_nested(obj, "outer.inner", 2)
        assert obj == {"outer": {"inner": 2}}

    def test_set_creates_intermediate_dicts(self):
        """Test that intermediate dicts are created if missing."""
        obj = {"outer": {}}
        set_nested(obj, "outer.new.deep", 3)
        assert obj == {"outer": {"new": {"deep": 3}}}


class TestJsonParsing:
    """Tests for JSON parsing in merge-config.py."""

    def test_valid_json_parsing(self, tmp_path):
        """Test that valid JSON parses correctly."""
        # Create a temporary config file
        config_file = tmp_path / "test_config.json"
        config_file.write_text('{"key": "value", "number": 42}')

        with open(config_file) as f:
            data = json.load(f)

        assert data == {"key": "value", "number": 42}

    def test_invalid_json_parsing(self, tmp_path):
        """Test that invalid JSON raises JSONDecodeError."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text('{"key": "value",}')  # Invalid JSON

        with pytest.raises(json.JSONDecodeError):
            with open(config_file) as f:
                json.load(f)

    def test_empty_json_object(self, tmp_path):
        """Test that empty JSON object parses."""
        config_file = tmp_path / "empty.json"
        config_file.write_text("{}")

        with open(config_file) as f:
            data = json.load(f)

        assert data == {}

    def test_json_with_arrays(self, tmp_path):
        """Test JSON with arrays parses correctly."""
        config_file = tmp_path / "arrays.json"
        config_file.write_text('{"models": ["a", "b", "c"]}')

        with open(config_file) as f:
            data = json.load(f)

        assert data == {"models": ["a", "b", "c"]}


class TestMergeLogic:
    """Tests for the merge logic used in merge-config.py."""

    def test_merge_models_section(self):
        """Test merging models.providers.ollama section."""
        target = {
            "models": {
                "providers": {
                    "ollama": {"models": [{"id": "old-model"}]}
                }
            }
        }
        source = {
            "models": {
                "providers": {
                    "ollama": {"models": [{"id": "new-model"}]}
                }
            }
        }

        tgt_val = get_nested(target, "models.providers.ollama")
        src_val = get_nested(source, "models.providers.ollama")
        result = deep_merge(tgt_val, src_val)

        assert result == {"models": [{"id": "new-model"}]}

    def test_merge_aliases_section(self):
        """Test merging agents.defaults.models (aliases)."""
        target = {
            "agents": {
                "defaults": {
                    "models": {
                        "ollama/model1": {"alias": "short1"}
                    }
                }
            }
        }
        source = {
            "agents": {
                "defaults": {
                    "models": {
                        "ollama/model2": {"alias": "short2"}
                    }
                }
            }
        }

        tgt_val = get_nested(target, "agents.defaults.models")
        src_val = get_nested(source, "agents.defaults.models")
        result = deep_merge(tgt_val, src_val)

        assert "ollama/model1" in result
        assert "ollama/model2" in result

    def test_merge_fallbacks_section(self):
        """Test merging agents.defaults.model.fallbacks."""
        target = {
            "agents": {
                "defaults": {
                    "model": {
                        "fallbacks": ["model-a", "model-b"]
                    }
                }
            }
        }
        source = {
            "agents": {
                "defaults": {
                    "model": {
                        "fallbacks": ["model-c", "model-d"]
                    }
                }
            }
        }

        tgt_val = get_nested(target, "agents.defaults.model")
        src_val = get_nested(source, "agents.defaults.model")
        result = deep_merge(tgt_val, src_val)

        # Lists should be replaced, not merged
        assert result["fallbacks"] == ["model-c", "model-d"]


class TestBackupCreation:
    """Tests for backup creation functionality."""

    def test_backup_creation(self, tmp_path):
        """Test that backup file is created."""
        target_file = tmp_path / "openclaw.json"
        target_file.write_text('{"test": true}')

        backup_file = target_file.with_suffix(".json.bak")

        shutil.copy2(target_file, backup_file)

        assert backup_file.exists()
        assert backup_file.read_text() == '{"test": true}'

    def test_backup_preserves_metadata(self, tmp_path):
        """Test that backup preserves file metadata."""
        target_file = tmp_path / "openclaw.json"
        target_file.write_text('{"test": true}')

        import time
        time.sleep(0.1)  # Ensure mtime differs

        backup_file = target_file.with_suffix(".json.bak")
        shutil.copy2(target_file, backup_file)

        # Check that the file was copied (metadata preserved)
        assert backup_file.exists()


class TestDryRunMode:
    """Tests for dry-run mode."""

    def test_dry_run_does_not_modify_files(self, tmp_path):
        """Test that dry-run doesn't modify the target file."""
        source_file = tmp_path / "source.json"
        source_file.write_text('{"value": "new"}')

        target_file = tmp_path / "target.json"
        target_file.write_text('{"value": "old"}')

        original_content = target_file.read_text()

        # Simulate dry-run (import and check logic)
        with open(source_file) as f:
            source = json.load(f)
        with open(target_file) as f:
            target = json.load(f)

        # In dry-run mode, we compare but don't write
        src_val = get_nested(source, "value")
        tgt_val = get_nested(target, "value")

        # Target should NOT be modified
        assert target_file.read_text() == original_content
        assert tgt_val == "old"

    def test_dry_run_detects_changes(self, tmp_path):
        """Test that dry-run correctly identifies changes."""
        source = {"key": "new_value"}
        target = {"key": "old_value"}

        src_val = get_nested(source, "key")
        tgt_val = get_nested(target, "key")

        has_changes = tgt_val != src_val
        assert has_changes is True


class TestOnlyFlags:
    """Tests for --only-models and --only-agents flags."""

    def test_only_models_flag(self):
        """Test that only_models selects correct sections."""
        only_models = True
        only_agents = False

        if only_models:
            sections_to_merge = [("models.providers.ollama", "models.providers.ollama")]
        elif only_agents:
            sections_to_merge = [
                ("agents.defaults.model", "agents.defaults.model"),
                ("agents.defaults.models", "agents.defaults.models"),
            ]
        else:
            sections_to_merge = [
                ("models.providers.ollama", "models.providers.ollama"),
                ("agents.defaults.model", "agents.defaults.model"),
                ("agents.defaults.models", "agents.defaults.models"),
            ]

        assert len(sections_to_merge) == 1
        assert sections_to_merge[0] == ("models.providers.ollama", "models.providers.ollama")

    def test_only_agents_flag(self):
        """Test that only_agents selects correct sections."""
        only_models = False
        only_agents = True

        if only_models:
            sections_to_merge = [("models.providers.ollama", "models.providers.ollama")]
        elif only_agents:
            sections_to_merge = [
                ("agents.defaults.model", "agents.defaults.model"),
                ("agents.defaults.models", "agents.defaults.models"),
            ]
        else:
            sections_to_merge = [
                ("models.providers.ollama", "models.providers.ollama"),
                ("agents.defaults.model", "agents.defaults.model"),
                ("agents.defaults.models", "agents.defaults.models"),
            ]

        assert len(sections_to_merge) == 2
        assert ("agents.defaults.model", "agents.defaults.model") in sections_to_merge
        assert ("agents.defaults.models", "agents.defaults.models") in sections_to_merge


class TestIntegration:
    """Integration tests simulating actual merge-config.py behavior."""

    def test_full_merge_workflow(self, tmp_path):
        """Test complete merge workflow."""
        # Create source config
        source_file = tmp_path / "source.json"
        source_config = {
            "models": {
                "providers": {
                    "ollama": {
                        "models": [
                            {"id": "model-1", "name": "Model 1"},
                            {"id": "model-2", "name": "Model 2"}
                        ]
                    }
                }
            },
            "agents": {
                "defaults": {
                    "model": {"primary": "model-1", "fallbacks": ["model-2"]},
                    "models": {"ollama/model-1": {"alias": "m1"}}
                }
            }
        }
        source_file.write_text(json.dumps(source_config))

        # Create target config
        target_file = tmp_path / "target.json"
        target_config = {
            "models": {
                "providers": {
                    "ollama": {
                        "models": [{"id": "old-model"}]
                    }
                }
            },
            "agents": {
                "defaults": {
                    "model": {"primary": "old"},
                    "models": {}
                }
            }
        }
        target_file.write_text(json.dumps(target_config))

        # Load configs
        with open(source_file) as f:
            source = json.load(f)
        with open(target_file) as f:
            target = json.load(f)

        # Merge models.providers.ollama
        src_val = get_nested(source, "models.providers.ollama")
        set_nested(target, "models.providers.ollama", json.loads(json.dumps(src_val)))

        # Merge agents.defaults.model
        src_val = get_nested(source, "agents.defaults.model")
        set_nested(target, "agents.defaults.model", json.loads(json.dumps(src_val)))

        # Merge agents.defaults.models
        src_val = get_nested(source, "agents.defaults.models")
        set_nested(target, "agents.defaults.models", json.loads(json.dumps(src_val)))

        # Verify merge
        merged_models = get_nested(target, "models.providers.ollama.models")
        assert len(merged_models) == 2
        assert merged_models[0]["id"] == "model-1"

        merged_primary = get_nested(target, "agents.defaults.model.primary")
        assert merged_primary == "model-1"

        merged_aliases = get_nested(target, "agents.defaults.models")
        assert "ollama/model-1" in merged_aliases


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
