# Feature Specification: yfinance Data Exporter

**Feature Branch**: `001-yfinance-data-exporter`
**Created**: 2025-11-16
**Status**: Draft
**Input**: User description: "yfinanceから各指標の計算に必要な値を取れるようなものを作りたいです。指標を表示するとともに、計算の元となった個別の値も記録した列も設けて指標とともに分析や機械学習による解釈、バックテストで重要なものをすべて値に含めてcsvに出力したいです。まずは5銘柄でテストをすると良いかと思います。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Data Export (Priority: P1)

クオンツアナリストが、指定した銘柄の財務データとファンダメンタル指標を一度に取得し、CSV形式で保存できる。

**Why this priority**: データ取得と保存は全ての分析の基盤であり、最も基本的な機能。これがなければ後続の分析ができない。

**Independent Test**: 銘柄コードのリストを入力として与え、CSV出力を確認することで完全にテスト可能。出力CSVに期待される列（生データ+指標）が全て含まれていることを検証できる。

**Acceptance Scenarios**:

1. **Given** 銘柄コードリスト（例：`note/data/data_j - Sheet1.tsv`から`--limit 5`で5銘柄抽出）, **When** データエクスポートを実行, **Then** 指定銘柄分の財務データと計算済み指標を含むCSVファイルが生成される
2. **Given** yfinanceから取得可能な銘柄コード, **When** データエクスポートを実行, **Then** 各銘柄について、時価総額、総資産、現金、負債、営業CF、CAPEXなどの基礎データが取得される
3. **Given** 取得した基礎データ, **When** 指標計算を実行, **Then** ネットキャッシュ比率、ROIC、FCF利回り、PBRなどの指標が計算され、CSVに含まれる

---

### User Story 2 - Detailed Data Provenance (Priority: P2)

クオンツアナリストが、計算された指標だけでなく、その計算の元となった個別の値（例：EV = 時価総額 + 純有利子負債）も同じCSVに記録できる。

**Why this priority**: 指標の内訳を保持することで、異常値の原因分析や機械学習における特徴量エンジニアリングが可能になる。P1の基本機能の上に成り立つ価値追加機能。

**Independent Test**: CSV出力に、指標列（例：`net_cash_ratio`）だけでなく、その計算要素列（`total_cash`, `total_debt`, `market_cap`）も含まれていることを確認できる。

**Acceptance Scenarios**:

1. **Given** 計算された指標（例：ネットキャッシュ比率）, **When** CSV出力を確認, **Then** 指標列に加えて、計算元の列（`total_cash`, `total_debt`, `market_cap`）も含まれている
2. **Given** 出力されたCSVデータ, **When** 手動で指標を再計算, **Then** CSV内の指標列と手動計算結果が一致する（データの整合性が保証される）

---

### User Story 3 - Error Handling and Data Validation (Priority: P3)

クオンツアナリストが、yfinanceからデータ取得に失敗した場合や、計算不可能な指標がある場合でも、エラー内容を把握し、取得できたデータは保存できる。

**Why this priority**: yfinanceは全ての銘柄・全ての項目のデータを提供するわけではないため、部分的な失敗に対処できる必要がある。P1/P2の機能を補完し、実用性を高める。

**Independent Test**: 意図的にデータ不足の銘柄を含めて実行し、エラーログと出力CSVの両方を検証できる。

**Acceptance Scenarios**:

1. **Given** yfinanceがデータを提供しない銘柄, **When** データエクスポートを実行, **Then** エラーログに失敗理由が記録され、取得できた項目はnullとしてCSVに含まれる
2. **Given** 計算に必要なデータが欠損している指標, **When** 指標計算を実行, **Then** 該当する指標列はnullとなり、警告がログに記録される
3. **Given** データ取得・計算完了後, **When** CSV出力を確認, **Then** ファイル名にデータ取得日時が含まれている（形式: `stock_data_YYYYMMDD_HHMMSS.csv`）

---

### Edge Cases

- yfinanceのAPIレート制限に達した場合はどう処理するか？→ 最大3回リトライ（指数バックオフ：1秒、2秒、4秒）を実行し、3回失敗したらエラーとして報告
- 銘柄コードが無効（存在しない）場合はどう処理するか？→ エラーログに記録し、その銘柄はスキップして処理を継続
- 財務データの会計期が異なる銘柄が混在する場合はどう処理するか？→ 最新の会計期データを使用し、データ取得日時と共に会計期情報も記録
- CSV出力先のディレクトリが存在しない場合はどう処理するか？→ 自動でディレクトリを作成する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは銘柄コードのリストを入力として受け取り、yfinanceから財務データを取得できること。`--limit N`オプションで処理銘柄数を制限可能（デフォルト: 全銘柄、テスト段階では5銘柄推奨）
- **FR-002**: システムは取得した財務データから、以下のファンダメンタル指標を計算できること：
  - ネットキャッシュ比率
  - 企業価値（EV）
  - ROIC（Return on Invested Capital）
  - CROIC（Cash ROIC）
  - Gross Profitability
  - EV/EBIT
  - FCF利回り
  - Piotroski Fスコア（データが揃う場合のみ）
  - Shareholder Yield（データが揃う場合のみ）
  - PBR
  - EV/FCF
