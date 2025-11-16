# Research: yfinance Data Exporter

**Feature**: 001-yfinance-data-exporter
**Date**: 2025-11-16
**Status**: Complete

## Overview

本フィーチャーはyfinance APIを使用したデータ取得CLIツールのため、以下の技術領域を調査：
1. yfinance APIのベストプラクティスとレート制限対策
2. polarsでのCSV I/O最適化
3. CLI引数パーシング（Python標準ライブラリ）
4. リトライロジックの実装パターン

## 調査項目

### 1. yfinance APIのベストプラクティス

**Decision**: `yfinance.Ticker`クラスを使用し、財務データは`.info`、`.financials`、`.balance_sheet`、`.cashflow`プロパティから取得

**Rationale**:
- yfinanceは非公式APIのため、レート制限やデータ欠損が頻繁に発生
- エラーハンドリングとリトライロジックが必須
- Constitution原則I（Data Quality）に従い、取得失敗時はnullを明示的に記録

**Key Findings**:
- yfinanceは日本株（`.T`サフィックス）に対応
- 財務データの会計期は最新のみ取得（`iloc[0]`）
- データ項目の有無はティッカーごとに異なるため、`try-except`または`.get()`メソッドで安全にアクセス

**Alternatives Considered**:
- pandas_datareader: yfinanceより古く、日本株サポートが不完全
- 有料API（Bloomberg、Refinitiv）: コスト高、個人プロジェクトには不適

**Implementation Pattern**:
```python
import yfinance as yf
from typing import Optional

def fetch_ticker_data(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        balance_sheet = stock.balance_sheet

        return {
            "market_cap": info.get("marketCap"),
            "total_cash": balance_sheet.loc["Cash And Cash Equivalents"].iloc[0]
                         if "Cash And Cash Equivalents" in balance_sheet.index else None,
            # ...
        }
    except Exception as e:
        logging.error(f"Failed to fetch {ticker}: {e}")
        return {}  # Empty dict signals failure
```

---

### 2. Polarsでのファイル I/O最適化

**Decision**: `polars.read_csv()`でTSV読み込み、`polars.DataFrame.write_csv()`で出力

**Rationale**:
- polarsはpandasより高速（特に大規模データセット）
- Constitution原則IV（Performance）に準拠
- スキーマ検証機能により、データ型の整合性を早期に検出

**Key Findings**:
- TSV読み込み: `separator="\t"`オプション必須
- CSV出力: デフォルトでUTF-8、BOMなし（Excel互換性のためBOM追加も検討可能）
- `lazy=True`での遅延評価は今回不要（銘柄数が限定的）

**Implementation Pattern**:
```python
import polars as pl

# TSV読み込み（2列目=銘柄コード）
df = pl.read_csv("note/data/data_j - Sheet1.tsv", separator="\t")
tickers = df.select(pl.col(df.columns[1])).to_series().to_list()

# CSV出力
output_df.write_csv("note/data/exports/stock_data_20251116_120000.csv")
```

**Alternatives Considered**:
- pandas: 遅い、Constitution違反
- csvモジュール（標準ライブラリ）: 低レベルすぎる、polarsの方が安全

---

### 3. CLI引数パーシング

**Decision**: `argparse`（Python標準ライブラリ）を使用

**Rationale**:
- 標準ライブラリのため追加依存なし
- `--limit`、`--input`、`--output`などのオプション引数に対応
- ヘルプメッセージ自動生成

**Key Findings**:
- `argparse.ArgumentParser(description="...")`でCLI説明を記述
- `type=int`で型変換、`default=None`でデフォルト値設定
- `required=False`で任意オプション

**Implementation Pattern**:
```python
import argparse

parser = argparse.ArgumentParser(description="Export stock data from yfinance to CSV")
parser.add_argument("--input", type=str, default="note/data/data_j - Sheet1.tsv",
                    help="Input TSV/CSV file path (default: note/data/data_j - Sheet1.tsv)")
parser.add_argument("--limit", type=int, default=None,
                    help="Limit number of stocks to process (default: all)")
parser.add_argument("--output", type=str, default="note/data/exports/",
                    help="Output directory for CSV (default: note/data/exports/)")

args = parser.parse_args()
```

**Alternatives Considered**:
- click: 高機能だが依存追加が必要
- typer: モダンだが依存追加が必要、Python 3.12との互換性確認が必要
- **python-fire**: 関数を自動的にCLIに変換、シンプルで強力。依存追加が必要だが、`argparse`よりボイラープレートが少ない。検討の価値あり（実装時に選択）

---

### 4. リトライロジックの実装

**Decision**: 指数バックオフ（1秒、2秒、4秒）で最大3回リトライ、`time.sleep()`使用

**Rationale**:
- yfinance APIのレート制限・一時的障害に対応
- 仕様書（Clarifications）で明確化済み
- シンプルな実装で十分（サードパーティライブラリ不要）

**Key Findings**:
- 指数バックオフ: `2^attempt`秒待機（1秒、2秒、4秒）
- リトライ対象: ネットワークエラー、タイムアウト、HTTPステータス429（Too Many Requests）
- リトライ非対象: 銘柄コード不正（404 Not Found）

**Implementation Pattern**:
```python
import time
from typing import Optional

def fetch_with_retry(ticker: str, max_retries: int = 3) -> Optional[dict]:
    for attempt in range(max_retries):
        try:
            return fetch_ticker_data(ticker)
        except (ConnectionError, TimeoutError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1, 2, 4 seconds
                logging.warning(f"Retry {attempt+1}/{max_retries} for {ticker} after {wait_time}s")
                time.sleep(wait_time)
            else:
                logging.error(f"Failed after {max_retries} attempts: {ticker}")
                return None
```

**Alternatives Considered**:
- `tenacity`ライブラリ: 高機能だが依存追加、今回の単純ケースではオーバーエンジニアリング
- `requests.adapters.Retry`: yfinanceは内部でrequestsを使うが、外部から制御不可

---

## Constitution準拠確認

- **I. Data Quality**: ✅ エラーハンドリング、null明示、polarsスキーマ検証
- **II. Reproducibility**: ✅ タイムスタンプ記録、パラメータ明記
- **III. Transparency**: N/A（CLIツール）
- **IV. Performance**: ✅ polars使用、遅延評価検討（今回不要と判断）
- **V. Maintainability**: ✅ 型ヒント、標準ライブラリ優先、既存ライブラリ再利用

---

## 未解決項目

なし（全ての技術選択完了）

---

## 次ステップ

Phase 1: データモデル設計（data-model.md）、CLI契約（contracts/cli-interface.md）、クイックスタート（quickstart.md）の生成
