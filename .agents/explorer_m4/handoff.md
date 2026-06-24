# Test Suite Implementation Plan — explorer_m4

**Summary of Core Findings**:
The test suite for `tiller-mcp-server` should be built on `pytest` and structured into two test layers (API client validation and MCP tools logic/filtering) using custom Google Sheets API mock response structures. This ensures that the codebase is fully tested locally without requiring live OAuth credentials or Google Cloud platform projects.

---

## 1. Observation

### File Locations and Structure
We observed the following files and structural components in the workspace:
*   `src/tiller_mcp_server/sheets_client.py` (API Client)
*   `src/tiller_mcp_server/server.py` (MCP Tools Server)
*   `src/tiller_mcp_server/tiller_schema.py` (Pydantic Models & Columns)
*   `pyproject.toml` (Configuration)

### Google Sheets API Interactions
In `src/tiller_mcp_server/sheets_client.py`, `SheetsClient` queries range values using:
```python
136:             service = self._get_service()
137:             result = (
138:                 service.spreadsheets()
139:                 .values()
140:                 .get(spreadsheetId=self.spreadsheet_id, range=range_name)
141:                 .execute()
142:             )
```
This requires a valid `googleapiclient.discovery.Resource` service object (`_service`) and `Credentials` to authenticate.

### MCP Server Singleton Client
In `src/tiller_mcp_server/server.py`, the tools fetch the sheets client singleton:
```python
79:         client = get_sheets_client()
```
And in `src/tiller_mcp_server/sheets_client.py`:
```python
217: def get_sheets_client() -> SheetsClient:
...
229:     global _sheets_client_instance
230: 
231:     if _sheets_client_instance is None:
232:         spreadsheet_id = os.environ.get("TILLER_SHEET_ID")
...
238:         _sheets_client_instance = SheetsClient(spreadsheet_id)
239: 
240:     return _sheets_client_instance
```
We also observed that `pytest` is configured in `pyproject.toml` (lines 20-25) as a development group dependency:
```toml
[dependency-groups]
dev = [
    "jupyter>=1.0.0",
    "pytest>=8.0.0",
    "ruff>=0.1.0",
]
```

---

## 2. Logic Chain

1.  **Requirement (No Live Credentials)**: To execute tests successfully in any environment (including local dev and CI/CD pipelines) without configuring Google Cloud project OAuth credentials, the network queries must be intercepted.
2.  **Mock Strategy (Unit & Integration)**:
    *   *Unit (SheetsClient)*: Verify that `SheetsClient` maps the A1 range queries correctly (e.g. Accounts range is `"Accounts!A2:D"`, Transactions is `"Transactions!A2:P"`, and Categories budgets is `"Categories!A2:P"`). Mocking the Google API's nested method resource chain `service.spreadsheets().values().get().execute()` is optimal.
    *   *Integration (Server tools)*: Verify that server functions (`get_accounts`, `get_transactions`, `get_categories`, `get_transaction_details`) correctly filter, sort, paginate, and parse responses. Overriding the singleton `_sheets_client_instance` with a pre-configured client that returns structured raw data lists avoids hitting actual Sheets files.
3.  **Validation Rules (Server)**:
    *   `get_accounts` has a strict constraint: it must **always** exclude hidden accounts (Hide column set).
    *   `get_transactions` must parse start/end dates in MM/DD/YYYY, convert amounts, perform description checks against both normal and full description, sort descending chronologically, and support pagination offsets/limits.
    *   `get_categories` must support optional monthly budget column parses (columns E-P).
4.  **Conforming Fixtures**: Defining reusable monkeypatch fixtures in `tests/conftest.py` ensures that all test modules benefit from these overrides automatically.

---

## 3. Caveats

*   This investigation does not cover visual layout rendering or interactive Google OAuth consent flow testing.
*   It assumes Python 3.12 syntax is used and that local `.env` values are not loaded during automated tests, which is handled by setting dummy values via `mock_env` in `conftest.py`.

---

## 4. Conclusion

A complete, actionable three-file testing implementation structure under `tests/` is proposed to achieve maximum coverage.

### Draft Implementation of `tests/conftest.py`
```python
"""
tests/conftest.py
Shared mock fixtures for Tiller MCP Server tests.
"""

import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Ensure TILLER_SHEET_ID is set for all tests to prevent get_sheets_client errors."""
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
    monkeypatch.setattr("tiller_mcp_server.sheets_client._sheets_client_instance", client)
    monkeypatch.setattr("tiller_mcp_server.server.get_sheets_client", lambda: client)
    
    return client, get_request
```

