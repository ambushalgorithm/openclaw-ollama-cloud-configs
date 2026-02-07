# Ollama Cloud Configs for OpenClaw

Sanitized Ollama cloud model configurations for OpenClaw. Merge these into your `openclaw.json` to get 11 cloud-hosted models with aliases and fallback chains.

## Quick Start

```bash
# Clone Openclaw
git clone git@github.com:openclaw/openclaw.git

# Run config to create the default openclaw.json file
openclaw configure --section workspace

# Clone and enter the repo
git clone git@github.com:crayon-doing-petri/openclaw-ollama-cloud-configs.git
cd openclaw-ollama-cloud-configs

# Check current status
./setup-ollama.sh status

# Pull all cloud models (11 models via ollama pull)
./setup-ollama.sh pull

# Preview changes
./merge-config.py --dry-run

# Merge config into your openclaw.json
./merge-config.py --backup

# Restart OpenClaw
openclaw gateway restart
```

## Fresh Start

<img width="755" height="598" alt="image" src="https://github.com/user-attachments/assets/8603aa5d-70e8-4277-a382-05dfdf8c115a" />

```bash
# Clone Openclaw
git clone git@github.com:openclaw/openclaw.git

# install openclaw npm, etc

# Run config to create the default openclaw.json file
openclaw configure --section workspace

<img width="755" height="598" alt="image" src="https://github.com/user-attachments/assets/8603aa5d-70e8-4277-a382-05dfdf8c115a" />

# Clone and enter the repo
git clone git@github.com:crayon-doing-petri/openclaw-ollama-cloud-configs.git
cd openclaw-ollama-cloud-configs

# Check current status
./setup-ollama.sh status

# Pull all cloud models (11 models via ollama pull)
./setup-ollama.sh pull

# Preview changes
./merge-config.py --dry-run

# Merge config into your openclaw.json
./merge-config.py --backup

# Build the development version if you're working on things
pnpm install && pnpm build && \
cd ui && pnpm install && pnpm build && \
cd .. && openclaw gateway uninstall && openclaw gateway install && \
systemctl --user daemon-reload && \
systemctl --user enable --now openclaw-gateway.service && \
openclaw status

# Restart OpenClaw
openclaw gateway restart
```

## Included Models

| Model | Alias | Input | Context | Cost (in/out) |
|-------|-------|-------|---------|---------------|
| `kimi-k2.5:cloud` | `kimi` | text+image | 262K | $0.0005/$0.0028 |
| `deepseek-v3.2:cloud` | `deepseek` | text | 128K | $0.00028/$0.00042 |
| `deepseek-v3.1:671b-cloud` | `deepseek-r` | text | 128K | $0.0006/$0.0017 |
| `minimax-m2:cloud` | `minimax` | text | 128K | $0.0003/$0.0012 |
| `minimax-m2.1:cloud` | `minimax-xl` | text | 256K | $0.0003/$0.0012 |
| `qwen3-coder-next:cloud` | `qwen-coder` | text | 128K | $0.0005/$0.0012 |
| `devstral-2:123b-cloud` | `devstral` | text | 128K | $0.0008/$0.0025 |
| `gemini-3-pro-preview:cloud` | `gemini-pro` | text+image | 1M | $0.00125/$0.005 |
| `gemini-3-flash-preview:cloud` | `gemini-flash` | text+image | 1M | $0.00015/$0.0006 |
| `ministral-3:14b-cloud` | `ministral` | text+image | 128K | $0.0001/$0.0003 |
| `rnj-1:8b-cloud` | `rnj` | text | 128K | $0.0004/$0.0012 |

## Usage

### In Chat (Aliases)
```
@kimi explain this
@deepseek write a function
@gemini-pro analyze this image
@qwen-coder review my code
```

### Via CLI
```bash
# Use specific model
openclaw run --model ollama/deepseek-v3.2:cloud "prompt"

# Use alias
openclaw run --model @deepseek "prompt"
```

## Scripts

### `merge-config.py`
Merge the Ollama config into your OpenClaw configuration.

```bash
./merge-config.py --help              # Show options
./merge-config.py --dry-run           # Preview changes
./merge-config.py --backup            # Merge with backup
./merge-config.py --only-models       # Just update model list
./merge-config.py --only-agents       # Just update aliases/defaults
```

### `setup-ollama.sh`
Check Ollama installation, pull models, and verify cloud connectivity.

```bash
./setup-ollama.sh status      # Full status (default)
./setup-ollama.sh check       # Quick check
./setup-ollama.sh pull        # Pull all 11 cloud models
./setup-ollama.sh aliases     # List aliases
./setup-ollama.sh test        # Test connectivity
./setup-ollama.sh test kimi   # Test specific model
```

## File Structure

```
.
├── openclaw-ollama-cloud.json   # Sanitized model config
├── merge-config.py              # Merge script
├── setup-ollama.sh              # Setup/verify script
└── README.md                    # This file
```

## What's in the Config?

The `openclaw-ollama-cloud.json` contains only the model-related sections:

- **models.providers.ollama** — Provider config with 11 cloud models
- **agents.defaults.model.primary** — Default model (`kimi`)
- **agents.defaults.model.fallbacks** — Fallback chain (10 models)
- **agents.defaults.models** — Aliases for shorthand access

## Merging Behavior

The merge script updates these paths in your `~/.openclaw/openclaw.json`:

| Path | Behavior |
|------|----------|
| `models.providers.ollama` | Full replace (all models) |
| `agents.defaults.model.primary` | Replace |
| `agents.defaults.model.fallbacks` | Replace |
| `agents.defaults.models` | Replace (aliases) |

Your existing auth, channels, gateway, and other settings are untouched.

## Prerequisites

1. **Ollama installed**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Ollama running**
   ```bash
   ollama serve
   ```

3. **Pull cloud models**
   ```bash
   ./setup-ollama.sh pull
   # Or individually:
   ollama pull kimi-k2.5:cloud
   ollama pull deepseek-v3.2:cloud
   ollama pull deepseek-v3.1:671b-cloud
   ollama pull minimax-m2:cloud
   ollama pull minimax-m2.1:cloud
   ollama pull qwen3-coder-next:cloud
   ollama pull devstral-2:123b-cloud
   ollama pull gemini-3-pro-preview:cloud
   ollama pull gemini-3-flash-preview:cloud
   ollama pull ministral-3:14b-cloud
   ollama pull rnj-1:8b-cloud
   ```

4. **Cloud access configured**
   - Ollama Cloud relay should be active (local 127.0.0.1:11434 proxies to cloud)

## Troubleshooting

### Ollama not found
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Can't connect to Ollama
```bash
# Check if running
curl http://127.0.0.1:11434/api/tags

# Start Ollama
ollama serve
```

### Model not responding
```bash
# Test connectivity
./setup-ollama.sh test kimi
```

## License

MIT — use, modify, commit to your own repos.