- **FR-003**: システムは指標計算の元となった個別の値（時価総額、総資産、現金、負債、営業CF、CAPEXなど）もCSVに含めること
- **FR-004**: システムはデータ取得日時をファイル名に記録すること。ファイル名形式: `stock_data_YYYYMMDD_HHMMSS.csv`（Constitution原則II: Reproducibility準拠）
- **FR-005**: システムはデータ取得エラー・計算エラーをログに記録し、エラーが発生した項目はnullとして扱うこと（Constitution原則I: Data Quality準拠）
- **FR-006**: タイムスタンプ付きファイル名により、複数回実行時の上書きを自動的に防止すること
- **FR-007**: システムはTSV/CSVファイルの2列目（インデックス1）から銘柄コードを読み込むこと。デフォルトファイルパス: `note/data/data_j - Sheet1.tsv`（"コード"列）。オプションで別のファイルパスをコマンドライン引数で指定可能

### Constitution Compliance Requirements

All features MUST comply with the jp-quant-playground Constitution (v1.0.0):

- **Data Quality**: yfinance data validation with polars, explicit null handling for missing data
- **Reproducibility**: Fixed random seeds (if applicable), documented parameters, timestamped data acquisition
- **Transparency**: Variable naming follows `{data_type}_{processing}_{condition}` pattern (if using marimo)
- **Performance**: polars (not pandas), cash flow metrics prioritized, lazy evaluation for large datasets
- **Maintainability**: Type hints, Ruff-compliant, indicator logic in `note/libs/indicators.py` (already exists)

### Key Entities *(include if feature involves data)*

- **StockFinancialData**: 1銘柄の財務データを表すエンティティ
  - 属性: 銘柄コード、銘柄名、時価総額、総資産、総負債、現金及び現金等価物、営業CF、CAPEX、EBIT、売上総利益、純利益、株主資本など
  - 関係: 複数の計算済み指標と1対多の関係
- **CalculatedIndicator**: 計算されたファンダメンタル指標
  - 属性: 指標名、指標値、計算式の元となった値のリスト
  - 関係: StockFinancialDataに従属
- **ExportMetadata**: CSV出力のメタデータ
  - 属性: データ取得日時、対象銘柄数、成功/失敗数、出力ファイルパス

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 5銘柄のデータ取得から指標計算、CSV出力までを2分以内に完了できる（銘柄数に応じてスケール）
- **SC-002**: yfinanceから取得可能な財務データ項目の90%以上を正しく取得できる（銘柄によってはデータ欠損があることを考慮）
- **SC-003**: 出力CSVに、指標列（最低5種類）と計算元データ列（最低10項目）が含まれている
- **SC-004**: データ取得エラーが発生した場合でも、エラー内容が明確にログに記録され、取得できたデータは失われない
- **SC-005**: 同じ銘柄リストで複数回実行した場合、データ取得日が同一であれば、出力される指標値が完全に一致する（再現性の保証）

## Clarifications

### Session 2025-11-16

- Q: 入力インターフェース（銘柄リストの受け取り方法）はどうするか？ → A: TSVファイルから読み込み（デフォルト: `note/data/data_j - Sheet1.tsv`）、オプションで別のCSV/TSVファイルパスを指定可能
- Q: yfinance APIのリトライ回数と待機間隔はどうするか？ → A: 最大3回リトライ、指数バックオフ（1秒、2秒、4秒）
- Q: TSVファイルに5銘柄以上ある場合の処理は？ → A: 全銘柄処理（デフォルト）、`--limit N`オプションで銘柄数制限可能（テスト段階では`--limit 5`推奨）
- Q: データ取得日時などのメタデータの記録方法は？ → A: ファイル名にタイムスタンプを含める（形式: `stock_data_YYYYMMDD_HHMMSS.csv`）
- Q: TSVファイルのどの列から銘柄コードを読み取るか？ → A: 固定で2列目（インデックス1、"コード"列）を使用

## Assumptions

- yfinanceが提供するデータの正確性は保証されていないため、異常値検出は次フェーズの課題とする
- `--limit`オプションにより、小規模テスト（5銘柄）から大規模データセット（数百〜数千銘柄）まで対応可能な設計
- CSV出力先のデフォルトディレクトリは`note/data/exports/`とする
- 既存の`note/libs/indicators.py`の指標計算関数を再利用する