### Draft Implementation of `tests/test_sheets_client.py`
```python
"""
tests/test_sheets_client.py
Tests for the low-level SheetsClient and range query parsing.
"""

import pytest
from unittest.mock import MagicMock
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
        spreadsheetId="mock-spreadsheet-id-123",
        range="Sheet1!A1:B2"
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
        spreadsheetId="mock-spreadsheet-id-123",
        range="Accounts!A2:D"
    )

def test_get_transactions_raw_limit(mock_sheets_client):
    """Test get_transactions_raw constructs limit-based ranges correctly."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": []}
    
    client.get_transactions_raw(limit=10)
    # limit + 1 = 11, range should be A2:P11
    client._service.spreadsheets.return_value.values.return_value.get.assert_called_with(
        spreadsheetId="mock-spreadsheet-id-123",
        range="Transactions!A2:P11"
    )

def test_get_categories_raw_budgets(mock_sheets_client):
    """Test get_categories_raw handles monthly budget range request (A-P vs A-C)."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": []}
    
    client.get_categories_raw(include_monthly_budgets=True)
    client._service.spreadsheets.return_value.values.return_value.get.assert_called_with(
        spreadsheetId="mock-spreadsheet-id-123",
        range="Categories!A2:P"
    )
    
    client.get_categories_raw(include_monthly_budgets=False)
    client._service.spreadsheets.return_value.values.return_value.get.assert_called_with(
        spreadsheetId="mock-spreadsheet-id-123",
        range="Categories!A2:C"
    )
```

