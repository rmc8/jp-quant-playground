# Data Model: yfinance Data Exporter

**Feature**: 001-yfinance-data-exporter
**Date**: 2025-11-16
**Input**: spec.md, research.md

## Overview

yfinance Data Exporterのデータフローとエンティティ定義。データは3段階で変換される：
1. **Input**: TSV/CSVファイル（銘柄コードリスト）
2. **Intermediate**: yfinance API レスポンス（財務データ）
3. **Output**: 統合CSV（生データ + 計算済み指標）

---

## Entities

### 1. StockTicker（入力エンティティ）

**Purpose**: TSVファイルから読み込まれる銘柄識別子

**Attributes**:
| Field | Type | Description | Validation | Example |
|-------|------|-------------|------------|---------|
| `ticker_code` | `str` | 銘柄コード（日本株は`.T`サフィックス） | 非空文字列、`.T`で終わる | `"7203.T"` |

**Source**: `note/data/data_j - Sheet1.tsv`の2列目（インデックス1）

**Lifecycle**:
1. TSVファイル読み込み
2. `--limit N`オプションによるフィルタ（先頭N件）
3. yfinance APIリクエストの入力として使用

---

### 2. RawFinancialData（中間エンティティ）

**Purpose**: yfinance APIから取得した生の財務データ（1銘柄分）

**Attributes**:
| Field | Type | Description | Nullable | Source |
|-------|------|-------------|----------|--------|
| `ticker` | `str` | 銘柄コード | No | リクエスト元 |
| `market_cap` | `Optional[float]` | 時価総額 | Yes | `stock.info["marketCap"]` |
| `total_cash` | `Optional[float]` | 現金及び現金等価物 | Yes | `balance_sheet.loc["Cash And Cash Equivalents"]` |
| `total_debt` | `Optional[float]` | 有利子負債 | Yes | `balance_sheet.loc["Total Debt"]` |
| `total_assets` | `Optional[float]` | 総資産 | Yes | `balance_sheet.loc["Total Assets"]` |
| `book_value` | `Optional[float]` | 株主資本 | Yes | `balance_sheet.loc["Stockholders Equity"]` |
| `operating_cash_flow` | `Optional[float]` | 営業キャッシュフロー | Yes | `cashflow.loc["Operating Cash Flow"]` |
| `capex` | `Optional[float]` | 設備投資額（負値） | Yes | `cashflow.loc["Capital Expenditure"]` |
| `ebit` | `Optional[float]` | 営業利益（EBIT） | Yes | `financials.loc["EBIT"]` |
| `gross_profit` | `Optional[float]` | 売上総利益 | Yes | `financials.loc["Gross Profit"]` |
| `net_income` | `Optional[float]` | 純利益 | Yes | `financials.loc["Net Income"]` |

**Validation Rules**:
- 全フィールドがnullの場合、データ取得失敗と判断
- 数値フィールドは`float`型（polarsの`Float64`にマッピング）
- nullはpolarsの`null`として明示的に扱う（Constitution原則I）

**State Transitions**:
1. **Fetching**: yfinance APIリクエスト中
2. **Success**: データ取得成功（少なくとも1フィールド非null）
3. **Partial**: 一部フィールドのみ取得成功
4. **Failed**: 全フィールドnull（リトライ3回後も取得失敗）

---

### 3. CalculatedIndicators（出力エンティティ - 一部）

**Purpose**: 計算されたファンダメンタル指標（1銘柄分）

