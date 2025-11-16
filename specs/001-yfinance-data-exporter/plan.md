# Implementation Plan: yfinance Data Exporter

**Branch**: `001-yfinance-data-exporter` | **Date**: 2025-11-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-yfinance-data-exporter/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

CLIツールとして、TSV/CSVファイルから銘柄コードを読み込み、yfinance APIを経由して財務データを取得し、ファンダメンタル指標を計算してCSV出力する。既存の`note/libs/indicators.py`を活用し、Constitution原則（Data Quality、Reproducibility、Performance、Maintainability）に準拠した設計。

**主要機能**:
- TSVファイル（デフォルト: `note/data/data_j - Sheet1.tsv`の2列目）から銘柄コード読み込み
- yfinance APIからの財務データ取得（リトライロジック: 最大3回、指数バックオフ）
- 11種類のファンダメンタル指標計算（既存ライブラリ活用）
- 生データ+指標をCSV出力（ファイル名: `stock_data_YYYYMMDD_HHMMSS.csv`）
- `--limit N`オプションによる銘柄数制限（デフォルト: 全銘柄）

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: polars (>=1.35.2), yfinance (>=0.2.66), 既存の`note/libs/indicators.py`
**Storage**: CSV出力（デフォルトディレクトリ: `note/data/exports/`）
**Testing**: pytest（Type hints必須、Ruff準拠）
**Target Platform**: macOS/Linux（CLI tool）
**Project Type**: Single CLI application
**Performance Goals**: 5銘柄を2分以内に処理（SC-001）、銘柄数に応じてスケール
**Constraints**: yfinance APIレート制限対応（リトライロジック）、polars使用必須、型ヒント必須
**Scale/Scope**: 初期5銘柄テスト、将来的に数百〜数千銘柄対応

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**jp-quant-playground Constitution Compliance (v1.0.0)**

- [x] **I. Data Quality**: ✅ yfinanceデータのエラーハンドリング実装（FR-005）、polarsスキーマ検証、null明示処理
- [x] **II. Reproducibility**: ✅ タイムスタンプ付きファイル名（FR-004）、パラメータ明記（`--limit`オプション）
- [x] **III. Transparency**: ⚠️ N/A（CLIツールのためmarimo変数命名は不適用、ただし関数名は明確に）
- [x] **IV. Performance**: ✅ polars使用（Technical Context明記）、既存`note/libs/indicators.py`活用
- [x] **V. Maintainability**: ✅ 型ヒント必須（Technical Context）、Ruff準拠、既存指標ライブラリ再利用

**Violations requiring justification**: なし（原則IIIはmarimoノートブック専用のため、CLIツールでは適用外）

## Project Structure

### Documentation (this feature)

```text
specs/001-yfinance-data-exporter/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli-interface.md # CLI引数仕様
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
note/
├── libs/
│   ├── __init__.py           # 既存
│   ├── indicators.py         # 既存（再利用）
│   ├── data_fetcher.py       # 新規：yfinanceデータ取得ロジック
│   └── csv_exporter.py       # 新規：CSV出力ロジック
├── data/
│   ├── data_j - Sheet1.tsv   # 既存（入力データ）
│   └── exports/              # 新規：CSV出力先ディレクトリ
└── scripts/
    └── export_stock_data.py  # 新規：CLIエントリポイント

tests/
└── note/
    ├── test_data_fetcher.py  # 新規
    ├── test_csv_exporter.py  # 新規
    └── test_cli_integration.py # 新規
```

**Structure Decision**: 既存の`note/`ディレクトリ構造を拡張。`note/libs/`に新規モジュール追加、`note/scripts/`に実行可能CLIスクリプト配置。Constitution原則Vに従い、ビジネスロジックをライブラリ化（`data_fetcher.py`, `csv_exporter.py`）し、CLIは薄いラッパーとする。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

該当なし（全原則準拠）
