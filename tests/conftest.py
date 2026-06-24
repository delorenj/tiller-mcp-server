"""Shared mock fixtures for Tiller MCP Server tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Ensure TILLER_SHEET_ID is set for all tests.

    This prevents get_sheets_client errors.
    """
    monkeypatch.setenv("TILLER_SHEET_ID", "mock-spreadsheet-id-123")


@pytest.fixture
def mock_sheets_service():
    """Mock Google Sheets API service resource chain."""
    service = MagicMock()
    spreadsheets = MagicMock()
    values = MagicMock()
    get_request = MagicMock()

    service.spreadsheets.return_value = spreadsheets
    spreadsheets.values.return_value = values
    values.get.return_value = get_request

    return service, get_request


@pytest.fixture
def mock_sheets_client(monkeypatch, mock_sheets_service):
    """Provide a SheetsClient with mocked _get_service and credentials."""
    from tiller_mcp_server.sheets_client import SheetsClient

    client = SheetsClient("mock-spreadsheet-id-123")

    # Mock credentials loading to skip OAuth2 file searches
    client._credentials = MagicMock()
    client._credentials.valid = True

    # Mock the internal service
    service, get_request = mock_sheets_service
    client._service = service

    # Inject singleton mock so get_sheets_client() returns this mocked instance
    monkeypatch.setattr(
        "tiller_mcp_server.sheets_client._sheets_client_instance", client
    )
    monkeypatch.setattr("tiller_mcp_server.server.get_sheets_client", lambda: client)

    return client, get_request
