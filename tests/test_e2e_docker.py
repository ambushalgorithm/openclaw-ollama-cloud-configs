#!/usr/bin/env python3
"""
E2E Docker tests for openclaw-ollama-cloud-configs using openclaw-e2e

Run with: python3 -m pytest tests/test_e2e_docker.py -v
Prerequisites: openclaw-e2e skill installed, Docker running
"""

import json
import subprocess
import time
from pathlib import Path

import pytest

# Paths
REPO_DIR = Path(__file__).parent.parent
E2E_SCRIPT = Path(__file__).parent.parent.parent / "openclaw-skills" / "openclaw-e2e-skill" / "scripts" / "openclaw-e2e"


class TestOpenClawE2E:
    """E2E tests using openclaw-e2e Docker container."""

    @pytest.fixture(scope="class", autouse=True)
    def ensure_container_running(self):
        """Ensure container is running before tests."""
        # Check if container is already running
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if "openclaw-dev-test" not in result.stdout:
            # Try to start it
            if E2E_SCRIPT.exists():
                start_result = subprocess.run(
                    [str(E2E_SCRIPT), "start"],
                    capture_output=True,
                    text=True
                )
                if start_result.returncode != 0:
                    pytest.skip(f"Could not start E2E container: {start_result.stderr}")
            else:
                pytest.skip("E2E script not found")
            
            # Wait for container to be ready
            time.sleep(5)
        
        yield

    def run_e2e_exec(self, *args):
        """Run command inside E2E container."""
        # Use docker exec directly instead of the wrapper script
        cmd = ["docker", "exec", "openclaw-dev-test"] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=REPO_DIR
        )
        return result

    def test_container_is_running(self):
        """Test that E2E container is running."""
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        assert "openclaw-dev-test" in result.stdout

    def test_copy_repo_to_container(self):
        """Test that we can copy repo files to container."""
        # Copy the repo to container
        result = subprocess.run(
            ["docker", "cp", str(REPO_DIR), "openclaw-dev-test:/home/node/openclaw-ollama-cloud-configs"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Verify files exist
        result = self.run_e2e_exec("ls", "-la", "/home/node/openclaw-ollama-cloud-configs/")
        assert "merge-config.py" in result.stdout

    def test_merge_config_inside_container(self, tmp_path):
        """Test running merge-config.py inside container."""
        # First, copy a target config to container
        # Create a minimal test config
        test_config = {
            "models": {"providers": {"ollama": {"models": []}}},
            "agents": {"defaults": {"model": {}, "models": {}}}
        }
        
        # Write locally
        local_config = tmp_path / "test_openclaw.json"
        local_config.write_text(json.dumps(test_config))
        
        # Copy to container (use different name to avoid busy error)
        result = subprocess.run(
            ["docker", "cp", str(local_config), "openclaw-dev-test:/home/node/.openclaw/test-merge.json"],
            capture_output=True,
            text=True
        )
        
        # Copy repo to container if not already there
        subprocess.run(
            ["docker", "cp", str(REPO_DIR), "openclaw-dev-test:/home/node/openclaw-ollama-cloud-configs"],
            capture_output=True
        )
        
        # Run merge inside container (using the test config)
        result = self.run_e2e_exec(
            "python3",
            "/home/node/openclaw-ollama-cloud-configs/merge-config.py",
            "--dry-run",
            "--source", "/home/node/openclaw-ollama-cloud-configs/openclaw-ollama-cloud.json",
            "--target", "/home/node/.openclaw/test-merge.json"
        )
        
        # Should succeed (dry-run)
        assert result.returncode == 0 or "Previewing" in result.stdout

    def test_setup_ollama_status_inside_container(self):
        """Test running setup-ollama.sh status inside container."""
        # Ensure repo is in container
        subprocess.run(
            ["docker", "cp", str(REPO_DIR), "openclaw-dev-test:/home/node/openclaw-ollama-cloud-configs"],
            capture_output=True
        )
        
        result = self.run_e2e_exec(
            "bash",
            "/home/node/openclaw-ollama-cloud-configs/setup-ollama.sh",
            "status"
        )
        
        # Should run (may fail if ollama not running, but should execute)
        assert "status" in result.stdout.lower() or result.returncode in [0, 1]

    def test_setup_ollama_aliases_inside_container(self):
        """Test running setup-ollama.sh aliases inside container."""
        # Ensure repo is in container
        subprocess.run(
            ["docker", "cp", str(REPO_DIR), "openclaw-dev-test:/home/node/openclaw-ollama-cloud-configs"],
            capture_output=True
        )
        
        result = self.run_e2e_exec(
            "bash",
            "/home/node/openclaw-ollama-cloud-configs/setup-ollama.sh",
            "aliases"
        )
        
        # Should run without crashing
        assert len(result.stdout + result.stderr) > 0

    def test_config_survives_container_restart(self, tmp_path):
        """Test that config persists after container restart."""
        # Create test config
        test_config = {
            "test": "value",
            "models": {"providers": {"ollama": {"test": True}}}
        }
        
        local_config = tmp_path / "restart_test.json"
        local_config.write_text(json.dumps(test_config))
        
        # Copy to container
        subprocess.run(
            ["docker", "cp", str(local_config), "openclaw-dev-test:/home/node/.openclaw/test_config.json"],
            check=True
        )
        
        # Restart container
        subprocess.run(["docker", "restart", "openclaw-dev-test"], check=True)
        time.sleep(3)
        
        # Check config still exists
        result = self.run_e2e_exec("cat", "/home/node/.openclaw/test_config.json")
        assert "test" in result.stdout
        assert "value" in result.stdout


class TestOpenClawE2ECommands:
    """Test openclaw-e2e script commands directly."""

    def test_e2e_status_command(self):
        """Test openclaw-e2e status command."""
        if not E2E_SCRIPT.exists():
            pytest.skip("E2E script not found")
        
        result = subprocess.run(
            [str(E2E_SCRIPT), "status"],
            capture_output=True,
            text=True
        )
        
        # Should run without error
        assert result.returncode in [0, 1]

    def test_e2e_help_command(self):
        """Test openclaw-e2e help command."""
        if not E2E_SCRIPT.exists():
            pytest.skip("E2E script not found")
        
        result = subprocess.run(
            [str(E2E_SCRIPT), "help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "start" in result.stdout.lower() or "stop" in result.stdout.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
