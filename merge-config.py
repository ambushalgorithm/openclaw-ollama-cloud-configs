#!/usr/bin/env python3
"""
Merge Ollama cloud model configuration into OpenClaw config.

Usage:
  ./merge-config.py [OPTIONS]

Options:
  --source PATH       Path to ollama cloud config (default: ./openclaw-ollama-cloud.json)
  --target PATH       Path to openclaw.json (default: ~/.openclaw/openclaw.json)
  --dry-run           Show what would change without applying
  --backup            Create .bak backup of target before modifying
  --only-models       Only merge models.providers.ollama section
  --only-agents       Only merge agents.defaults.model section
  -h, --help          Show this help message

Examples:
  ./merge-config.py                           # Full merge with defaults
  ./merge-config.py --dry-run                 # Preview changes
  ./merge-config.py --backup                  # Merge with backup
  ./merge-config.py --only-models             # Just update provider models
"""

import json
import sys
import shutil
from pathlib import Path
from typing import Any


def deep_merge(target: Any, source: Any, path: str = "") -> Any:
    """Deep merge source into target."""
    if isinstance(target, dict) and isinstance(source, dict):
        for key in source:
            if key in target:
                if isinstance(target[key], dict) and isinstance(source[key], dict):
                    target[key] = deep_merge(target[key], source[key], f"{path}.{key}")
                elif isinstance(target[key], list) and isinstance(source[key], list):
                    # For lists, we replace entirely (don't append)
                    target[key] = source[key]
                else:
                    target[key] = source[key]
            else:
                target[key] = source[key]
        return target
    return source


def get_nested(obj: dict, path: str) -> Any:
    """Get nested value by dot path."""
    keys = path.split(".")
    for key in keys:
        if obj is None or not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def set_nested(obj: dict, path: str, value: Any) -> None:
    """Set nested value by dot path."""
    keys = path.split(".")
    for key in keys[:-1]:
        if key not in obj or not isinstance(obj[key], dict):
            obj[key] = {}
        obj = obj[key]
    obj[keys[-1]] = value


def main():
    args = sys.argv[1:]

    # Parse simple args
    dry_run = "--dry-run" in args
    backup = "--backup" in args
    only_models = "--only-models" in args
    only_agents = "--only-agents" in args
    help_requested = "-h" in args or "--help" in args

    if help_requested:
        print(__doc__)
        sys.exit(0)

    # Get paths
    source_idx = args.index("--source") + 1 if "--source" in args else None
    target_idx = args.index("--target") + 1 if "--target" in args else None

    source_path = Path(args[source_idx]) if source_idx else Path(__file__).parent / "openclaw-ollama-cloud.json"
    target_path = Path(args[target_idx]) if target_idx else Path.home() / ".openclaw" / "openclaw.json"

    # Validate paths
    if not source_path.exists():
        print(f"❌ Source config not found: {source_path}")
        sys.exit(1)

    if not target_path.exists():
        print(f"❌ Target config not found: {target_path}")
        print("   Run 'openclaw doctor' first to initialize.")
        sys.exit(1)

    # Load configs
    with open(source_path, "r") as f:
        source = json.load(f)

    with open(target_path, "r") as f:
        target = json.load(f)

    # Determine what to merge
    sections_to_merge = []

    if only_models:
        sections_to_merge = [("models.providers.ollama", "models.providers.ollama")]
    elif only_agents:
        sections_to_merge = [
            ("agents.defaults.model", "agents.defaults.model"),
            ("agents.defaults.models", "agents.defaults.models"),
        ]
    else:
        # Full merge: models + agent defaults
        sections_to_merge = [
            ("models.providers.ollama", "models.providers.ollama"),
            ("agents.defaults.model", "agents.defaults.model"),
            ("agents.defaults.models", "agents.defaults.models"),
        ]

    # Preview or apply changes
    print(f"{'🔄' if not dry_run else '👁️'}  {'Merging' if not dry_run else 'Previewing'} Ollama cloud config")
    print(f"   Source: {source_path}")
    print(f"   Target: {target_path}")
    print()

    changes = []

    for src_path, tgt_path in sections_to_merge:
        src_val = get_nested(source, src_path)
        tgt_val = get_nested(target, tgt_path)

        if src_val is None:
            print(f"   ⚠️  Skipping {src_path} (not found in source)")
            continue

        if dry_run:
            if tgt_val != src_val:
                changes.append(f"   📝 {tgt_path}: would update")
            else:
                changes.append(f"   ✅ {tgt_path}: already up to date")
        else:
            if tgt_val != src_val:
                # Ensure parent path exists
                parent_keys = tgt_path.split(".")[:-1]
                current = target
                for key in parent_keys:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                set_nested(target, tgt_path, json.loads(json.dumps(src_val)))  # Deep copy
                changes.append(f"   ✅ {tgt_path}: updated")
            else:
                changes.append(f"   ✅ {tgt_path}: already up to date")

    for change in changes:
        print(change)

    if dry_run:
        print()
        print("🏁 Dry run complete. Use without --dry-run to apply changes.")
        sys.exit(0)

    # Create backup if requested
    if backup:
        backup_path = target_path.with_suffix(".json.bak")
        shutil.copy2(target_path, backup_path)
        print(f"   💾 Backup created: {backup_path}")

    # Write merged config
    with open(target_path, "w") as f:
        json.dump(target, f, indent=2)

    print()
    print("✅ Merge complete!")
    print()
    print("📝 Next steps:")
    print("   1. Review the merged config: openclaw config.get | jq '.models.providers.ollama'")
    print("   2. Restart OpenClaw to pick up changes: openclaw gateway restart")
    print("   3. Run `./setup-ollama.sh` to pull/configure models")


if __name__ == "__main__":
    main()
