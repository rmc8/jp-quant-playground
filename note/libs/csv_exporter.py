"""CSV export functionality with TSV input reading.

This module handles reading ticker codes from TSV files and exporting
financial data with calculated indicators to CSV format.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import polars as pl

from note.libs import indicators


def filter_individual_stocks(df: pl.DataFrame) -> pl.DataFrame:
    """Filter out ETF/ETN from DataFrame, keeping only individual stocks.

    Args:
        df: DataFrame read from TSV file with market category column

    Returns:
        DataFrame containing only individual stocks (ETF/ETN excluded)
    """
    # Column index 3 (4th column) contains market category
    # Filter out rows where market category is "ETF・ETN"
    market_col = df.columns[3] if len(df.columns) > 3 else None

    if market_col is None:
        logging.warning("Market category column not found, returning all data")
        return df

    total_count = len(df)
    filtered_df = df.filter(pl.col(market_col) != "ETF・ETN")
    individual_count = len(filtered_df)
    etf_count = total_count - individual_count

    logging.info(
        f"Filtered {individual_count} individual stocks (excluded {etf_count} ETF/ETN)"
    )

    return filtered_df


def read_tickers_from_tsv(
    tsv_path: str,
    ticker_column: int = 1,
    limit: Optional[int] = None,
    exclude_etf: bool = True,
) -> list[str]:
    """Read ticker codes from TSV file.

    Args:
        tsv_path: Path to TSV file
        ticker_column: Column index for ticker codes (default: 1 for 2nd column)
        limit: Maximum number of tickers to read (default: None for all)
        exclude_etf: Exclude ETF/ETN from results (default: True)

    Returns:
        List of ticker codes
    """
    try:
        df = pl.read_csv(tsv_path, separator="\t", has_header=True)

        # Filter out ETF/ETN if requested
        if exclude_etf:
            df = filter_individual_stocks(df)

        # Get column by index
        if ticker_column >= len(df.columns):
            logging.error(
                f"Column index {ticker_column} out of range. File has {len(df.columns)} columns."
            )
            return []

        column_name = df.columns[ticker_column]
        tickers = df[column_name].drop_nulls().to_list()

        # Apply limit if specified
        if limit is not None and limit > 0:
            tickers = tickers[:limit]
            logging.info(f"Limited to first {limit} tickers")

        logging.info(f"Read {len(tickers)} ticker codes from {tsv_path}")
        return tickers

    except Exception as e:
        logging.error(f"Failed to read TSV file {tsv_path}: {e}")
        return []


def build_dataframe(ticker_data_list: list[dict]) -> pl.DataFrame:
    """Build polars DataFrame from list of ticker data dictionaries.

    Args:
        ticker_data_list: List of dictionaries containing financial data

    Returns:
        Polars DataFrame with raw financial data columns
    """
    if not ticker_data_list:
        logging.warning("Empty ticker data list, returning empty DataFrame")
        return pl.DataFrame()

    # Filter out None values and empty dicts
    valid_data = [d for d in ticker_data_list if d and isinstance(d, dict)]

    if not valid_data:
        logging.warning("No valid data after filtering, returning empty DataFrame")
        return pl.DataFrame()

    # Create DataFrame from list of dictionaries
    df = pl.DataFrame(valid_data)
    logging.info(f"Built DataFrame with {len(df)} rows and {len(df.columns)} columns")

    return df


def merge_tsv_metadata(
    df: pl.DataFrame, tsv_path: str, ticker_column: int = 1
) -> pl.DataFrame:
    """Merge TSV metadata (stock name, sector, market category) into DataFrame.

    Args:
        df: DataFrame with ticker column
        tsv_path: Path to TSV file containing metadata
        ticker_column: Column index for ticker codes (default: 1 for 2nd column)

    Returns:
        DataFrame with additional metadata columns from TSV
    """
    if df.is_empty():
        logging.warning("Empty DataFrame, skipping metadata merge")
        return df

    try:
        # Read TSV file
        tsv_df = pl.read_csv(tsv_path, separator="\t", has_header=True)

        # Select relevant columns:
        # - Column 1 (index 1): ticker code
        # - Column 2 (index 2): stock name
        # - Column 3 (index 3): market category
        # - Column 5 (index 5): 33-sector category
        # - Column 7 (index 7): 17-sector category
        metadata_cols = [
            tsv_df.columns[1],  # ticker code
            tsv_df.columns[2],  # stock name
            tsv_df.columns[3],  # market category
            tsv_df.columns[5],  # 33-sector category
            tsv_df.columns[7],  # 17-sector category
        ]

        tsv_metadata = tsv_df.select(metadata_cols)

        # Rename columns to English
        ticker_col_name = tsv_metadata.columns[0]
        tsv_metadata = tsv_metadata.rename(
            {
                tsv_metadata.columns[1]: "stock_name",
                tsv_metadata.columns[2]: "market_category",
                tsv_metadata.columns[3]: "sector_33",
                tsv_metadata.columns[4]: "sector_17",
            }
        )

        # Join with main DataFrame on ticker column
        merged_df = df.join(
            tsv_metadata, left_on="ticker", right_on=ticker_col_name, how="left"
        )

        logging.info(
            f"Merged TSV metadata. Added {len(merged_df.columns) - len(df.columns)} columns"
        )

        return merged_df

    except Exception as e:
        logging.error(f"Failed to merge TSV metadata: {e}")
        return df


def add_indicators_to_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    """Add calculated fundamental indicators to DataFrame.

    Args:
        df: DataFrame with raw financial data

    Returns:
        DataFrame with additional indicator columns
    """
    if df.is_empty():
        logging.warning("Empty DataFrame, skipping indicator calculation")
        return df

    try:
        # Calculate indicators using note/libs/indicators.py functions
        # Note: ROIC, CROIC, and Piotroski F-score require data not available from yfinance
        # First calculate enterprise value, then use it for EV-based ratios
        df_with_ev = df.with_columns(
            [
                # Net Cash Ratio
                indicators.calculate_net_cash_ratio(
                    pl.col("total_cash"), pl.col("total_debt"), pl.col("market_cap")
                ).alias("net_cash_ratio"),
                # Enterprise Value (needed for EV/EBIT and EV/FCF)
                indicators.calculate_enterprise_value(
                    pl.col("market_cap"), pl.col("total_debt"), pl.col("total_cash")
                ).alias("enterprise_value"),
                # Gross Profitability
                indicators.calculate_gross_profitability(
                    pl.col("gross_profit"), pl.col("total_assets")
                ).alias("gross_profitability"),
                # FCF Yield
                indicators.calculate_fcf_yield(
                    pl.col("operating_cash_flow"),
                    pl.col("capex"),
                    pl.col("market_cap"),
                ).alias("fcf_yield"),
                # PBR
                indicators.calculate_pbr(
                    pl.col("market_cap"), pl.col("book_value")
                ).alias("pbr"),
            ]
        )

        # Now add EV-based ratios using the calculated enterprise_value
        df_with_ev_ratios = df_with_ev.with_columns(
            [
                # EV/EBIT
                indicators.calculate_ev_ebit(
                    pl.col("enterprise_value"),
                    pl.col("ebit"),
                ).alias("ev_ebit"),
                # EV/FCF
                indicators.calculate_ev_fcf(
                    pl.col("enterprise_value"),
                    pl.col("operating_cash_flow"),
                    pl.col("capex"),
                ).alias("ev_fcf"),
            ]
        )

        # Add valuation metrics for value/dividend investing
        df_with_indicators = df_with_ev_ratios.with_columns(
            [
                # PSR (Price to Sales Ratio) = Market Cap / Total Revenue
                (pl.col("market_cap") / pl.col("total_revenue")).alias("psr"),
                # PEG Ratio = PER / Earnings Growth Rate (%)
                # earnings_growth is decimal (0.15 = 15%), convert to percentage
                (pl.col("trailing_pe") / (pl.col("earnings_growth") * 100)).alias(
                    "peg_ratio"
                ),
            ]
        )

        logging.info(
            f"Added indicators to DataFrame. Total columns: {len(df_with_indicators.columns)}"
        )
        return df_with_indicators

    except Exception as e:
        logging.error(f"Failed to calculate indicators: {e}")
        return df


def add_earnings_flags(df: pl.DataFrame) -> pl.DataFrame:
    """Add earnings growth flag based on 3-year consecutive earnings growth.

    Args:
        df: DataFrame with earnings_y0, earnings_y1, earnings_y2 columns

    Returns:
        DataFrame with additional consecutive_earnings_growth column (bool)
    """
    if df.is_empty():
        logging.warning("Empty DataFrame, skipping earnings flags calculation")
        return df

    try:
        # Calculate 3-year consecutive earnings growth flag
        # True if: earnings_y0 > earnings_y1 > earnings_y2 (all not null)
        df_with_flag = df.with_columns(
            [
                (
                    (pl.col("earnings_y0").is_not_null())
                    & (pl.col("earnings_y1").is_not_null())
                    & (pl.col("earnings_y2").is_not_null())
                    & (pl.col("earnings_y0") > pl.col("earnings_y1"))
                    & (pl.col("earnings_y1") > pl.col("earnings_y2"))
                ).alias("consecutive_earnings_growth")
            ]
        )

        logging.info("Added consecutive earnings growth flag")
        return df_with_flag

    except Exception as e:
        logging.error(f"Failed to add earnings flags: {e}")
        return df


def reorder_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Reorder DataFrame columns for better readability.

    Column order:
    1. ticker
    2. Metadata: stock_name, market_category, sector_33, sector_17
    3. Dividend metrics: dividend_yield, payout_ratio
    4. Earnings: earnings_y0, earnings_y1, earnings_y2, consecutive_earnings_growth
    5. Valuation: trailing_pe, psr, peg_ratio
    6. Raw financial data: market_cap, total_cash, etc.
    7. Calculated indicators: net_cash_ratio, ev, etc.

    Args:
        df: DataFrame to reorder

    Returns:
        DataFrame with reordered columns
    """
    if df.is_empty():
        return df

    # Define column order groups
    priority_cols = ["ticker"]
    metadata_cols = ["stock_name", "market_category", "sector_33", "sector_17"]
    dividend_cols = ["dividend_yield", "payout_ratio"]
    earnings_cols = [
        "earnings_y0",
        "earnings_y1",
        "earnings_y2",
        "consecutive_earnings_growth",
    ]
    valuation_cols = ["trailing_pe", "psr", "peg_ratio"]

    # Get all existing columns from each group
    existing_priority = [c for c in priority_cols if c in df.columns]
    existing_metadata = [c for c in metadata_cols if c in df.columns]
    existing_dividend = [c for c in dividend_cols if c in df.columns]
    existing_earnings = [c for c in earnings_cols if c in df.columns]
    existing_valuation = [c for c in valuation_cols if c in df.columns]

    # All other columns (preserve their order)
    other_cols = [
        c
        for c in df.columns
        if c
        not in existing_priority
        + existing_metadata
        + existing_dividend
        + existing_earnings
        + existing_valuation
    ]

    # Combine in desired order
    new_order = (
        existing_priority
        + existing_metadata
        + existing_dividend
        + existing_earnings
        + existing_valuation
        + other_cols
    )

    return df.select(new_order)


def export_to_csv(df: pl.DataFrame, output_dir: str = "note/data/exports/") -> str:
    """Export DataFrame to CSV with timestamp in filename.

    Args:
        df: Polars DataFrame to export
        output_dir: Output directory path (default: note/data/exports/)

    Returns:
        Path to exported CSV file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stock_data_{timestamp}.csv"
    filepath = output_path / filename

    # Export to CSV
    df.write_csv(filepath)
    logging.info(f"Exported {len(df)} rows to {filepath}")

    return str(filepath)
