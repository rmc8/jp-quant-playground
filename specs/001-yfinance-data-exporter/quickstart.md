# Quickstart: yfinance Data Exporter

**Feature**: 001-yfinance-data-exporter
**Date**: 2025-11-16
**Audience**: クオンツアナリスト、開発者

## Overview

yfinance Data Exporterは、日本株のファンダメンタル指標をyfinance APIから取得し、CSV形式で出力するCLIツールです。このガイドでは、5銘柄のテストから実際の分析までの手順を説明します。

---

## Prerequisites

- Python 3.12以上
- `uv`パッケージマネージャ
- インターネット接続（yfinance API使用のため）

**確認コマンド**:
```bash
python --version  # Python 3.12.x or higher
uv --version      # uv 0.x.x or higher
```

---

## Installation

### 1. リポジトリのセットアップ

```bash
# 依存関係のインストール
uv sync

# 動作確認
uv run python --version
```

### 2. 出力ディレクトリの作成（自動作成されるが、手動でも可）

```bash
mkdir -p note/data/exports
```

---

## Quick Start (5銘柄テスト)

### ステップ1: デフォルト設定で実行

```bash
uv run python note/scripts/export_stock_data.py --limit 5
```

**実行内容**:
- `note/data/data_j - Sheet1.tsv`から先頭5銘柄読み込み
- yfinance APIから財務データ取得（リトライロジック付き）
- ファンダメンタル指標計算
- CSV出力: `note/data/exports/stock_data_YYYYMMDD_HHMMSS.csv`

**所要時間**: 約30秒〜2分（APIレスポンス次第）

---

### ステップ2: 出力CSVの確認

```bash
ls -lh note/data/exports/
```

**出力例**:
```
-rw-r--r--  1 user  staff   15K Nov 16 14:30 stock_data_20251116_143022.csv
```

CSVファイルを開いて内容確認：

```bash
head -n 5 note/data/exports/stock_data_20251116_143022.csv
```

**CSV列の例**:
```
ticker,market_cap,total_cash,total_debt,...,net_cash_ratio,fcf_yield,pbr,...
7203.T,45000000000,3000000000,1000000000,...,0.044,0.05,1.2,...
6758.T,15000000000,2000000000,500000000,...,0.10,0.08,1.5,...
```

---

## Common Use Cases

### ユースケース1: カスタムCSVファイルから銘柄読み込み

```bash
# 自分で用意した銘柄リストCSVを使用
uv run python note/scripts/export_stock_data.py \
  --input /path/to/my_stocks.csv \
  --limit 10
```

**前提**: CSVの2列目に銘柄コード（例: `7203.T`）が含まれること

---

### ユースケース2: 全銘柄処理（limitなし）

```bash
# note/data/data_j - Sheet1.tsvの全銘柄を処理
uv run python note/scripts/export_stock_data.py
```

**注意**: 数百〜数千銘柄の場合、処理時間が長くなります（約1銘柄あたり5-15秒）

---

### ユースケース3: 出力先ディレクトリの変更

```bash
uv run python note/scripts/export_stock_data.py \
  --output /tmp/my_exports/ \
  --limit 5
```

---

## Output Interpretation

### CSVファイルの構造

| 列カテゴリ | 説明 | 例 |
|-----------|------|-----|
| `ticker` | 銘柄コード | `7203.T` |
| **生データ列** | yfinanceから取得した財務データ | `market_cap`, `total_cash`, `operating_cash_flow`, ... |
| **指標列** | 計算されたファンダメンタル指標 | `net_cash_ratio`, `fcf_yield`, `pbr`, `roic`, ... |

### Null値の解釈

- **Null（空文字列）**: yfinanceがデータを提供していない、または計算不可
- **意味**: その銘柄では当該指標が利用できない（データ欠損）

**例**:
```csv
ticker,market_cap,roic,fcf_yield
7203.T,45000000000,,0.05
```
→ 7203.T（トヨタ）はROIC計算に必要なデータ（NOPAT、投下資本）が欠損

---

## Troubleshooting

### 問題1: yfinance API エラー

**症状**:
```
[ERROR] Failed after 3 attempts: 7203.T
```

**原因**: yfinance APIのレート制限、ネットワークエラー

**解決策**:
- 数分待ってから再実行
- `--limit`で銘柄数を減らす（例: `--limit 3`）

---

### 問題2: 入力ファイルが見つからない

**症状**:
```
[ERROR] Input file not found: note/data/data_j - Sheet1.tsv
```

**解決策**:
- ファイルパスを確認（相対パス vs 絶対パス）
- `--input`オプションで正しいパスを指定

---

### 問題3: 出力ディレクトリが書き込み不可

**症状**:
```
[ERROR] Permission denied: note/data/exports/
```

**解決策**:
```bash
chmod 755 note/data/exports/
# または
sudo chown $(whoami) note/data/exports/
```

---

## Next Steps

### 1. データ分析

出力されたCSVをpolarsまたはpandasで読み込み、探索的データ分析を実行：

```python
import polars as pl

df = pl.read_csv("note/data/exports/stock_data_20251116_143022.csv")

# ネットキャッシュ比率の分布確認
print(df.select("ticker", "net_cash_ratio").sort("net_cash_ratio", descending=True))

# FCF利回り上位銘柄
print(df.filter(pl.col("fcf_yield").is_not_null()).sort("fcf_yield", descending=True).head(10))
```

---

### 2. marimoノートブックで可視化

既存の`note/ncav_analysis.py`を参考に、独自の分析ノートブックを作成：

```bash
uv run marimo edit note/my_analysis.py
```

---

### 3. バックテスト

取得したデータを使って、ファンダメンタル指標ベースのバックテストを実行（次フェーズ）

---

## Example Workflow

```bash
# 1. 5銘柄テスト
uv run python note/scripts/export_stock_data.py --limit 5

# 2. 出力確認
head -n 10 note/data/exports/stock_data_*.csv

# 3. 分析（Python REPL）
uv run python
>>> import polars as pl
>>> df = pl.read_csv("note/data/exports/stock_data_20251116_143022.csv")
>>> df.describe()

# 4. 本番実行（全銘柄）
uv run python note/scripts/export_stock_data.py
```

---

## Performance Tips

- **並列処理**: 現在未対応（将来的に`asyncio`導入を検討）
- **キャッシング**: yfinanceは内部でキャッシュを使用（同日再実行は高速）
- **バッチサイズ**: `--limit`で処理を分割し、段階的に実行

---

## Constitution Compliance

このツールは以下のConstitution原則に準拠しています：

- ✅ **Data Quality**: エラーハンドリング、null明示処理
- ✅ **Reproducibility**: タイムスタンプ付きファイル名、パラメータ明記
- ✅ **Performance**: polars使用、既存ライブラリ再利用
- ✅ **Maintainability**: 型ヒント、Ruff準拠、モジュール化

---

## Support

問題が発生した場合は、エラーログを確認し、上記Troubleshootingセクションを参照してください。
