"""Unit tests for the csv_exporter module."""

import re
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest


def test_timestamp_filename_generation(tmp_path: Path) -> None:
    """Test that CSV export generates filename with correct timestamp format."""
    from note.libs.csv_exporter import export_to_csv

    # Create a simple DataFrame
    df = pl.DataFrame(
        {
            "ticker": ["7203"],
            "market_cap": [1000000],
            "net_cash_ratio": [0.15],
        }
    )

    # Export to temporary directory
    output_file = export_to_csv(df, output_dir=str(tmp_path))

    # Verify filename format: stock_data_YYYYMMDD_HHMMSS.csv
    filename = Path(output_file).name
    pattern = r"^stock_data_\d{8}_\d{6}\.csv$"
    assert re.match(pattern, filename), (
        f"Filename '{filename}' should match format stock_data_YYYYMMDD_HHMMSS.csv"
    )

    # Verify timestamp is recent (within last 10 seconds)
    timestamp_str = filename.replace("stock_data_", "").replace(".csv", "")
    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    time_diff = (datetime.now() - timestamp).total_seconds()
    assert time_diff < 10, (
        f"Timestamp should be recent, but was {time_diff:.1f} seconds ago"
    )


def test_csv_column_ordering() -> None:
    """Test that CSV columns are ordered correctly: ticker first, then metadata, then data."""
    from note.libs.csv_exporter import build_dataframe, reorder_columns

    # Create sample data with various columns
    raw_data = [
        {
            "ticker": "7203",
            "market_cap": 1000000,
            "total_cash": 500000,
            "total_debt": 300000,
            "book_value": 700000,
        }
    ]

    # Build DataFrame
    df = build_dataframe(raw_data)

    # Add some indicator columns (simulating add_indicators_to_dataframe)
    df = df.with_columns(
        [
            (
                (pl.col("total_cash") - pl.col("total_debt")) / pl.col("market_cap")
            ).alias("net_cash_ratio"),
            (pl.col("market_cap") / pl.col("book_value")).alias("pbr"),
        ]
    )

    # Reorder columns
    df_ordered = reorder_columns(df)

    # Verify ticker is first
    assert df_ordered.columns[0] == "ticker", "First column should be 'ticker'"

    # Verify ticker appears before other columns
    ticker_index = df_ordered.columns.index("ticker")
    assert ticker_index == 0, "Ticker should be at index 0"


def test_read_tickers_from_tsv_with_limit(tmp_path: Path) -> None:
    """Test that read_tickers_from_tsv respects --limit parameter."""
    from note.libs.csv_exporter import read_tickers_from_tsv

    # Create a temporary TSV file with multiple tickers
    # Use actual column structure: col0(日付等), col1(ticker), col2(name), col3(market), ...
    tsv_file = tmp_path / "tickers.tsv"
    tsv_content = """日付等	銘柄コード	銘柄名	市場・商品区分	33業種コード	33業種区分	17業種コード	17業種区分
dummy	1301	極洋	プライム	3050	水産・農林業	050	食品
dummy	1332	日本水産	プライム	3050	水産・農林業	050	食品
dummy	7203	トヨタ自動車	プライム	5050	輸送用機器	050	自動車・輸送機
dummy	7267	ホンダ	プライム	5050	輸送用機器	050	自動車・輸送機
dummy	9984	ソフトバンクグループ	プライム	7050	情報・通信業	050	情報・通信
"""
    tsv_file.write_text(tsv_content, encoding="utf-8")

    # Test without limit and without ETF filtering (should return all 5)
    tickers_all = read_tickers_from_tsv(
        str(tsv_file), ticker_column=1, limit=None, exclude_etf=False
    )
    assert len(tickers_all) == 5, "Should return all 5 tickers without limit"

    # Test with limit=2 (should return first 2)
    tickers_limited = read_tickers_from_tsv(
        str(tsv_file), ticker_column=1, limit=2, exclude_etf=False
    )
    assert len(tickers_limited) == 2, "Should return exactly 2 tickers with limit=2"
    # Tickers may be integers if polars infers that from the data
    assert str(tickers_limited[0]) == "1301", "First ticker should be 1301"
    assert str(tickers_limited[1]) == "1332", "Second ticker should be 1332"


def test_build_dataframe_from_ticker_data() -> None:
    """Test that build_dataframe constructs a polars DataFrame correctly."""
    from note.libs.csv_exporter import build_dataframe

    # Sample ticker data
    ticker_data_list = [
        {
            "ticker": "7203",
            "market_cap": 30000000000,
            "total_cash": 5000000000,
            "total_debt": 2000000000,
        },
        {
            "ticker": "9984",
            "market_cap": 10000000000,
            "total_cash": 3000000000,
            "total_debt": 8000000000,
        },
    ]

    # Build DataFrame
    df = build_dataframe(ticker_data_list)

    # Verify DataFrame structure
    assert isinstance(df, pl.DataFrame), "Should return a polars DataFrame"
    assert len(df) == 2, "Should have 2 rows"
    assert "ticker" in df.columns, "Should have ticker column"
    assert "market_cap" in df.columns, "Should have market_cap column"

    # Verify data integrity
    assert df["ticker"][0] == "7203", "First ticker should be 7203"
    assert df["ticker"][1] == "9984", "Second ticker should be 9984"


def test_export_to_csv_creates_file(tmp_path: Path) -> None:
    """Test that export_to_csv actually creates a CSV file."""
    from note.libs.csv_exporter import export_to_csv

    # Create a simple DataFrame
    df = pl.DataFrame(
        {
            "ticker": ["7203", "9984"],
            "market_cap": [30000000000, 10000000000],
            "net_cash_ratio": [0.1, -0.5],
        }
    )

    # Export to temporary directory
    output_file = export_to_csv(df, output_dir=str(tmp_path))

    # Verify file was created
    assert Path(output_file).exists(), "CSV file should be created"
    assert Path(output_file).is_file(), "Output should be a file"
    assert Path(output_file).stat().st_size > 0, "CSV file should not be empty"

    # Verify file can be read back
    df_read = pl.read_csv(output_file)
    assert len(df_read) == 2, "Should have 2 rows when read back"
    assert "ticker" in df_read.columns, "Should have ticker column when read back"


def test_filter_individual_stocks() -> None:
    """Test that filter_individual_stocks correctly excludes ETF/ETN."""
    from note.libs.csv_exporter import filter_individual_stocks

    # Create DataFrame with mixed stock types
    # Note: filter_individual_stocks expects market category in column index 3 (4th column)
    df = pl.DataFrame(
        {
            "col0": ["dummy0", "dummy1", "dummy2", "dummy3"],  # Column 0
            "col1": ["dummy0", "dummy1", "dummy2", "dummy3"],  # Column 1
            "col2": ["dummy0", "dummy1", "dummy2", "dummy3"],  # Column 2
            "market_category": [
                "プライム",
                "スタンダード",
                "ETF・ETN",
                "ETF・ETN",
            ],  # Column 3
            "ticker_code": ["1301", "1305", "1320", "1321"],  # Column 4
        }
    )

    # Filter out ETF/ETN
    df_filtered = filter_individual_stocks(df)

    # Verify only individual stocks remain
    assert len(df_filtered) == 2, "Should have 2 individual stocks (exclude 2 ETF/ETN)"
    assert all(df_filtered["market_category"] != "ETF・ETN"), (
        "Should not contain any ETF/ETN"
    )
    assert "1301" in df_filtered["ticker_code"], "Should include 1301"
    assert "1305" in df_filtered["ticker_code"], "Should include 1305"
