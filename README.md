# ☁️ OpenClaw Ollama Cloud Configs

Pre-configured cloud-hosted Ollama models for OpenClaw — 11 models with aliases, fallback chains, and automatic setup.

<img width="755" height="598" alt="OpenClaw Config" src="https://github.com/user-attachments/assets/8603aa5d-70e8-4277-a382-05dfdf8c115a" />

## What You Get

```
┌─────────────────────────────────────────────────────────┐
│  kimi        → Kimi K2.5 (vision, 262K context)         │
│  deepseek    → DeepSeek V3.2 (fast general)             │
│  deepseek-r  → DeepSeek R1 671B (reasoning)             │
│  qwen-coder  → Qwen 3 Coder (code specialist)           │
│  gemini-pro  → Gemini 3 Pro (vision, 1M context)        │
│  gemini-flash→ Gemini 3 Flash (fast vision)             │
│  + 5 more...                                            │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ 11 cloud-hosted models via Ollama
- ✅ Short aliases (`@kimi`, `@deepseek`, `@qwen-coder`)
- ✅ Automatic fallback chain (if one fails, try the next)
- ✅ One-command setup

## Quick Start (2 minutes)

**Prerequisites:** OpenClaw installed, Ollama Cloud relay active

```bash
# Clone this repo
git clone git@github.com:crayon-doing-petri/openclaw-ollama-cloud-configs.git
cd openclaw-ollama-cloud-configs

# Check status and pull models
./setup-ollama.sh pull

# Merge config into your OpenClaw
./merge-config.py --backup

# Restart OpenClaw
openclaw gateway restart

# Test it
openclaw agent --model @kimi "Hello!"
```

Done! You can now use `@kimi`, `@deepseek`, `@gemini-pro`, etc.

## Included Models

| Alias | Model | Inputs | Context | Cost (in/out) |
|-------|-------|--------|---------|---------------|
| `kimi` | `kimi-k2.5:cloud` | text+image | 262K | $0.50/$2.80 per M |
| `deepseek` | `deepseek-v3.2:cloud` | text | 128K | $0.28/$0.42 per M |
| `deepseek-r` | `deepseek-v3.1:671b-cloud` | text | 128K | $0.60/$1.70 per M |
| `minimax` | `minimax-m2:cloud` | text | 128K | $0.30/$1.20 per M |
| `minimax-xl` | `minimax-m2.1:cloud` | text | 256K | $0.30/$1.20 per M |
| `qwen-coder` | `qwen3-coder-next:cloud` | text | 128K | $0.50/$1.20 per M |
| `devstral` | `devstral-2:123b-cloud` | text | 128K | $0.80/$2.50 per M |
| `gemini-pro` | `gemini-3-pro-preview:cloud` | text+image | 1M | $1.25/$5.00 per M |
| `gemini-flash` | `gemini-3-flash-preview:cloud` | text+image | 1M | $0.15/$0.60 per M |
| `ministral` | `ministral-3:14b-cloud` | text+image | 128K | $0.10/$0.30 per M |
| `rnj` | `rnj-1:8b-cloud` | text | 128K | $0.40/$1.20 per M |

**Default:** `kimi` (best balance of capability, speed, and vision support)

**Fallback chain:** kimi → deepseek-r → gemini-pro → deepseek → qwen-coder → minimax-xl → ...

## Usage

### In OpenClaw Chat
```
@kimi explain quantum computing
@deepseek-r solve this step by step
@gemini-pro analyze this screenshot
@qwen-coder review my rust code
```

### Via CLI
```bash
# Use an alias
openclaw agent --message "Write a poem" --model @kimi

# Use full model path (same thing)
openclaw agent --message "Write a poem" --model ollama/kimi-k2.5:cloud
```

### In your openclaw.json
```json5
{
  agent: {
    model: "@kimi"  // or "ollama/kimi-k2.5:cloud"
  }
}
```

## Setup Commands

### `setup-ollama.sh` — Pull and verify models

```bash
./setup-ollama.sh status       # Check what's installed
./setup-ollama.sh pull         # Pull all 11 cloud models
./setup-ollama.sh test         # Test all models
./setup-ollama.sh test kimi    # Test specific model
./setup-ollama.sh aliases      # Show all aliases
```

### `merge-config.py` — Merge into OpenClaw

```bash
./merge-config.py --dry-run     # Preview changes (no modify)
./merge-config.py --backup      # Merge with timestamped backup
./merge-config.py --only-models # Update just model definitions
./merge-config.py --only-agents # Update just aliases/defaults
```

**What gets merged into `~/.openclaw/openclaw.json`:**

| Section | Action |
|---------|--------|
| `models.providers.ollama.models` | Replace (11 models) |
| `agents.defaults.model.primary` | Replace (→ `@kimi`) |
| `agents.defaults.model.fallbacks` | Replace (fallback chain) |
| `agents.defaults.models` | Replace (aliases) |

Your auth, channels, gateway settings, and other configs are **left untouched**.

## Prerequisites

### 1. Ollama installed
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Ollama running (with cloud relay)
```bash
# Ollama should be running locally on 11434
ollama serve

# Verify it's working
curl http://127.0.0.1:11434/api/tags
```

> **Note:** This config uses Ollama Cloud models. Your local Ollama proxies requests to the cloud (no local GPU needed for these models).

### 3. OpenClaw configured
```bash
# Ensure you have a base config
openclaw configure --section workspace
```

## File Structure

```
.
├── openclaw-ollama-cloud.json    # Model definitions + aliases
├── merge-config.py               # Config merger script
├── setup-ollama.sh               # Setup/verification script
└── README.md                     # You're here!
```

## Troubleshooting

### "ollama: command not found"
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### "Can't connect to Ollama"
```bash
# Start Ollama
ollama serve &

# Verify
curl http://127.0.0.1:11434/api/tags
```

### Model not responding
```bash
# Test specific model
./setup-ollama.sh test kimi

# Should show: ✅ kimi-k2.5:cloud - Working
```

### Config not merging
```bash
# Check it found your openclaw.json
ls ~/.openclaw/openclaw.json

# Dry run to see what it would change
./merge-config.py --dry-run
```

## Updating

```bash
git pull                          # Get latest model list
./setup-ollama.sh pull            # Pull any new models
./merge-config.py --backup        # Re-merge config
openclaw gateway restart          # Apply changes
```

## License

MIT — use, modify, commit to your own repos. No attribution required.
