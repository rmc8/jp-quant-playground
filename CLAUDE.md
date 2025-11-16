# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

日本株のクオンツ戦略を実験するためのプレイグラウンド。ファンダメンタル指標を組み合わせて、市場を超えるリターンを目指すバックテスト環境。

主な分析対象指標（`note/indicators.md`参照）：
- 安全性：ネットキャッシュ比率
- 資本効率：ROIC、CROIC、Gross Profitability
- 割安度：EV/EBIT、FCF利回り
- 財務改善：Piotroski Fスコア
- 株主還元：Shareholder Yield
- 伝統的指標：PBR、EV/FCF

## 開発環境

**Python**: 3.12以上必須

**パッケージマネージャー**: `uv`を使用

**主要依存関係**:
- `marimo`: ノートブック環境（Jupyter代替）
- `polars`: データフレーム処理（pandas代替、高速）
- `yfinance`: 株価データ取得
- `plotly`: インタラクティブな可視化

## よく使うコマンド

### 環境セットアップ
```bash
# 依存関係のインストール
uv sync

# 開発用依存関係含むインストール
uv sync --group dev
```

### コード品質
```bash
# リンター実行（Ruff）
uv run ruff check .

# フォーマット実行（Ruff）
uv run ruff format .

# インポート整理（isort）
uv run isort .
```

### ノートブック実行
```bash
# marimoノートブックを起動（該当ファイルがある場合）
uv run marimo edit notebook.py
```

### データエクスポート
```bash
# 個別銘柄のみ5銘柄テスト（デフォルト：ETF・ETN除外）
uv run python -m note.scripts.export_stock_data --limit 5

# ETF・ETNも含めて処理
uv run python -m note.scripts.export_stock_data --limit 5 --include-etf

# 全個別銘柄処理（約4,000銘柄）
uv run python -m note.scripts.export_stock_data

# カスタム入力・出力パス指定
uv run python -m note.scripts.export_stock_data --input path/to/file.tsv --output path/to/output/
```

## アーキテクチャ

### データ処理の方針
- **Polars優先**: pandasではなくpolarsを使用する（高速、メモリ効率）
- **キャッシュフロー重視**: 会計利益よりもキャッシュフローベースの指標を優先
- **マルチファクター**: 単一指標ではなく、Value/Quality/Safety/Momentumの組み合わせで戦略構築

### ファンダメンタル指標の計算
指標計算時の注意点（`note/indicators.md`の戦略に基づく）:
- EV（企業価値）= 時価総額 + 純有利子負債（= 有利子負債 - 現金等価物）
- ROIC = NOPAT / 投下資本（運転資本を含む）
- FCF = 営業CF - CAPEX
- Shareholder Yield = 配当利回り + 自社株買い純額利回り + 負債削減利回り

### データソース
- `yfinance`で日本株データ取得（ティッカーは`.T`サフィックス、例：`7203.T`はトヨタ）
- 財務データの利用可能性に注意：yfinanceは全ての指標を提供しないため、計算可能な指標を優先
- **TSV入力ファイル構造**（`note/data/data_j - Sheet1.tsv`）:
  - 列2（インデックス1）: 銘柄コード
  - 列3（インデックス2）: 銘柄名
  - 列4（インデックス3）: 市場・商品区分（「ETF・ETN」でフィルタリング）
  - 列6（インデックス5）: 33業種区分
  - 列8（インデックス7）: 17業種区分
  - 総銘柄数: 4,416（個別銘柄4,012 + ETF・ETN 404）
- **yfinance earnings API**: 非推奨だが一時的に利用可能（`Ticker.earnings`）。将来的には`Ticker.income_stmt`へ移行予定

## コーディング規約

### スタイル
- Ruffでリント・フォーマット
- isortでインポート整理
- 型ヒントを積極的に使用（Python 3.12の機能活用）

