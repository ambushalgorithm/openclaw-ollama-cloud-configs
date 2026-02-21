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

- [ ] **E2E tests for setup flow**
  - [ ] Test setup-ollama.sh status command
  - [ ] Test setup-ollama.sh pull command
  - [ ] Test setup-ollama.sh test command (single model)
  - [ ] Test setup-ollama.sh test command (all models)
  - [ ] Test merge-config.py full flow
  - [ ] Test config survives gateway restart

- [ ] **Schema validation for JSON config**
  - [ ] Validate openclaw-ollama-cloud.json schema
  - [ ] Add CI check for schema validation
  - [ ] Test invalid schema (should fail)

## Other

- [ ] Add CI/CD pipeline for automated tests
- [ ] Add CONTRIBUTING.md
