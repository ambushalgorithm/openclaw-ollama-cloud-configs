#!/bin/bash
#
# Set up Ollama and pull cloud models.
# Usage: ./setup-ollama.sh [--check|--pull|--setup|--status]

set -e

OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
CONFIG_FILE="${CONFIG_FILE:-./openclaw-ollama-cloud.json}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}ℹ️${NC}  $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠️${NC}  $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

check_ollama_installed() {
    if command -v ollama &> /dev/null; then
        log_success "Ollama is installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
        return 0
    else
        log_error "Ollama is not installed"
        echo "   Install: curl -fsSL https://ollama.com/install.sh | sh"
        return 1
    fi
}

check_ollama_running() {
    if curl -s "http://${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        log_success "Ollama is running at http://${OLLAMA_HOST}"
        return 0
    else
        log_warn "Ollama is not running at http://${OLLAMA_HOST}"
        echo "   Start with: ollama serve"
        return 1
    fi
}

get_cloud_models() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Config file not found: $CONFIG_FILE"
        return 1
    fi

    # Extract model IDs from config (jq or python fallback)
    if command -v jq &> /dev/null; then
        jq -r '.models.providers.ollama.models[].id' "$CONFIG_FILE" 2>/dev/null || true
    else
        python3 -c "
import json
import sys
try:
    with open('$CONFIG_FILE') as f:
        config = json.load(f)
    for m in config.get('models', {}).get('providers', {}).get('ollama', {}).get('models', []):
        print(m['id'])
except Exception as e:
    sys.exit(1)
" 2>/dev/null || true
    fi
}

check_models() {
    log_info "Checking cloud model availability..."

    if ! check_ollama_running; then
        return 1
    fi

    local models
    models=$(get_cloud_models)

    if [[ -z "$models" ]]; then
        log_warn "No models found in config"
        return 1
    fi

    echo
    echo "   Available models:"
    echo "   Model                          | Status"
    echo "   ------------------------------|--------"

    local available
    available=$(curl -s "http://${OLLAMA_HOST}/api/tags" 2>/dev/null | jq -r '.models[].name' 2>/dev/null || echo "")

    while IFS= read -r model; do
        [[ -z "$model" ]] && continue
        local status="⬜ not pulled"
        if echo "$available" | grep -qx "$model" 2>/dev/null; then
            status="${GREEN}✅ available${NC}"
        fi
        printf "   %-30s | %b\n" "$model" "$status"
    done <<< "$models"

    echo
    log_info "Note: Run './setup-ollama.sh pull' to pull all cloud models."
    log_info "Cloud models use 'ollama pull <model>:cloud' to register with the relay."
}

pull_models() {
    log_info "Pulling all cloud models from config..."

    if ! check_ollama_installed; then
        return 1
    fi

    if ! check_ollama_running; then
        return 1
    fi

    local models
    models=$(get_cloud_models)

    if [[ -z "$models" ]]; then
        log_warn "No models found in config"
        return 1
    fi

    echo
    log_info "This will pull the following models via Ollama cloud relay:"
    while IFS= read -r model; do
        [[ -z "$model" ]] && continue
        echo "   • $model"
    done <<< "$models"
    echo

    local pulled=0
    local failed=0

    while IFS= read -r model; do
        [[ -z "$model" ]] && continue
        echo
        log_info "Pulling: $model"
        if ollama pull "$model" 2>&1; then
            log_success "Pulled: $model"
            ((pulled++))
        else
            log_error "Failed to pull: $model"
            ((failed++))
        fi
    done <<< "$models"

    echo
    log_success "Pull complete: $pulled succeeded, $failed failed"

    if [[ $failed -gt 0 ]]; then
        log_warn "Some models failed to pull. Check your Ollama Cloud access."
        return 1
    fi
}

list_aliases() {
    log_info "Model aliases defined in config:"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Config file not found: $CONFIG_FILE"
        return 1
    fi

    if command -v jq &> /dev/null; then
        jq -r '.agents.defaults.models | to_entries[] | "  \(.key) → \(.value.alias)"' "$CONFIG_FILE" 2>/dev/null | grep "ollama/" || true
    else
        python3 -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
models = config.get('agents', {}).get('defaults', {}).get('models', {})
for full_name, meta in models.items():
    if full_name.startswith('ollama/'):
        alias = meta.get('alias', 'N/A')
        print(f'  {full_name} → {alias}')
" 2>/dev/null || true
    fi

    echo
    log_info "Usage in OpenClaw: @alias or --model ollama/<alias>:cloud"
    echo "   Examples:"
    echo "     @kimi"
    echo "     @deepseek"
    echo "     @gemini-pro"
    echo "     --model ollama/deepseek-v3.2:cloud"
}

test_connectivity() {
    log_info "Testing Ollama cloud connectivity..."

    if ! check_ollama_running; then
        return 1
    fi

    # Test a simple generation with a small model
    local test_model="${1:-kimi-k2.5:cloud}"

    echo
    echo "   Testing model: $test_model"

    if curl -s "http://${OLLAMA_HOST}/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$test_model\", \"prompt\": \"Hi\", \"stream\": false, \"options\": {\"num_predict\": 1}}" \
        > /dev/null 2>&1; then
        log_success "Cloud connectivity working for $test_model"
    else
        log_error "Failed to reach cloud model: $test_model"
        echo "   Make sure you have Ollama Cloud access configured."
        return 1
    fi
}

show_status() {
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║       Ollama Cloud Setup Status                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo

    if check_ollama_installed; then
        check_ollama_running
    fi

    echo
    check_models

    echo
    list_aliases
}

setup_all() {
    log_info "Running full Ollama setup..."

    if ! check_ollama_installed; then
        log_warn "Please install Ollama first:"
        echo "   curl -fsSL https://ollama.com/install.sh | sh"
        exit 1
    fi

    if ! check_ollama_running; then
        log_warn "Please start Ollama:"
        echo "   ollama serve"
        exit 1
    fi

    check_models
    echo
    list_aliases
    echo

    log_success "Ollama is configured for cloud models!"
    echo
    log_info "Quick test:"
    echo "   curl http://${OLLAMA_HOST}/api/tags | jq '.models[].name'"
}

# Main
case "${1:-status}" in
    check|--check)
        check_ollama_installed && check_ollama_running
        ;;
    status|--status)
        show_status
        ;;
    setup|--setup)
        setup_all
        ;;
    pull|--pull)
        pull_models
        ;;
    aliases|--aliases)
        list_aliases
        ;;
    test|--test)
        test_connectivity "${2:-kimi-k2.5:cloud}"
        ;;
    help|--help|-h)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  check    - Check if Ollama is installed and running"
        echo "  status   - Full status report (default)"
        echo "  setup    - Run full setup check"
        echo "  pull     - Pull all models defined in config via ollama pull"
        echo "  aliases  - List model aliases"
        echo "  test     - Test cloud connectivity (optionally: test <model>)"
        echo "  help     - Show this help"
        echo ""
        echo "Environment variables:"
        echo "  OLLAMA_HOST  - Ollama host:port (default: 127.0.0.1:11434)"
        echo "  CONFIG_FILE  - Path to config file (default: ./openclaw-ollama-cloud.json)"
        echo ""
        echo "Examples:"
        echo "  $0 pull                    # Pull all cloud models"
        echo "  $0 pull 2>&1 | tee pull.log # Pull with logging"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run '$0 help' for usage."
        exit 1
        ;;
esac