**Attributes**:
| Field | Type | Description | Calculation | Nullable |
|-------|------|-------------|-------------|----------|
| `net_cash_ratio` | `Optional[float]` | ネットキャッシュ比率 | `(total_cash - total_debt) / market_cap` | Yes |
| `enterprise_value` | `Optional[float]` | 企業価値（EV） | `market_cap + (total_debt - total_cash)` | Yes |
| `roic` | `Optional[float]` | ROIC | `nopat / invested_capital`（データ不足で計算不可の場合あり） | Yes |
| `fcf_yield` | `Optional[float]` | FCF利回り | `(operating_cash_flow - capex) / market_cap` | Yes |
| `pbr` | `Optional[float]` | PBR | `market_cap / book_value` | Yes |
| `ev_ebit` | `Optional[float]` | EV/EBIT | `enterprise_value / ebit` | Yes |
| `gross_profitability` | `Optional[float]` | Gross Profitability | `gross_profit / total_assets` | Yes |

**Calculation Dependencies**:
- `note/libs/indicators.py`の既存関数を使用
- 計算に必要なフィールドがnullの場合、指標もnullとする
- ゼロ除算は事前チェックでnull化

**Validation Rules**:
- 指標値は`-∞`〜`+∞`の範囲（異常値検出は次フェーズ）
- 計算エラーは警告ログ出力 + null化

---

### 4. ExportRow（最終出力エンティティ）

**Purpose**: CSV出力の1行（1銘柄分の完全データ）

**Schema**:
```
ticker, market_cap, total_cash, total_debt, ..., net_cash_ratio, enterprise_value, ..., fcf_yield, pbr
```

**Structure**: `RawFinancialData` + `CalculatedIndicators`の結合

**Column Order**:
1. `ticker`（銘柄コード）
2. 生データフィールド（アルファベット順）
3. 計算済み指標フィールド（アルファベット順）

**Output Format**:
- ファイル名: `stock_data_YYYYMMDD_HHMMSS.csv`
- エンコーディング: UTF-8（BOMなし）
- 区切り文字: カンマ（`,`）
- ヘッダー行: あり
- Null表現: 空文字列（CSVデフォルト）

---

## Data Flow Diagram

```text
┌─────────────────────┐
│ TSV File            │
│ (data_j -.tsv)      │
│ Column 2: ticker    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Filter (--limit N)  │
│ → List[StockTicker] │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ yfinance API        │
│ (with retry)        │
│ → RawFinancialData  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ indicators.py       │
│ → CalculatedIndicat-│
│   ors               │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Combine             │
│ → ExportRow         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ CSV File            │
│ stock_data_*.csv    │
└─────────────────────┘
```

---

## Relationships

- **1 TSV File** → **N StockTickers** （1:N）
- **1 StockTicker** → **1 RawFinancialData** （1:1）
- **1 RawFinancialData** → **1 CalculatedIndicators** （1:1）
- **1 (RawFinancialData + CalculatedIndicators)** → **1 ExportRow** （1:1）
- **N ExportRows** → **1 CSV File** （N:1）

---

## Error Handling Strategy

| Error Scenario | Handling | Data Model Impact |
|----------------|----------|-------------------|
| yfinance API失敗（リトライ3回後） | `RawFinancialData`の全フィールドnull | `CalculatedIndicators`も全null |
| 一部フィールドのみ取得失敗 | 該当フィールドnull、他は正常値 | 依存する指標のみnull |
| 指標計算エラー（ゼロ除算など） | 警告ログ + 該当指標null | `ExportRow`に影響するが、他指標は計算 |
| TSVファイル読み込み失敗 | プログラム終了（CRITICAL ERROR） | データフローが開始されない |

---

## Performance Considerations

- **Lazy Evaluation**: 今回は使用しない（銘柄数が限定的、5-数百程度）
- **Batch Processing**: yfinance APIは銘柄ごとに順次処理（並列化は将来検討）
- **Memory**: polarsの効率的なメモリ管理により、数千銘柄でも問題なし

---

## Constitution Compliance

- **I. Data Quality**: ✅ null明示、polarsスキーマ検証
- **II. Reproducibility**: ✅ タイムスタンプ記録（ファイル名）
- **IV. Performance**: ✅ polars使用
- **V. Maintainability**: ✅ 型ヒント（全エンティティ）、既存ライブラリ再利用
