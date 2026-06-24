# Execution Plan: Refactor tiller-mcp-server to 33GOD Standards

## Milestones

### Milestone 1: Planning & Decomposing (Status: DONE)
- Define architecture, layout, and milestones.
- Initialize `BRIEFING.md`, `progress.md`, `PROJECT.md`, and `plan.md`.
- Start heartbeat cron.

### Milestone 2: Refactor Package Structure (Status: PLANNED)
- Goal: Proper python packaging and linting setup.
- **Tasks**:
  1. Explore current dependencies and verify they are fully declared in `pyproject.toml`.
  2. Remove `requirements.txt` (dependencies moved to `pyproject.toml`).
  3. Add `ruff` configuration to `pyproject.toml` for linting and formatting.
  4. Verify project environment can sync via `uv sync`.
- **Verification**: Run `uv sync` and check that the venv is created and all tools (`ruff`) are available.

### Milestone 3: Rebranding (Status: PLANNED)
- Goal: Rebrand project under `delorenj` and remove `jackstein21` references.
- **Tasks**:
  1. Find and replace all occurrences of `jackstein21` with `delorenj`.
  2. Find and replace all occurrences of `Jack Stein` with `Jarad DeLorenzo` (or `delorenj` where appropriate).
  3. Update `LICENSE` copyright notice to: `Copyright (c) 2025-2026 Jarad DeLorenzo`.
  4. Re-write `README.md` to reflect `uv` and `mise` development workflow.
- **Verification**: Ripgrep check for `jackstein21` and `Jack Stein`.

### Milestone 4: Mock-based Test Suite (Status: PLANNED)
- Goal: Comprehensive unit tests using mocks for Google Sheets API and FastMCP.
- **Tasks**:
  1. Implement test suite under `tests/` using `pytest`.
  2. Mock Google Sheets client so tests run without live OAuth credentials.
  3. Write tests for `get_accounts`, `get_transactions`, `get_categories`.
  4. Ensure 100% pass rate.
- **Verification**: Run `pytest tests/`.

### Milestone 5: uv/mise Integration & Final Verification (Status: PLANNED)
- Goal: Conforming to 33GOD standards with uv and mise, passing audit.
- **Tasks**:
  1. Ensure entry point `tiller-mcp-server = "tiller_mcp_server.server:main"` works.
  2. Add `mise.toml` tasks: `sync`, `dev`, `test`, `lint`, `format`, `build`.
  3. Verify `mise run lint`, `mise run format`, `mise run test`, `mise run build` work as expected.
  4. Verify `pjangler audit` reports `ok: true`.
- **Verification**: Run `node /home/delorenj/code/pjangler/dist/index.js audit`.