### ファイル構成
- `note/`: ノート・ドキュメント・分析用コード
- `note/libs/`: 共通ライブラリ・ユーティリティ関数
  - `indicators.py`: ファンダメンタル指標計算関数（11指標）
  - `data_fetcher.py`: yfinance API データ取得（リトライロジック付き）
  - `csv_exporter.py`: TSV読み込み、DataFrame構築、CSV出力
- `note/scripts/`: CLIツール
  - `export_stock_data.py`: 株式データエクスポートツール（python-fire使用）
- `note/data/`: データファイル
  - `exports/`: CSV出力先ディレクトリ

### データ分析時の推奨事項
- marimoでインタラクティブな分析環境を構築
- plotlyで可視化（静的グラフよりインタラクティブを優先）
- バックテストは再現性を重視（シード値の固定、パラメータの明記）

## Active Technologies
- **yfinanceデータエクスポーター**: 割安株・高配当株スクリーニング向けCSV出力ツール
  - **実装ファイル**: `note/libs/data_fetcher.py`, `note/libs/csv_exporter.py`, `note/scripts/export_stock_data.py`
  - **主要機能**:
    - ETF・ETNフィルタリング（デフォルトで個別銘柄のみ、`--include-etf`で全銘柄）
    - TSVメタデータ統合（銘柄名、市場区分、業種33/17）
    - 日本株対応（数値コードに自動で`.T`サフィックス追加）
    - 指数バックオフリトライ（1秒→2秒→4秒、最大3回）
  - **出力指標**（32列）:
    - **メタデータ**: ticker, stock_name, market_category, sector_33, sector_17
    - **配当指標**: dividend_yield（配当利回り）, payout_ratio（配当性向）
    - **利益データ**: earnings_y0/y1/y2（3年分）, consecutive_earnings_growth（連続増益フラグ）
    - **バリュエーション**: trailing_pe（PER）, psr（PSR）, peg_ratio（PEG Ratio）
    - **財務データ**: market_cap, total_cash, total_debt, total_assets, book_value, operating_cash_flow, capex, ebit, gross_profit, net_income, total_revenue, earnings_growth
    - **計算指標**: net_cash_ratio, enterprise_value, gross_profitability, fcf_yield, pbr, ev_ebit, ev_fcf
  - **CLI**: `uv run python -m note.scripts.export_stock_data [--limit N] [--include-etf] [--input PATH] [--output PATH]`
- **依存関係**: Python 3.12, polars (>=1.35.2), yfinance (>=0.2.66), fire (>=0.7.1), pytest (>=8.0.0)

## Recent Changes
- **2025-11-16**: 割安株・高配当株投資向けデータエクスポーター完成
  - **新規ファイル**: `data_fetcher.py`, `csv_exporter.py`, `export_stock_data.py`
  - **実装機能**:
    - ETF・ETNフィルタリング（デフォルトで個別銘柄のみ、`--include-etf`で全銘柄処理）
    - TSVメタデータ統合（銘柄名、市場区分、33業種区分、17業種区分）
    - 配当指標: 配当利回り、配当性向
    - 利益データ: 当年・前年・前々年の純利益、3年連続増益フラグ
    - バリュエーション指標: PER（株価収益率）、PSR（株価売上高倍率）、PEG Ratio
    - ファンダメンタル指標: ネットキャッシュ比率、EV、Gross Profitability、EV/EBIT、FCF利回り、PBR、EV/FCF
    - 列順序最適化: ticker → メタデータ → 配当 → 利益 → バリュエーション → 財務データ → 計算指標
  - **出力形式**: CSV 32列、タイムスタンプ付きファイル名
  - **テスト結果**: 10銘柄処理（4/10銘柄成功、無効ティッカー自動除外）
  - **統計分析**: TSVファイル全4,416銘柄（個別銘柄4,012 + ETF・ETN 404）を分析し、市場区分フィールドで100%正確にフィルタリング可能と確認
