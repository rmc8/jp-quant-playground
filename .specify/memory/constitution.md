<!--
Sync Impact Report - Constitution v1.0.0

Version Change: None → v1.0.0 (Initial Constitution)
Ratification Date: 2025-11-16

Modified Principles:
  - NEW: I. Data Quality - yfinanceデータのバリデーションとpolars使用
  - NEW: II. Reproducibility - バックテスト環境の完全再現性
  - NEW: III. Transparency - marimoでの処理内容記述命名規則
  - NEW: IV. Performance - Polars優先とキャッシュフロー重視計算
  - NEW: V. Maintainability - 型ヒント、Ruffリント、モジュール化

Added Sections:
  - Development Workflow (開発フロー定義)
  - Analysis Standards (分析基準定義)

Removed Sections: N/A

Templates Requiring Updates:
  ✅ plan-template.md - Constitution Checkセクションに5原則を追加予定
  ✅ spec-template.md - Requirements/Constraintsに原則準拠確認を追加予定
  ✅ tasks-template.md - タスク分類に原則駆動型カテゴリを追加予定

Follow-up TODOs: None
-->

# jp-quant-playground Constitution

## Core Principles

### I. Data Quality (データ品質)

**データの信頼性を最優先とする**

- yfinanceから取得したデータには欠損・異常値が含まれる前提で設計すること
- polarsのスキーマ検証機能を活用し、データ型の整合性を確保すること
- 計算不可能な指標（データ不足）は明示的にnull扱いとし、推測値を使用しないこと
- データ取得時のエラーハンドリングを必須とし、失敗理由をログに記録すること

**Rationale**: yfinanceは全てのファンダメンタル指標を提供しないため、データ品質の検証なしでは誤った分析結果を導く可能性がある。polarsの厳格な型システムを活用することで、pandasよりも早期にデータ問題を検出できる。

### II. Reproducibility (再現性)

**全ての分析結果は完全に再現可能でなければならない**

- ランダム性を伴う処理（機械学習、サンプリング）は必ずシード値を固定すること
- バックテストのパラメータ（リバランス頻度、取引コスト、銘柄数など）を明記すること
- データ取得日時を記録し、時系列データの参照時点を明確化すること
- 環境依存を排除し、`uv.lock`で依存関係のバージョンを固定すること

**Rationale**: クオンツ戦略の検証においては、同じ条件で同じ結果が得られることが科学的信頼性の基盤となる。再現不可能な分析は検証も改善もできない。

### III. Transparency (透明性)

**marimo変数の命名は処理内容を完全に記述すること**

- marimoの変数再定義制約により、変数名で処理内容を区別すること
- ❌ Bad: `data = fetch()` → `data = clean()` (再定義エラー)
- ✅ Good: `raw_stock_data` → `stock_data_with_indicators` → `filtered_high_ncav_stocks`
- 変数名のパターン: `{データ種別}_{処理内容}_{条件}` (例: `backtest_portfolio_returns_top_quintile`)
- 一時変数であっても、その役割が明確にわかる名前を付けること

**Rationale**: marimoは変数の再定義を許さないため、処理フロー全体が変数名に反映される。これは可読性と保守性の向上に直結する強制的な良習慣である。

### IV. Performance (パフォーマンス)

**計算効率とキャッシュフロー重視の指標設計**

- pandasではなくpolarsを使用すること（高速、メモリ効率、並列処理）
- 会計利益ベースよりもキャッシュフローベースの指標を優先すること
- FCF（営業CF - CAPEX）、CROIC（Cash ROIC）など、現金創出力に焦点を当てること
- 大量銘柄の指標計算は遅延評価（lazy evaluation）を活用すること

**Rationale**: polarsはpandasの10-100倍高速であり、日本株全市場（約4000銘柄）の分析に必須。また、日本企業の会計利益は保守的すぎるため、キャッシュフロー指標の方が実態を反映する。

### V. Maintainability (保守性)

**長期的な保守性を確保する設計**

