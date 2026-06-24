"""Integration unit tests for Tiller MCP Server tools."""

import json

from tiller_mcp_server.server import (
    get_accounts,
    get_categories,
    get_transaction_details,
    get_transactions,
)
from tiller_mcp_server.sheets_client import SheetsClientError

# Define standard mock datasets
MOCK_ACCOUNTS = [
    ["Chase Checking - xxxx1111 (A1)", "", "Checking", ""],
    ["Amex Gold - xxxx2222 (B2)", "", "Credit Cards", ""],
    ["Fidelity 401k - xxxx3333 (C3)", "", "Retirement", ""],
    ["Secret Account - xxxx4444 (D4)", "", "Savings", "Hide"],  # hidden account
]

MOCK_TRANSACTIONS = [
    [
        "",
        "12/20/2025",
        "Starbucks Coffee",
        "Dining Out",
        "-$15.50",
        "Amex Gold",
        "xxxx2222",
        "American Express",
        "12/01/25",
        "12/15/25",
        "5f4e3d2c1b0a9f8e7d6c5b4a",
        "acc_2222",
        "",
        "STARBUCKS COFFEE",
        "12/21/25",
        "12/21/25",
    ],
    [
        "",
        "12/15/2025",
        "Whole Foods",
        "Groceries",
        "-$120.00",
        "Chase Checking",
        "xxxx1111",
        "Chase",
        "12/01/25",
        "12/15/25",
        "a1b2c3d4e5f6a7b8c9d0e1f2",
        "acc_1111",
        "",
        "WHOLE FOODS MARKET",
        "12/16/25",
        "12/16/25",
    ],
    [
        "",
        "12/01/2025",
        "Employer Payroll",
        "Salary",
        "$2,500.00",
        "Chase Checking",
        "xxxx1111",
        "Chase",
        "12/01/25",
        "12/01/25",
        "9f8e7d6c5b4a3f2e1d0c9b8a",
        "acc_1111",
        "101",
        "EMPLOYER PAYROLL DIRECT DEP",
        "12/02/25",
        "12/02/25",
    ],
]

MOCK_CATEGORIES = [
    ["Groceries", "Living", "Expense"],
    ["Dining Out", "Fun", "Expense"],
    ["Salary", "Primary Income", "Income"],
    ["Investments Transfer", "Transfers", "Transfer"],
]

MOCK_CATEGORIES_WITH_BUDGETS = [
    # A=category, B=group, C=type, D=hide, E-P=Jan-Dec
    [
        "Groceries",
        "Living",
        "Expense",
        "",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
        "$600",
    ],
    [
        "Dining Out",
        "Fun",
        "Expense",
        "",
        "$200",
        "$200",
        "$250",
        "$250",
        "$200",
        "$200",
        "$200",
        "$200",
        "$200",
        "$200",
        "$300",
        "$400",
    ],
    [
        "Salary",
        "Primary Income",
        "Income",
        "",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
        "$5,000",
    ],
    [
        "Investments Transfer",
        "Transfers",
        "Transfer",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ],
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
    """Test retrieving transactions without filters (returns sorted list)."""
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
