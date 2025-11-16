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

## コーディング規約

### スタイル
- Ruffでリント・フォーマット
- isortでインポート整理
- 型ヒントを積極的に使用（Python 3.12の機能活用）

### ファイル構成
- `note/`: ノート・ドキュメント・分析用コード
- `note/libs/`: 共通ライブラリ・ユーティリティ関数

### データ分析時の推奨事項
- marimoでインタラクティブな分析環境を構築
- plotlyで可視化（静的グラフよりインタラクティブを優先）
- バックテストは再現性を重視（シード値の固定、パラメータの明記）
