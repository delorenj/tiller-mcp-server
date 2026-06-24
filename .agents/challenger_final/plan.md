# Verification Plan - challenger_final

This plan outlines the steps to verify the refactoring of `tiller-mcp-server`.

## Steps

1. **Environment Setup & Sync**
   - Ensure the correct python/node environment is selected via `mise`.
   - Run `uv sync` or `mise run sync` to ensure dependencies are installed.

2. **Run Lint and Formatting Checks**
   - Run `mise run lint` to check for style/linting errors.
   - Run `mise run format` to check for formatting consistency.

3. **Run Unit Tests**
   - Run `mise run test` (which calls `uv run pytest`) to execute all unit tests.
   - Verify that all 23 mock-based unit tests pass successfully.

4. **Build Package Artifacts**
   - Run `mise run build` (which calls `uv build`).
   - Check that the built artifacts (`.tar.gz` and `.whl`) are generated under `dist/`.

5. **Verify CLI Executable & Help Outputs**
   - Run `uv run tiller-mcp-server --help` to ensure the entrypoint is configured correctly and prints CLI help output.

6. **Stress Test / Edge Cases**
   - Verify if any mock tests are flaky or slow.
   - Check if environment variables like `TILLER_SHEET_ID` are validated gracefully when the CLI is run.

7. **Compile Findings & Generate Handoff**
   - Write `/home/delorenj/code/tiller-mcp-server/.agents/challenger_final/handoff.md` following the 5-component report template.
   - Notify the parent orchestrator.
