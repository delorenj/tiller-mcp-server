"""Tests for the low-level SheetsClient and range query parsing."""

from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from tiller_mcp_server.sheets_client import SheetsClient, SheetsClientError


def test_sheets_client_init():
    """Test client initialization constraints."""
    with pytest.raises(SheetsClientError, match="spreadsheet_id is required"):
        SheetsClient("")

    client = SheetsClient("fake-id")
    assert client.spreadsheet_id == "fake-id"


def test_get_sheet_range_success(mock_sheets_client):
    """Test that get_sheet_range successfully queries the API and returns values."""
    client, get_request = mock_sheets_client

    # Mock successful API response
    get_request.execute.return_value = {
        "values": [["Header1", "Header2"], ["Val1", "Val2"]]
    }

    values = client.get_sheet_range("Sheet1!A1:B2")
    assert values == [["Header1", "Header2"], ["Val1", "Val2"]]

    # Verify the correct arguments were passed to Google client
    client._service.spreadsheets.return_value.values.return_value.get.assert_called_once_with(
        spreadsheetId="mock-spreadsheet-id-123", range="Sheet1!A1:B2"
    )


def test_get_sheet_range_empty(mock_sheets_client):
    """Test get_sheet_range when the sheet is empty (no values key)."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {}  # Empty response

    values = client.get_sheet_range("Sheet1!A1:B2")
    assert values == []


def test_get_sheet_range_http_error(mock_sheets_client):
    """Test get_sheet_range raises SheetsClientError on HttpError."""
    client, get_request = mock_sheets_client

    resp = MagicMock(status=404)
    get_request.execute.side_effect = HttpError(resp, b"Not Found")

    with pytest.raises(SheetsClientError, match="Failed to read range"):
        client.get_sheet_range("Sheet1!A1:B2")


def test_get_accounts_raw(mock_sheets_client):
    """Test get_accounts_raw makes the correct range query (Accounts!A2:D)."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": [["Acc1", "", "Checking", ""]]}

    res = client.get_accounts_raw()
    assert res == [["Acc1", "", "Checking", ""]]

    client._service.spreadsheets.return_value.values.return_value.get.assert_called_with(
        spreadsheetId="mock-spreadsheet-id-123", range="Accounts!A2:D"
    )


def test_get_transactions_raw_limit(mock_sheets_client):
    """Test get_transactions_raw constructs limit-based ranges correctly."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": []}

    client.get_transactions_raw(limit=10)
    # limit + 1 = 11, range should be A2:P11
    client._service.spreadsheets.return_value.values.return_value.get.assert_called_with(
        spreadsheetId="mock-spreadsheet-id-123", range="Transactions!A2:P11"
    )


def test_get_categories_raw_budgets(mock_sheets_client):
    """Test get_categories_raw handles monthly budget range request (A-P vs A-C)."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": []}

    client.get_categories_raw(include_monthly_budgets=True)
    client._service.spreadsheets.return_value.values.return_value.get.assert_called_with(
        spreadsheetId="mock-spreadsheet-id-123", range="Categories!A2:P"
    )

    client.get_categories_raw(include_monthly_budgets=False)
    client._service.spreadsheets.return_value.values.return_value.get.assert_called_with(
        spreadsheetId="mock-spreadsheet-id-123", range="Categories!A2:C"
    )
