# BRIEFING — 2026-06-24T01:57:30Z

## Mission
Investigate the tiller-mcp-server package structure, pyproject.toml, requirements.txt, identify missing dependencies, configure ruff, and propose a clean pyproject.toml format conforming to 33GOD standards.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: Read-only investigator
- Working directory: /home/delorenj/code/tiller-mcp-server/.agents/explorer_m2
- Original parent: a86a76e6-35ef-40ef-b82c-655843353024
- Milestone: Milestone 2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- CODE_ONLY network mode: No external internet access or HTTP clients targeting external URLs.
- Do not run build/test modification commands, only read files and write to working directory.

## Current Parent
- Conversation ID: a86a76e6-35ef-40ef-b82c-655843353024
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `pyproject.toml` (package config)
  - `requirements.txt` (legacy dependencies)
  - `src/tiller_mcp_server/` (package code, `__init__.py`, `server.py`, `sheets_client.py`, `tiller_schema.py`)
  - `auth/auth_setup.py` (auth code)
  - `mise.toml` (workflow configuration)
  - `.mise/version-files.conf` (version-files configuration)
- **Key findings**:
  - `pandas` is declared as a core dependency in `pyproject.toml` but is completely unused in the code.
  - `jupyter` is declared as an optional dev dependency in `requirements.txt` but is missing from `pyproject.toml`.
  - Development tools like `ruff` and `pytest` are not declared in `pyproject.toml`.
  - `requirements.txt` is redundant and can drift from `pyproject.toml`.
  - `src/tiller_mcp_server/__init__.py` hardcodes `__version__ = "1.0.0"` which diverges from `0.1.0` in `pyproject.toml`.
  - `.mise/version-files.conf` only tracks git tags, not `pyproject.toml`.
- **Unexplored areas**: None, all exploration complete.

## Key Decisions Made
- Recommend deleting `requirements.txt` to avoid drift.
- Recommend removing `pandas` from core `dependencies` as it is unused, saving install overhead.
- Recommend utilizing `[dependency-groups]` (PEP 735) for dev tools (`jupyter`, `ruff`, `pytest`).
- Recommend adding `toml pyproject.toml` to `.mise/version-files.conf`.
- Propose a clean, modern Ruff config in `pyproject.toml` for linting and formatting.
- Recommend using `importlib.metadata.version` in `__init__.py` to avoid hardcoding versions.

## Artifact Index
- `/home/delorenj/code/tiller-mcp-server/.agents/explorer_m2/handoff.md` — Final structured report of the exploration and findings.