- Python 3.12の型ヒントを必須とし、mypy互換の静的型付けを行うこと
- Ruffでリント・フォーマットを統一し、手動フォーマットを禁止すること
- 指標計算ロジックは`note/libs/indicators.py`に集約し、ノートブックから分離すること
- 関数は単一責任原則に従い、1関数1指標の計算とすること

**Rationale**: クオンツ戦略は長期的な検証と改善が必要なため、コードの可読性と変更容易性が成功の鍵となる。特に指標計算ロジックの再利用性は分析の生産性を大きく向上させる。

## Development Workflow

### ノートブック開発プロセス

1. **仮説立案**: 検証したいファンダメンタル指標の組み合わせを文書化
2. **指標実装**: `note/libs/indicators.py`に計算関数を追加（型ヒント付き）
3. **marimo作成**: セクション構成を決定し、変数命名規則に従ってノートブックを作成
4. **EDA実行**: plotlyで指標の分布・相関を可視化し、異常値を確認
5. **バックテスト**: シード固定、パラメータ明記の上で実行
6. **検証**: 再現性確認（別日実行で同一結果）、Ruffチェック、isort実行

### コード品質ゲート

全てのコミット前に以下を実行すること：

```bash
uv run ruff check .
uv run ruff format .
uv run isort .
```

### marimoノートブック実行

```bash
uv run marimo edit note/{notebook_name}.py
```

## Analysis Standards

### ファンダメンタル指標の計算基準

以下の計算式を厳守すること（`note/indicators.md`参照）：

- **EV（企業価値）**: 時価総額 + 純有利子負債（= 有利子負債 - 現金等価物）
- **ROIC**: NOPAT / 投下資本（運転資本を含む）
- **FCF（フリーキャッシュフロー）**: 営業CF - CAPEX
- **Shareholder Yield**: 配当利回り + 自社株買い純額利回り + 負債削減利回り

### バックテスト設計原則

- **リバランス頻度**: 月次または四半次（過剰最適化を避けるため年次は避ける）
- **取引コスト**: 片道0.3%以上を想定（日本株の実務的コスト）
- **ユニバース**: 時価総額・流動性でフィルタ（マイクロキャップ除外）
- **ルックアヘッドバイアス**: 財務データは公表後の取引日から使用可能とする

### 機械学習・統計分析基準

本プロジェクトでは以下の分析手法を優先する：

1. **指標の予測力評価**: IC（Information Coefficient）分析、Quintile分析で単一指標の有効性を検証
2. **リスク調整後リターン**: シャープレシオ、最大ドローダウン、カルマーレシオの最適化
3. **因子分解分析**: Value/Quality/Safety因子へのリターン寄与度分解

scikit-learnを使用する場合も、必ず`random_state`パラメータでシードを固定すること。

## Governance

### 憲法の改正手順

1. 改正提案を`.specify/memory/`配下にドラフトとして作成
2. 既存原則との矛盾点、影響範囲を文書化
3. テンプレートファイル（plan/spec/tasks）との整合性を確認
4. バージョン番号をセマンティックバージョニングに従って更新：
   - **MAJOR**: 原則の削除・根本的再定義（後方非互換）
   - **MINOR**: 新原則の追加・既存原則の大幅拡張
   - **PATCH**: 文言の明確化・誤字修正（意味変更なし）
5. Sync Impact Reportを更新し、憲法ファイル冒頭に記録

### コンプライアンス確認

- 全ての機能実装前に、この憲法の5原則に照らして設計を確認すること
- `/speckit.plan`コマンド実行時、Constitution Checkセクションで原則違反がないか検証すること
- 原則違反が必要な場合、Complexity Trackingセクションで正当化すること

### ランタイムガイダンス

日常的な開発ガイダンスは`CLAUDE.md`を参照すること。憲法は原則のみを定義し、具体的な実装手順は`CLAUDE.md`に委譲する。

**Version**: 1.0.0 | **Ratified**: 2025-11-16 | **Last Amended**: 2025-11-16
