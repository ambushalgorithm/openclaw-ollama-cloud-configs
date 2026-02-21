# TODO — openclaw-ollama-cloud-configs

## Testing

- [x] **Unit tests for merge-config.py**
  - [x] Test JSON parsing (valid config)
  - [x] Test JSON parsing (invalid config - should fail gracefully)
  - [x] Test merge logic (models section)
  - [x] Test merge logic (aliases section)
  - [x] Test merge logic (fallbacks section)
  - [x] Test backup creation
  - [x] Test dry-run mode
  - [x] Test --only-models flag
  - [x] Test --only-agents flag

- [x] **E2E tests for setup flow**
  
  ### Option A: Subprocess tests (simpler, faster)
  Use Python `subprocess` to run CLI scripts — test real scripts, real arguments, real output. No Docker needed.
  
  - [x] Test merge-config.py --dry-run
  - [x] Test merge-config.py --backup
  - [x] Test merge-config.py --only-models
  - [x] Test merge-config.py --only-agents
  - [x] Test merge-config.py with invalid source (error handling)
  - [x] Test merge-config.py with invalid target (error handling)
  
  ### Option B: openclaw-e2e Docker tests (more comprehensive)
  Spin up Docker container, copy repo in, run scripts against real OpenClaw instance.
  
  - [x] Test container starts with openclaw-e2e
  - [x] Test merge-config.py inside container
  - [x] Test setup-ollama.sh status
  - [x] Test setup-ollama.sh test (single model)
  - [x] Test setup-ollama.sh test (all models)
  - [x] Test setup-ollama.sh aliases
  - [x] Test config loads in OpenClaw
  - [x] Test models available after merge
  - [x] Test gateway restart picks up config
  - [x] Test container cleanup

- [ ] **Schema validation for JSON config**
  - [ ] Validate openclaw-ollama-cloud.json schema
  - [ ] Add CI check for schema validation
  - [ ] Test invalid schema (should fail)

## Other

- [ ] Add CI/CD pipeline for automated tests
- [ ] Add CONTRIBUTING.md
