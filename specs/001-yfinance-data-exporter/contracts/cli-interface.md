# CLI Interface Contract: yfinance Data Exporter

**Feature**: 001-yfinance-data-exporter
**Date**: 2025-11-16
**Version**: 1.0.0

## Overview

CLIツール`export_stock_data.py`のインターフェース仕様。

---

## Command Signature

```bash
python note/scripts/export_stock_data.py [OPTIONS]
```

または`uv run`経由：

```bash
uv run python note/scripts/export_stock_data.py [OPTIONS]
```

---

## Options

### `--input` (optional)

**Type**: `str`
**Default**: `"note/data/data_j - Sheet1.tsv"`
**Description**: 銘柄コードを含むTSV/CSVファイルのパス（2列目を読み込み）
**Example**:
```bash
python note/scripts/export_stock_data.py --input my_stocks.csv
```

**Validation**:
- ファイルが存在しない場合: エラー終了（exit code 1）
- ファイルが読み込み不可: エラー終了（exit code 1）

---

### `--limit` (optional)

**Type**: `int`
**Default**: `None`（全銘柄処理）
**Description**: 処理する銘柄数の上限（先頭N件）
**Example**:
```bash
python note/scripts/export_stock_data.py --limit 5
```

**Validation**:
- 負の値: エラー終了（exit code 1）
- ゼロ: エラー終了（exit code 1）
- TSVファイルの行数より大きい値: 全銘柄処理（警告ログ出力）

---

### `--output` (optional)

**Type**: `str`
**Default**: `"note/data/exports/"`
**Description**: CSV出力先ディレクトリ
**Example**:
```bash
python note/scripts/export_stock_data.py --output /tmp/stock_exports/
```

**Validation**:
- ディレクトリが存在しない場合: 自動作成
- 書き込み権限がない場合: エラー終了（exit code 1）

---

### `--help`, `-h` (optional)

**Description**: ヘルプメッセージを表示して終了
**Example**:
```bash
python note/scripts/export_stock_data.py --help
```

**Output**:
```
usage: export_stock_data.py [-h] [--input INPUT] [--limit LIMIT] [--output OUTPUT]

Export stock data from yfinance to CSV

optional arguments:
  -h, --help       show this help message and exit
  --input INPUT    Input TSV/CSV file path (default: note/data/data_j - Sheet1.tsv)
  --limit LIMIT    Limit number of stocks to process (default: all)
  --output OUTPUT  Output directory for CSV (default: note/data/exports/)
```

---

## Exit Codes

| Code | Meaning | Example Scenario |
|------|---------|------------------|
| 0    | Success | データ取得・出力が全て成功 |
| 1    | Error   | 入力ファイル不正、出力ディレクトリ書き込み不可、引数バリデーション失敗 |

---

## Output

### Success Case

**stdout**:
```
[INFO] Reading tickers from: note/data/data_j - Sheet1.tsv
[INFO] Processing 5 stocks (--limit 5)
[INFO] Fetching data for 7203.T...
[INFO] Fetching data for 6758.T...
[INFO] Fetching data for 9984.T...
[INFO] Fetching data for 6861.T...
[INFO] Fetching data for 8306.T...
[INFO] Successfully processed 5/5 stocks
[INFO] CSV exported to: note/data/exports/stock_data_20251116_143022.csv
```

**Generated File**: `note/data/exports/stock_data_20251116_143022.csv`

---

### Partial Failure Case

**stdout**:
```
[INFO] Reading tickers from: note/data/data_j - Sheet1.tsv
[INFO] Processing 3 stocks
[INFO] Fetching data for 7203.T...
[WARNING] Retry 1/3 for 6758.T after 1s
[WARNING] Retry 2/3 for 6758.T after 2s
[ERROR] Failed after 3 attempts: 6758.T
[INFO] Fetching data for 9984.T...
[INFO] Successfully processed 2/3 stocks
[WARNING] 1 stock(s) failed to fetch
[INFO] CSV exported to: note/data/exports/stock_data_20251116_143100.csv
```

**Notes**:
- 失敗した銘柄もCSVに含まれる（全フィールドがnull）
- エラーログには失敗理由が記録される

---

### Error Case (Invalid Input)

**stderr**:
```
[ERROR] Input file not found: invalid_file.csv
```

**Exit Code**: 1

---

## Logging

### Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| INFO  | 正常な処理フロー | "Fetching data for 7203.T..." |
| WARNING | 一時的なエラー（リトライ可能） | "Retry 1/3 for 6758.T after 1s" |
| ERROR | 回復不能なエラー | "Failed after 3 attempts: 6758.T" |
| CRITICAL | プログラム終了レベルのエラー | "Input file not found" |

### Log Format

```
[LEVEL] Message
```

**Example**:
```
[INFO] Reading tickers from: note/data/data_j - Sheet1.tsv
[WARNING] Retry 1/3 for 6758.T after 1s
[ERROR] Failed after 3 attempts: 6758.T
```

---

## Examples

### Example 1: Default Usage (Process All Stocks)

```bash
python note/scripts/export_stock_data.py
```

**Result**: `note/data/data_j - Sheet1.tsv`から全銘柄処理、CSV出力先は`note/data/exports/`

---

### Example 2: Test with 5 Stocks

```bash
python note/scripts/export_stock_data.py --limit 5
```

**Result**: 先頭5銘柄のみ処理

---

### Example 3: Custom Input and Output

```bash
python note/scripts/export_stock_data.py \
  --input /path/to/my_stocks.csv \
  --output /tmp/exports/ \
  --limit 10
```

**Result**: カスタムCSVから10銘柄処理、`/tmp/exports/`に出力

---

## Contract Validation

### Pre-Conditions

- Python 3.12以上がインストール済み
- `uv`パッケージマネージャが利用可能
- 依存ライブラリ（polars、yfinance）がインストール済み（`uv sync`実行済み）

### Post-Conditions

- 成功時: CSV出力ファイルが指定ディレクトリに存在
- 失敗時: エラーログが標準エラー出力に記録され、exit code 1で終了

### Invariants

- CSVファイル名は常に`stock_data_YYYYMMDD_HHMMSS.csv`形式
- CSVヘッダー行は必ず存在
- `ticker`列は必ず最初の列

---

## Version History

| Version | Date       | Changes |
|---------|------------|---------|
| 1.0.0   | 2025-11-16 | 初版リリース |
