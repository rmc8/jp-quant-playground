"""Unit tests for the data_fetcher module."""

import time
from unittest.mock import MagicMock, patch

import pytest


def test_retry_logic_with_exponential_backoff() -> None:
    """Test that fetch_with_retry attempts multiple times and returns None on failure."""
    from note.libs.data_fetcher import fetch_with_retry

    # Mock fetch_ticker_data to always return empty dict (failure)
    with patch("note.libs.data_fetcher.fetch_ticker_data") as mock_fetch:
        mock_fetch.return_value = {}  # Simulate failure (empty dict)

        result = fetch_with_retry("TEST.T", max_retries=3)

        # Verify it was called 3 times (initial + 2 retries)
        assert mock_fetch.call_count == 3, "Should attempt 3 times total"

        # Verify result is None after all retries failed
        assert result is None, "Should return None after all retries fail"


def test_retry_logic_succeeds_on_second_attempt() -> None:
    """Test that retry logic stops retrying once it succeeds."""
    from note.libs.data_fetcher import fetch_with_retry

    # Mock fetch_ticker_data to fail first time, succeed second time
    with patch("note.libs.data_fetcher.fetch_ticker_data") as mock_fetch:
        mock_fetch.side_effect = [
            {},  # First attempt fails (empty dict)
            {"ticker": "TEST.T", "market_cap": 1000000},  # Second attempt succeeds
        ]

        result = fetch_with_retry("TEST.T", max_retries=3)

        # Verify it was called exactly 2 times (stopped after success)
        assert mock_fetch.call_count == 2, "Should stop retrying after success"

        # Verify result is the successful data
        assert result is not None, "Should return data on success"
        assert result["ticker"] == "TEST.T", "Should return correct ticker data"


def test_fetch_ticker_data_handles_exceptions() -> None:
    """Test that fetch_ticker_data catches and logs exceptions."""
    from note.libs.data_fetcher import fetch_ticker_data

    # Mock yfinance.Ticker to raise an exception
    with patch("note.libs.data_fetcher.yf.Ticker") as mock_ticker:
        mock_ticker.side_effect = Exception("API Error")

        # Should not raise, should return empty dict
        result = fetch_ticker_data("INVALID.T")

        assert result == {}, "Should return empty dict when exception occurs"


def test_fetch_ticker_data_returns_dict_on_success() -> None:
    """Test that fetch_ticker_data returns a dict with expected fields."""
    from note.libs.data_fetcher import fetch_ticker_data

    # Mock yfinance.Ticker to return valid data
    with patch("note.libs.data_fetcher.yf.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "marketCap": 1000000000,
            "totalCash": 50000000,
            "totalDebt": 30000000,
        }
        mock_ticker_class.return_value = mock_ticker

        result = fetch_ticker_data("7203")

        assert result is not None, "Should return data dict on success"
        assert isinstance(result, dict), "Should return a dictionary"
        assert "ticker" in result, "Should include ticker field"
        assert result["ticker"] == "7203", "Should preserve original ticker code"


def test_japanese_ticker_suffix_handling() -> None:
    """Test that numeric ticker codes get .T suffix added for yfinance."""
    from note.libs.data_fetcher import fetch_ticker_data

    with patch("note.libs.data_fetcher.yf.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.info = {"marketCap": 1000000}
        mock_ticker_class.return_value = mock_ticker

        # Test with numeric ticker (should add .T)
        result = fetch_ticker_data("7203")

        # Verify yfinance.Ticker was called with .T suffix
        mock_ticker_class.assert_called_once_with("7203.T")

        # Verify returned ticker preserves original code
        assert result["ticker"] == "7203", (
            "Should return original ticker code without .T"
        )
