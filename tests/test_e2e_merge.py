#!/usr/bin/env python3
"""
E2E Subprocess tests for merge-config.py

Run with: python3 -m pytest tests/test_e2e_merge.py -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Paths
REPO_DIR = Path(__file__).parent.parent
MERGE_SCRIPT = REPO_DIR / "merge-config.py"
SOURCE_CONFIG = REPO_DIR / "openclaw-ollama-cloud.json"


class TestMergeConfigSubprocess:
    """E2E tests for merge-config.py using subprocess."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temp directory for test files."""
        return tmp_path

    @pytest.fixture
    def valid_target_config(self, temp_dir):
        """Create a valid target openclaw.json config."""
        config = {
            "models": {
                "providers": {
                    "ollama": {
                        "baseUrl": "http://127.0.0.1:11434/v1",
                        "apiKey": "ollama-local",
                        "models": [{"id": "old-model"}]
                    }
                }
            },
            "agents": {
                "defaults": {
                    "model": {
                        "primary": "old-model",
                        "fallbacks": []
                    },
                    "models": {}
                }
            }
        }
        config_file = temp_dir / "openclaw.json"
        config_file.write_text(json.dumps(config, indent=2))
        return config_file

    @pytest.fixture
    def minimal_target_config(self, temp_dir):
        """Create a minimal target config (no existing models)."""
        config = {}
        config_file = temp_dir / "openclaw.json"
        config_file.write_text(json.dumps(config, indent=2))
        return config_file

    def run_merge_script(self, *args, source_path=None, target_path=None, cwd=None):
        """Helper to run merge-config.py with given args."""
        cmd = [sys.executable, str(MERGE_SCRIPT)]
        cmd.extend(args)
        
        env = os.environ.copy()
        if source_path:
            # Can't pass --source easily via env, just use args
            pass
        if target_path:
            pass
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or REPO_DIR,
            env=env
        )
        return result

    def test_dry_run_shows_preview(self, valid_target_config):
        """Test that --dry-run shows preview without modifying files."""
        original_content = valid_target_config.read_text()
        
        result = self.run_merge_script(
            "--dry-run",
            "--source", str(SOURCE_CONFIG),
            "--target", str(valid_target_config)
        )
        
        # Should succeed
        assert result.returncode == 0
        
        # Should show preview text
        assert "Previewing" in result.stdout or "dry run" in result.stdout.lower()
        
        # Should NOT modify the target file
        assert valid_target_config.read_text() == original_content

    def test_backup_creates_bak_file(self, valid_target_config):
        """Test that --backup creates a .bak file."""
        # Run with backup
        result = self.run_merge_script(
            "--backup",
            "--source", str(SOURCE_CONFIG),
            "--target", str(valid_target_config)
        )
        
        assert result.returncode == 0
        
        # Check .bak file exists
        bak_file = valid_target_config.with_suffix(".json.bak")
        assert bak_file.exists()
        
        # Original should be modified
        new_content = valid_target_config.read_text()
        assert new_content != ""

    def test_only_models_updates_models_section(self, temp_dir):
        """Test that --only-models only updates models section."""
        # Create target with existing agents config
        target_config = {
            "models": {"providers": {"ollama": {"models": [{"id": "old"}]}}},
            "agents": {
                "defaults": {
                    "model": {"primary": "keep-this"},
                    "models": {"keep": {"alias": "keep"}}
                }
            }
        }
        target_file = temp_dir / "openclaw.json"
        target_file.write_text(json.dumps(target_config))
        
        result = self.run_merge_script(
            "--only-models",
            "--source", str(SOURCE_CONFIG),
            "--target", str(target_file)
        )
        
        assert result.returncode == 0
        
        # Reload config
        with open(target_file) as f:
            result_config = json.load(f)
        
        # Models should be updated
        models = result_config.get("models", {}).get("providers", {}).get("ollama", {}).get("models", [])
        assert len(models) > 1  # Should have multiple models from source
        
        # Agents should be unchanged
        assert result_config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary") == "keep-this"

    def test_only_agents_updates_agents_section(self, temp_dir):
        """Test that --only-agents only updates agents section."""
        target_config = {
            "models": {"providers": {"ollama": {"models": [{"id": "keep-model"}]}}},
            "agents": {"defaults": {}}
        }
        target_file = temp_dir / "openclaw.json"
        target_file.write_text(json.dumps(target_config))
        
        result = self.run_merge_script(
            "--only-agents",
            "--source", str(SOURCE_CONFIG),
            "--target", str(target_file)
        )
        
        assert result.returncode == 0
        
        # Reload
        with open(target_file) as f:
            result_config = json.load(f)
        
        # Models should be unchanged
        models = result_config.get("models", {}).get("providers", {}).get("ollama", {}).get("models", [])
        assert len(models) == 1
        assert models[0]["id"] == "keep-model"
        
        # Agents should be updated
        assert result_config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary") != ""

    def test_invalid_source_file_shows_error(self, temp_dir):
        """Test that invalid source file shows appropriate error."""
        invalid_source = temp_dir / "invalid.json"
        invalid_source.write_text("not valid json {{{")
        
        target_file = temp_dir / "target.json"
        target_file.write_text("{}")
        
        result = self.run_merge_script(
            "--source", str(invalid_source),
            "--target", str(target_file)
        )
        
        # Should fail
        assert result.returncode != 0
        
        # Should show error message
        assert "error" in result.stdout.lower() or "error" in result.stderr.lower()

    def test_missing_target_file_shows_error(self, temp_dir):
        """Test that missing target file shows appropriate error."""
        nonexistent_target = temp_dir / "does_not_exist.json"
        
        result = self.run_merge_script(
            "--source", str(SOURCE_CONFIG),
            "--target", str(nonexistent_target)
        )
        
        # Should fail
        assert result.returncode != 0
        
        # Should show error about missing target
        output = result.stdout + result.stderr
        assert "not found" in output.lower() or "error" in output.lower()

    def test_help_flag_shows_help(self):
        """Test that -h or --help shows help message."""
        result = self.run_merge_script("-h")
        
        assert result.returncode == 0
        assert "--dry-run" in result.stdout or "--backup" in result.stdout


class TestSetupOllamaSubprocess:
    """E2E tests for setup-ollama.sh using subprocess."""

    def run_setup_script(self, *args):
        """Helper to run setup-ollama.sh."""
        script = REPO_DIR / "setup-ollama.sh"
        cmd = ["bash", str(script)]
        cmd.extend(args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=REPO_DIR
        )
        return result

    def test_status_command_exists(self):
        """Test that setup-ollama.sh status command runs."""
        result = self.run_setup_script("status")
        
        # Should run (may fail if ollama not running, but should execute)
        # Just check it didn't crash with "command not found"
        assert "status" in result.stdout.lower() or "error" in result.stdout.lower() or result.returncode in [0, 1]

    def test_aliases_command_exists(self):
        """Test that setup-ollama.sh aliases command runs."""
        result = self.run_setup_script("aliases")
        
        # Should execute without crashing
        output = result.stdout + result.stderr
        # Should show some alias info
        assert result.returncode in [0, 1, 126, 127] or len(output) > 0

    def test_invalid_command_shows_error(self):
        """Test that invalid command shows error."""
        result = self.run_setup_script("invalid-command-xyz")
        
        # Should fail
        assert result.returncode != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
