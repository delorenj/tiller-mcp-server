# Handoff Report: Milestone 2 Package Structure & Configuration Exploration

This report details the findings and proposals for refactoring the `tiller-mcp-server` package structure and Python package configuration to align with modern packaging best practices and 33GOD standards.

---

## 1. Observation

Direct observations made within the repository:

### Core File Structure and Configurations
- **Package Source**: The codebase uses a standard `src/` layout:
  - `src/tiller_mcp_server/__init__.py`
  - `src/tiller_mcp_server/server.py`
  - `src/tiller_mcp_server/sheets_client.py`
  - `src/tiller_mcp_server/tiller_schema.py`
- **Authentication**: `auth/auth_setup.py` exists to initialize OAuth credentials.
- **Environment**: Managed using `uv` (version `uv 0.11.14` detected) and `mise`.

### Current `pyproject.toml` Configuration (Lines 1-27)
```toml
[project]
name = "tiller-mcp-server"
version = "0.1.0"
description = "Tiller Money MCP Server"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.0.0",
    "google-auth>=2.0.0",
    "google-auth-oauthlib>=1.0.0",
    "google-auth-httplib2>=0.2.0",
    "google-api-python-client>=2.0.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "pandas>=2.0.0",
]

[project.scripts]
tiller-mcp-server = "tiller_mcp_server.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/tiller_mcp_server"]
```

### Current `requirements.txt` Configuration (Lines 1-17)
```text
# Google Sheets API
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.0.0

# MCP Framework
mcp>=1.0.0

# Data handling
pydantic>=2.0.0
python-dotenv>=1.0.0

# Development (optional)
jupyter>=1.0.0
pandas>=2.0.0
```

### Dependency Audit & Unused Libraries
- Grep search for `pandas` returned zero imports or usages within any `.py` file in the project. It only appears in dependency declarations (`pyproject.toml`, `requirements.txt`, and `uv.lock`).

### Version Parity Issues
- `src/tiller_mcp_server/__init__.py` contains a hardcoded literal version:
  ```python
  __version__ = "1.0.0"
  ```
  This differs from `0.1.0` in `pyproject.toml`.
- `.mise/version-files.conf` only contains:
  ```text
  gittag .
  ```
  It does not track `pyproject.toml`. As a result, running `mise run version` prints `v0.0.0` (defaults to git tag) instead of recognizing `0.1.0` in `pyproject.toml`.

---

## 2. Logic Chain

1. **Requirements redundancy**: `pyproject.toml` is already configured with `hatchling` as the build system and defines `dependencies`. Having `requirements.txt` is redundant, complicates updates, and risks dependency drift. Therefore, it should be deleted.
2. **Missing & Misplaced Dependencies**:
   - `jupyter>=1.0.0` is defined in `requirements.txt` but omitted from `pyproject.toml`.
   - `pandas` is declared as a core dependency in `pyproject.toml` but is entirely unused in the codebase. Core dependency list size should be minimized to avoid inflating installation footprint.
   - Development tools such as `ruff` (formatting/linting) and `pytest` (upcoming testing in M4) are not declared anywhere.
   - **Resolution**: Under modern standards, all core dependencies should be defined under `[project].dependencies` (excluding `pandas`). Optional development dependencies (`jupyter`, `pytest`, `ruff`) should be grouped in standard `[dependency-groups]` (PEP 735).
3. **Missing Tool configurations**: No Ruff configuration is declared in `pyproject.toml`. A standardized lint/format config block `[tool.ruff]` needs to be appended.
4. **Self-reported versioning**: Hardcoding `__version__ = "1.0.0"` in package code violates the single source of truth (SSOT) principle. The package version should be dynamically resolved at runtime from metadata via `importlib.metadata`.
5. **Version-files configuration**: To allow `mise-versioning` tasks (`version`, `version:bump`, etc.) to coordinate version updates, `.mise/version-files.conf` must track `pyproject.toml` using the `toml` type handler.

---

## 3. Caveats

- **Pandas Future Intent**: This analysis assumes `pandas` is not intended to be used in core functionality. If a future feature requires pandas data structures, it would need to be added back to core `dependencies`.
- **Ruff target version**: The ruff target version is set to `py312` to align with `requires-python = ">=3.12"`.

---

## 4. Conclusion

We recommend the following steps for the implementation phase of Milestone 2:

1. **Delete `requirements.txt`**: Let `pyproject.toml` act as the single source of truth.
2. **Update `pyproject.toml`**:
   - Remove `pandas>=2.0.0` from `dependencies`.
   - Create a `[dependency-groups]` table containing `dev` dependencies (`jupyter`, `ruff`, `pytest`).
   - Add `[tool.ruff]` section specifying rules, line length, and format options.
   *(See proposed file `/home/delorenj/code/tiller-mcp-server/.agents/explorer_m2/proposed_pyproject.toml`)*
3. **Configure Runtime Versioning**:
   - Modify `src/tiller_mcp_server/__init__.py` to fetch package version dynamically from metadata.
   *(See proposed file `/home/delorenj/code/tiller-mcp-server/.agents/explorer_m2/proposed___init__.py`)*
4. **Update version-files manifest**:
   - Append `toml pyproject.toml` to `.mise/version-files.conf`.
   *(See proposed file `/home/delorenj/code/tiller-mcp-server/.agents/explorer_m2/proposed_version-files.conf`)*

---

## 5. Verification Method

Once changes are applied, the implementer can verify correctness by running:

```bash
# 1. Sync dependencies and toolchain
uv sync

# 2. Run Ruff linting check (expect 0 errors or easily fixable stylistic ones)
uv run ruff check

# 3. Run Ruff format check
uv run ruff format --check

# 4. Re-run version task to verify it reads pyproject.toml (should output v0.1.0)
mise run version
```
