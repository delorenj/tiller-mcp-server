# Project: tiller-mcp-server

## Architecture
- The tiller-mcp-server is an MCP server built on FastMCP to interface with Google Sheets personal finance tracking (Tiller).
- It comprises:
  - `tiller_schema.py` for pydantic models.
  - `sheets_client.py` for API interaction.
  - `server.py` for defining MCP tools and running the server.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Planning and Decomposing | Create execution plan and project metadata | None | DONE |
| 2 | Refactoring Package Structure | Transition to hatchling, dependency configuration, configure ruff | M1 | DONE |
| 3 | Rebranding to delorenj | Rebrand license, README, URLs to delorenj, remove Jack Stein | M2 | DONE |
| 4 | Test Suite Implementation | Mock-based unit testing for google sheets client and server tools | M3 | DONE |
| 5 | Integration & Final Verification | uv run execution entry points, mise.toml configuration, audit | M4 | DONE |

## Code Layout
- `src/tiller_mcp_server/`
  - `__init__.py`
  - `server.py`
  - `sheets_client.py`
  - `tiller_schema.py`
- `tests/`
  - Mock tests (to be created)
- `pyproject.toml`
- `mise.toml`