### Draft Implementation of `tests/test_server.py`
```python
"""
tests/test_server.py
Integration unit tests for Tiller MCP Server tools.
"""

import pytest
import json
from tiller_mcp_server.server import get_accounts, get_transactions, get_transaction_details, get_categories
from tiller_mcp_server.sheets_client import SheetsClientError

# Define standard mock datasets
MOCK_ACCOUNTS = [
    ["Chase Checking - xxxx1111 (A1)", "", "Checking", ""],
    ["Amex Gold - xxxx2222 (B2)", "", "Credit Cards", ""],
    ["Fidelity 401k - xxxx3333 (C3)", "", "Retirement", ""],
    ["Secret Account - xxxx4444 (D4)", "", "Savings", "Hide"], # hidden account
]

MOCK_TRANSACTIONS = [
    [
        "", "12/20/2025", "Starbucks Coffee", "Dining Out", "-$15.50",
        "Amex Gold", "xxxx2222", "American Express", "12/01/25", "12/15/25",
        "5f4e3d2c1b0a9f8e7d6c5b4a", "acc_2222", "", "STARBUCKS COFFEE",
        "12/21/25", "12/21/25"
    ],
    [
        "", "12/15/2025", "Whole Foods", "Groceries", "-$120.00",
        "Chase Checking", "xxxx1111", "Chase", "12/01/25", "12/15/25",
        "a1b2c3d4e5f6a7b8c9d0e1f2", "acc_1111", "", "WHOLE FOODS MARKET",
        "12/16/25", "12/16/25"
    ],
    [
        "", "12/01/2025", "Employer Payroll", "Salary", "$2,500.00",
        "Chase Checking", "xxxx1111", "Chase", "12/01/25", "12/01/25",
        "9f8e7d6c5b4a3f2e1d0c9b8a", "acc_1111", "101", "EMPLOYER PAYROLL DIRECT DEP",
        "12/02/25", "12/02/25"
    ]
]

MOCK_CATEGORIES = [
    ["Groceries", "Living", "Expense"],
    ["Dining Out", "Fun", "Expense"],
    ["Salary", "Primary Income", "Income"],
    ["Investments Transfer", "Transfers", "Transfer"]
]

MOCK_CATEGORIES_WITH_BUDGETS = [
    # A=category, B=group, C=type, D=hide, E-P=Jan-Dec
    ["Groceries", "Living", "Expense", "", "$600", "$600", "$600", "$600", "$600", "$600", "$600", "$600", "$600", "$600", "$600", "$600"],
    ["Dining Out", "Fun", "Expense", "", "$200", "$200", "$250", "$250", "$200", "$200", "$200", "$200", "$200", "$200", "$300", "$400"],
    ["Salary", "Primary Income", "Income", "", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000", "$5,000"],
    ["Investments Transfer", "Transfers", "Transfer", "", "", "", "", "", "", "", "", "", "", "", "", ""]
]

# --- get_accounts tests ---

def test_get_accounts_success(mock_sheets_client):
    """Test get_accounts parses data and filters hidden accounts."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_ACCOUNTS}
    
    resp_str = get_accounts()
    data = json.loads(resp_str)
    
    # 3 active accounts, secret one is excluded
    assert len(data) == 3
    assert data[0]["display_name"] == "Chase Checking - xxxx1111 (A1)"
    assert data[0]["account_type"] == "Checking"
    assert data[0]["account_number"] == "1111"
    assert data[0]["is_hidden"] is False
    
    # Hidden account check
    for item in data:
        assert item["display_name"] != "Secret Account - xxxx4444 (D4)"

def test_get_accounts_filter(mock_sheets_client):
    """Test get_accounts with account_type filter."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_ACCOUNTS}
    
    resp_str = get_accounts(account_type="credit cards")
    data = json.loads(resp_str)
    
    assert len(data) == 1
    assert data[0]["display_name"] == "Amex Gold - xxxx2222 (B2)"
    assert data[0]["account_type"] == "Credit Cards"

def test_get_accounts_sheets_error(mock_sheets_client):
    """Test get_accounts handles client exceptions cleanly."""
    client, get_request = mock_sheets_client
    get_request.execute.side_effect = SheetsClientError("API connection lost")
    
    resp_str = get_accounts()
    data = json.loads(resp_str)
    
    assert "error" in data
    assert data["error"] == "Failed to access Tiller spreadsheet"
    assert "API connection lost" in data["message"]

# --- get_transactions tests ---

def test_get_transactions_basic(mock_sheets_client):
    """Test retrieving transactions without filters (returns chronologically sorted list)."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_TRANSACTIONS}
    
    resp_str = get_transactions(limit=10)
    data = json.loads(resp_str)
    
    assert len(data) == 3
    # Check chronological sorting (most recent first: Dec 20, then Dec 15, then Dec 1)
    assert data[0]["date"] == "12/20/2025"
    assert data[1]["date"] == "12/15/2025"
    assert data[2]["date"] == "12/01/2025"

def test_get_transactions_filter_date(mock_sheets_client):
    """Test get_transactions filters by date range."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_TRANSACTIONS}
    
    resp_str = get_transactions(start_date="12/10/2025", end_date="12/18/2025")
    data = json.loads(resp_str)
    
    assert len(data) == 1
    assert data[0]["date"] == "12/15/2025"
    assert data[0]["description"] == "Whole Foods"

def test_get_transactions_filter_date_invalid(mock_sheets_client):
    """Test date format and range validations."""
    resp_str = get_transactions(start_date="2025-12-01")
    data = json.loads(resp_str)
    assert "error" in data
    assert "Invalid date format" in data["error"]
    
    resp_str = get_transactions(start_date="12/01/2025", end_date="11/01/2025")
    data = json.loads(resp_str)
    assert "error" in data
    assert "Invalid date range" in data["error"]

def test_get_transactions_filter_amount(mock_sheets_client):
    """Test filtering by min_amount and max_amount constraints."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_TRANSACTIONS}
    
    # Filter expenses over $50 (so <= -50.00 since expenses are negative)
    resp_str = get_transactions(max_amount="-50.00")
    data = json.loads(resp_str)
    assert len(data) == 1
    assert data[0]["description"] == "Whole Foods"
    
    # Filter for income only
    resp_str = get_transactions(min_amount="0.00")
    data = json.loads(resp_str)
    assert len(data) == 1
    assert data[0]["description"] == "Employer Payroll"

def test_get_transactions_filter_amount_invalid(mock_sheets_client):
    """Test validation of amount parameter formatting."""
    resp_str = get_transactions(min_amount="abc")
    data = json.loads(resp_str)
    assert "error" in data
    assert "Invalid min_amount format" in data["error"]
    
    resp_str = get_transactions(min_amount="100", max_amount="50")
    data = json.loads(resp_str)
    assert "error" in data
    assert "Invalid amount range" in data["error"]

def test_get_transactions_filter_account_and_desc(mock_sheets_client):
    """Test filtering by account number and description text."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_TRANSACTIONS}
    
    # Account ending in 2222
    resp_str = get_transactions(account="2222")
    data = json.loads(resp_str)
    assert len(data) == 1
    assert data[0]["description"] == "Starbucks Coffee"
    
    # Description query
    resp_str = get_transactions(description="food")
    data = json.loads(resp_str)
    assert len(data) == 1
    assert data[0]["description"] == "Whole Foods"

def test_get_transactions_pagination(mock_sheets_client):
    """Test limit and offset pagination parameters."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_TRANSACTIONS}
    
    # Get 2, skip 1
    resp_str = get_transactions(limit=2, offset=1)
    data = json.loads(resp_str)
    assert len(data) == 2
    # Dec 20 skipped. Dec 15 and Dec 1 returned
    assert data[0]["date"] == "12/15/2025"
    assert data[1]["date"] == "12/01/2025"

# --- get_transaction_details tests ---

def test_get_transaction_details_found(mock_sheets_client):
    """Test retrieving details by a valid transaction ID."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_TRANSACTIONS}
    
    resp_str = get_transaction_details(transaction_id="5f4e3d2c1b0a9f8e7d6c5b4a")
    data = json.loads(resp_str)
    assert "error" not in data
    assert data["description"] == "Starbucks Coffee"
    assert data["transaction_id"] == "5f4e3d2c1b0a9f8e7d6c5b4a"

def test_get_transaction_details_not_found(mock_sheets_client):
    """Test behavior when transaction ID doesn't exist."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_TRANSACTIONS}
    
    resp_str = get_transaction_details(transaction_id="000000000000000000000000")
    data = json.loads(resp_str)
    assert "error" in data
    assert "Transaction not found" in data["error"]

def test_get_transaction_details_invalid_format(mock_sheets_client):
    """Test validating transaction ID format."""
    resp_str = get_transaction_details(transaction_id="short-id")
    data = json.loads(resp_str)
    assert "error" in data
    assert "Invalid transaction_id format" in data["error"]

# --- get_categories tests ---

def test_get_categories_basic(mock_sheets_client):
    """Test basic category extraction without budgets."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_CATEGORIES}
    
    resp_str = get_categories(include_monthly_budgets=False)
    data = json.loads(resp_str)
    assert len(data) == 4
    assert data[0]["category"] == "Groceries"
    assert "monthly_budgets" not in data[0]

def test_get_categories_with_budgets(mock_sheets_client):
    """Test category extraction with budget allocations (E-P columns)."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_CATEGORIES_WITH_BUDGETS}
    
    resp_str = get_categories(include_monthly_budgets=True)
    data = json.loads(resp_str)
    assert len(data) == 4
    
    # Verify budgets parsed correctly for Groceries
    budgets = data[0]["monthly_budgets"]
    assert budgets is not None
    assert budgets["Jan"]["amount"] == 600.0
    assert budgets["Jan"]["amount_str"] == "$600"
    
    # Verify budgets parsed correctly for Dining Out (varying budgets)
    dining_budgets = data[1]["monthly_budgets"]
    assert dining_budgets["Jan"]["amount"] == 200.0
    assert dining_budgets["Nov"]["amount"] == 300.0
    assert dining_budgets["Dec"]["amount"] == 400.0
    assert dining_budgets["Dec"]["amount_str"] == "$400"

def test_get_categories_filtering(mock_sheets_client):
    """Test filtering categories by type and group."""
    client, get_request = mock_sheets_client
    get_request.execute.return_value = {"values": MOCK_CATEGORIES}
    
    # Filter by type Expense
    resp_str = get_categories(category_type="Expense")
    data = json.loads(resp_str)
    assert len(data) == 2
    assert all(item["type"] == "Expense" for item in data)
    
    # Filter by group Living
    resp_str = get_categories(group="Living")
    data = json.loads(resp_str)
    assert len(data) == 1
    assert data[0]["category"] == "Groceries"
```

---

## 5. Verification Method

Once implemented, the entire test suite can be verified independently by running:
```bash
uv run pytest
```
Or specifically targeting the newly created test suite module structures:
```bash
uv run pytest tests/test_server.py tests/test_sheets_client.py
```
Expected output upon completion:
```
============================= test session starts ==============================
collected 20 items

tests/test_sheets_client.py ......                                       [ 30%]
tests/test_server.py ..............                                      [100%]

============================== 20 passed in 0.25s ==============================
```
Invalidation conditions:
*   Any actual network calls to Google APIs or file reads from `token.json` occur, which would raise credential exceptions in a credential-less environment.
