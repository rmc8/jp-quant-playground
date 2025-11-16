---

description: "Task list for yfinance Data Exporter implementation"
---

# Tasks: yfinance Data Exporter

**Input**: Design documents from `/specs/001-yfinance-data-exporter/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: Tests are NOT explicitly requested in the spec, but basic validation is included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `note/`, `tests/` at repository root
- Paths shown below use the actual project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create output directory `note/data/exports/` for CSV files
- [X] T002 [P] Create `note/scripts/` directory for CLI entry point
- [X] T003 [P] Verify dependencies are installed: polars>=1.35.2, yfinance>=0.2.66, pytest
- [X] T004 [P] Create `tests/note/` directory structure for test files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `note/libs/data_fetcher.py` with stub functions: `fetch_ticker_data(ticker: str) -> dict`, `fetch_with_retry(ticker: str, max_retries: int) -> Optional[dict]`
- [X] T006 [P] Implement retry logic with exponential backoff in `note/libs/data_fetcher.py`: 1s, 2s, 4s waits (max 3 retries)
- [X] T007 [P] Create `note/libs/csv_exporter.py` with stub functions: `read_tickers_from_tsv(file_path: str, limit: Optional[int]) -> list[str]`, `export_to_csv(data: pl.DataFrame, output_dir: str) -> str`
- [X] T008 Implement TSV reading in `note/libs/csv_exporter.py`: read column index 1 (ticker codes), apply `--limit` if specified
- [X] T009 Implement CSV export with timestamp in `note/libs/csv_exporter.py`: filename format `stock_data_YYYYMMDD_HHMMSS.csv`
- [X] T010 [P] Create CLI entry point `note/scripts/export_stock_data.py` with argparse setup: `--input`, `--limit`, `--output` options (or consider python-fire per research.md)
- [X] T011 Add logging configuration in `note/scripts/export_stock_data.py`: INFO/WARNING/ERROR levels, format `[LEVEL] Message`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Data Export (Priority: P1) 🎯 MVP

**Goal**: クオンツアナリストが、指定した銘柄の財務データとファンダメンタル指標を一度に取得し、CSV形式で保存できる

**Independent Test**: 銘柄コードのリストを入力として与え、CSV出力を確認することで完全にテスト可能。出力CSVに期待される列（生データ+指標）が全て含まれていることを検証できる

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `fetch_ticker_data()` in `note/libs/data_fetcher.py`: fetch from yfinance API using `yf.Ticker(ticker).info`, `.balance_sheet`, `.cashflow`, `.financials`
- [X] T013 [US1] Add error handling to `fetch_ticker_data()`: catch exceptions, return empty dict on failure, log errors
- [X] T014 [P] [US1] Implement `fetch_with_retry()` wrapper in `note/libs/data_fetcher.py`: call `fetch_ticker_data()` with retry logic from T006
- [X] T015 [P] [US1] Create data transformation function in `note/libs/csv_exporter.py`: `build_dataframe(raw_data_list: list[dict]) -> pl.DataFrame` to construct polars DataFrame from list of ticker data
- [X] T016 [US1] Integrate `note/libs/indicators.py` (existing) in `note/libs/csv_exporter.py`: import and call indicator calculation functions on DataFrame
- [X] T017 [US1] Wire up main flow in `note/scripts/export_stock_data.py`: read TSV → fetch data for each ticker → build DataFrame → calculate indicators → export CSV
- [X] T018 [US1] Add basic validation in `note/scripts/export_stock_data.py`: check input file exists, output directory is writable, exit with code 1 on errors

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - run with `--limit 5` to verify

---

## Phase 4: User Story 2 - Detailed Data Provenance (Priority: P2)

**Goal**: クオンツアナリストが、計算された指標だけでなく、その計算の元となった個別の値も同じCSVに記録できる

**Independent Test**: CSV出力に、指標列（例：`net_cash_ratio`）だけでなく、その計算要素列（`total_cash`, `total_debt`, `market_cap`）も含まれていることを確認できる

### Implementation for User Story 2

- [X] T019 [P] [US2] Update `fetch_ticker_data()` in `note/libs/data_fetcher.py`: ensure all raw financial fields are captured in return dict (market_cap, total_cash, total_debt, total_assets, book_value, operating_cash_flow, capex, ebit, gross_profit, net_income)
- [X] T020 [US2] Update `build_dataframe()` in `note/libs/csv_exporter.py`: include both raw data columns AND indicator columns in output DataFrame
- [X] T021 [US2] Verify CSV column order in `note/libs/csv_exporter.py`: ticker first, then raw data (alphabetical), then indicators (alphabetical) per data-model.md
- [X] T022 [US2] Add data integrity validation in `note/scripts/export_stock_data.py`: log warning if any indicators cannot be calculated due to missing raw data

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - CSV should contain both raw data and indicators

---

## Phase 5: User Story 3 - Error Handling and Data Validation (Priority: P3)

**Goal**: クオンツアナリストが、yfinanceからデータ取得に失敗した場合や、計算不可能な指標がある場合でも、エラー内容を把握し、取得できたデータは保存できる

**Independent Test**: 意図的にデータ不足の銘柄を含めて実行し、エラーログと出力CSVの両方を検証できる

### Implementation for User Story 3

- [X] T023 [P] [US3] Enhance error logging in `note/libs/data_fetcher.py`: log specific failure reason for each ticker (network error, API error, invalid ticker)
- [X] T024 [P] [US3] Add null handling in `note/libs/csv_exporter.py`: when raw data field is null, set to polars null (not empty string or 0)
- [X] T025 [US3] Update indicator calculation integration: catch calculation errors, log warnings, set indicator to null if calculation fails
- [X] T026 [US3] Add summary statistics logging in `note/scripts/export_stock_data.py`: log "Successfully processed X/Y stocks" with count of failures
- [X] T027 [US3] Implement file existence check in `note/scripts/export_stock_data.py`: check `--input` file exists before processing, exit with helpful error message if not
- [X] T028 [US3] Implement output directory auto-creation in `note/scripts/export_stock_data.py`: use `pathlib.Path.mkdir(parents=True, exist_ok=True)` for `--output` directory

**Checkpoint**: All user stories should now be independently functional with robust error handling

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Add type hints to all functions in `note/libs/data_fetcher.py` per Constitution principle V
- [X] T030 [P] Add type hints to all functions in `note/libs/csv_exporter.py` per Constitution principle V
- [X] T031 [P] Add type hints to main function in `note/scripts/export_stock_data.py` per Constitution principle V
- [X] T032 [P] Run `uv run ruff check note/` and fix any linting errors
- [X] T033 [P] Run `uv run ruff format note/` to format code
- [X] T034 [P] Run `uv run isort note/` to organize imports
- [X] T035 Manual end-to-end test per quickstart.md: run with `--limit 5`, verify CSV output contains expected columns
- [X] T036 [P] Create basic integration test in `tests/note/test_cli_integration.py`: test CLI with mock input file, verify CSV output exists
- [X] T037 [P] Create unit test for retry logic in `tests/note/test_data_fetcher.py`: mock yfinance failures, verify exponential backoff
- [X] T038 [P] Create unit test for CSV export in `tests/note/test_csv_exporter.py`: test timestamp filename generation, column ordering

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 but is independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1/US2 but is independently testable

### Within Each User Story

- Tasks marked [P] within a story can run in parallel
- Core implementation (fetch, transform, export) must complete before validation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003, T004)
- All Foundational tasks marked [P] can run in parallel within Phase 2 (T005, T006, T007, T010)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Tasks within a story marked [P] can run in parallel:
  - US1: T012, T014, T015 can run in parallel
  - US2: T019, T020 can start in parallel
  - US3: T023, T024, T027, T028 can run in parallel
- All polish tasks (T029-T034, T036-T038) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch core implementation tasks together (different files):
Task: "Implement fetch_ticker_data() in note/libs/data_fetcher.py"
Task: "Implement fetch_with_retry() wrapper in note/libs/data_fetcher.py"
Task: "Create data transformation function in note/libs/csv_exporter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T011) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T012-T018)
4. **STOP and VALIDATE**: Test User Story 1 independently with `uv run python note/scripts/export_stock_data.py --limit 5`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (T012-T018) → Test independently with `--limit 5` → Deploy/Demo (MVP!)
3. Add User Story 2 (T019-T022) → Test independently (verify raw data columns present) → Deploy/Demo
4. Add User Story 3 (T023-T028) → Test independently (test with invalid ticker) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T012-T018)
   - Developer B: User Story 2 (T019-T022) - can start in parallel but may need to coordinate with A
   - Developer C: User Story 3 (T023-T028) - can start in parallel
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Constitution compliance is baked into Foundational phase (type hints, polars, Ruff)

---

## Task Summary

**Total Tasks**: 38
**Setup Phase**: 4 tasks
**Foundational Phase**: 7 tasks (CRITICAL - blocks all stories)
**User Story 1 (P1)**: 7 tasks
**User Story 2 (P2)**: 4 tasks
**User Story 3 (P3)**: 6 tasks
**Polish Phase**: 10 tasks

**Parallel Opportunities**: 20 tasks marked [P] can run in parallel with others

**MVP Scope (Recommended)**: Complete through Phase 3 (User Story 1) = 18 tasks

**Independent Test Criteria**:
- US1: Run with `--limit 5`, verify CSV file generated with ticker + indicators
- US2: Verify CSV contains both raw data columns (market_cap, total_cash, etc.) and indicator columns (net_cash_ratio, fcf_yield, etc.)
- US3: Test with invalid ticker (e.g., "INVALID.T"), verify error logged but CSV still generated for valid tickers
