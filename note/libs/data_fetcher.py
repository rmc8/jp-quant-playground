"""yfinance data fetcher with retry logic.

This module provides functions to fetch stock financial data from yfinance API
with robust error handling and exponential backoff retry logic.
"""

import logging
import time
from typing import Optional

import yfinance as yf


def fetch_ticker_data(ticker: str) -> dict:
    """Fetch financial data for a single ticker from yfinance.

    Args:
        ticker: Stock ticker code (e.g., "7203" or "7203.T" for Toyota)
                If ticker is numeric only, ".T" suffix is automatically added for Tokyo exchange

    Returns:
        Dictionary containing financial data fields:
        - ticker: Stock ticker code (original format)
        - market_cap: Market capitalization
        - total_cash: Cash and cash equivalents
        - total_debt: Total debt
        - total_assets: Total assets
        - book_value: Stockholders equity
        - operating_cash_flow: Operating cash flow
        - capex: Capital expenditure
        - ebit: EBIT (Earnings Before Interest and Taxes)
        - gross_profit: Gross profit
        - net_income: Net income

        Returns empty dict {} if fetching fails.
    """
    try:
        # Auto-append .T suffix for Japanese stocks (numeric-only tickers)
        yf_ticker = ticker
        if ticker.isdigit():
            yf_ticker = f"{ticker}.T"
            logging.debug(f"Converting ticker {ticker} to {yf_ticker}")

        stock = yf.Ticker(yf_ticker)
        info = stock.info

        # Extract financial metrics with safe gets
        data = {
            "ticker": ticker,
            "market_cap": info.get("marketCap"),
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            "total_assets": info.get("totalAssets"),
            "book_value": info.get("bookValue"),
            "operating_cash_flow": info.get("operatingCashflow"),
            "capex": info.get("capitalExpenditures"),
            "ebit": info.get("ebit"),
            "gross_profit": info.get("grossProfits"),
            "net_income": info.get("netIncomeToCommon"),
            "dividend_yield": info.get("dividendYield"),
            # Valuation metrics for value/dividend investing
            "trailing_pe": info.get("trailingPE"),
            "total_revenue": info.get("totalRevenue"),
            "earnings_growth": info.get("earningsGrowth"),
            "payout_ratio": info.get("payoutRatio"),
        }

        # Check if we got at least some data
        non_null_values = sum(1 for v in data.values() if v is not None)
        if non_null_values > 1:  # More than just ticker
            logging.info(
                f"Successfully fetched data for {ticker} ({non_null_values} fields)"
            )
            return data
        else:
            logging.warning(f"No financial data available for {ticker}")
            return {}

    except Exception as e:
        logging.error(f"Failed to fetch data for {ticker}: {e}")
        return {}


def fetch_with_retry(ticker: str, max_retries: int = 3) -> Optional[dict]:
    """Fetch ticker data with exponential backoff retry logic.

    Retry strategy: exponential backoff with 1s, 2s, 4s wait times.

    Args:
        ticker: Stock ticker code
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        Dictionary of financial data, or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            data = fetch_ticker_data(ticker)
            if data:  # If we got some data, return it
                return data
            # If empty dict, fall through to retry
        except (ConnectionError, TimeoutError, Exception) as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # 1, 2, 4 seconds
                logging.warning(
                    f"Retry {attempt + 1}/{max_retries} for {ticker} after {wait_time}s: {e}"
                )
                time.sleep(wait_time)
            else:
                logging.error(f"Failed after {max_retries} attempts: {ticker}")
                return None

    # If we got here, all retries returned empty dict
    logging.error(f"Failed after {max_retries} attempts: {ticker}")
    return None


def fetch_earnings_history(ticker: str) -> dict:
    """Fetch historical earnings data (3 years) from yfinance.

    Args:
        ticker: Stock ticker code

    Returns:
        Dictionary containing:
        - earnings_y0: Most recent year net income
        - earnings_y1: Previous year net income
        - earnings_y2: 2 years ago net income
        Returns empty values (None) if data not available
    """
    try:
        # Auto-append .T suffix for Japanese stocks
        yf_ticker = ticker
        if ticker.isdigit():
            yf_ticker = f"{ticker}.T"

        stock = yf.Ticker(yf_ticker)
        earnings = stock.earnings  # Annual earnings DataFrame

        if earnings is None or earnings.empty:
            logging.warning(f"No earnings data available for {ticker}")
            return {"earnings_y0": None, "earnings_y1": None, "earnings_y2": None}

        # earnings DataFrame has 'Revenue' and 'Earnings' columns
        # Sort by index (year) in descending order to get most recent first
        earnings_sorted = earnings.sort_index(ascending=False)

        # Extract last 3 years of net income (Earnings column)
        earnings_list = (
            earnings_sorted["Earnings"].tolist()
            if "Earnings" in earnings_sorted.columns
            else []
        )

        result = {
            "earnings_y0": earnings_list[0] if len(earnings_list) > 0 else None,
            "earnings_y1": earnings_list[1] if len(earnings_list) > 1 else None,
            "earnings_y2": earnings_list[2] if len(earnings_list) > 2 else None,
        }

        logging.debug(f"Fetched earnings history for {ticker}: {result}")
        return result

    except Exception as e:
        logging.error(f"Failed to fetch earnings history for {ticker}: {e}")
        return {"earnings_y0": None, "earnings_y1": None, "earnings_y2": None}
