"""CLI tool to export stock financial data with fundamental indicators.

Usage:
    uv run python note/scripts/export_stock_data.py --limit 5
    uv run python note/scripts/export_stock_data.py --input path/to/file.tsv
    uv run python note/scripts/export_stock_data.py --output path/to/output/
"""

import logging
import sys
from pathlib import Path

import fire
from tqdm import tqdm

from note.libs import csv_exporter, data_fetcher


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def export_data(
    input: str = "note/data/data_j - Sheet1.tsv",
    limit: int | None = None,
    output: str = "note/data/exports/",
    include_etf: bool = False,
) -> None:
    """Export stock data with fundamental indicators to CSV.

    Args:
        input: Path to TSV file containing ticker codes (default: note/data/data_j - Sheet1.tsv)
        limit: Maximum number of stocks to process (default: None for all)
        output: Output directory for CSV files (default: note/data/exports/)
        include_etf: Include ETF/ETN in processing (default: False, individual stocks only)
    """
    logging.info("Starting stock data export process")
    logging.info(f"Input file: {input}")
    logging.info(f"Limit: {limit if limit else 'None (all stocks)'}")
    logging.info(f"Output directory: {output}")
    logging.info(f"Include ETF/ETN: {include_etf}")

    # Validation: Check input file exists
    input_path = Path(input)
    if not input_path.exists():
        logging.error(f"Input file does not exist: {input}")
        sys.exit(1)

    if not input_path.is_file():
        logging.error(f"Input path is not a file: {input}")
        sys.exit(1)

    # Validation: Check limit is positive if provided
    if limit is not None and limit <= 0:
        logging.error(f"Limit must be positive, got: {limit}")
        sys.exit(1)

    # Step 1: Read ticker codes from TSV file
    tickers = csv_exporter.read_tickers_from_tsv(
        tsv_path=input, ticker_column=1, limit=limit, exclude_etf=not include_etf
    )

    if not tickers:
        logging.error("No tickers found. Exiting.")
        sys.exit(1)

    # Step 2: Fetch financial data for each ticker with retry logic
    logging.info(f"Fetching data for {len(tickers)} tickers...")
    ticker_data_list = []

    # Fetch data for each ticker with progress bar
    for ticker in tqdm(tickers, desc="Fetching stock data", unit="stock"):
        data = data_fetcher.fetch_with_retry(ticker, max_retries=3)
        if data:
            # Step 2.5: Fetch earnings history (3 years)
            earnings_data = data_fetcher.fetch_earnings_history(ticker)
            # Merge earnings data into main data dict
            data.update(earnings_data)
            ticker_data_list.append(data)

    logging.info(
        f"Successfully fetched data for {len(ticker_data_list)}/{len(tickers)} tickers"
    )

    if not ticker_data_list:
        logging.error("No data fetched. Exiting.")
        sys.exit(1)

    # Step 3: Build DataFrame from fetched data
    df = csv_exporter.build_dataframe(ticker_data_list)

    # Step 3.5: Merge TSV metadata (stock name, sector, market category)
    df_with_metadata = csv_exporter.merge_tsv_metadata(df, tsv_path=input)

    # Step 4: Calculate and add indicators
    df_with_indicators = csv_exporter.add_indicators_to_dataframe(df_with_metadata)

    # Step 4.5: Add earnings growth flags
    df_with_earnings_flags = csv_exporter.add_earnings_flags(df_with_indicators)

    # Step 4.7: Reorder columns for better readability
    df_final = csv_exporter.reorder_columns(df_with_earnings_flags)

    # Step 5: Export to CSV
    output_path = csv_exporter.export_to_csv(df_final, output_dir=output)

    logging.info(f"Export complete! File saved to: {output_path}")
    print(f"\nExport complete! File saved to: {output_path}")


def main() -> None:
    """Entry point for CLI tool."""
    setup_logging()
    try:
        fire.Fire(export_data)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
