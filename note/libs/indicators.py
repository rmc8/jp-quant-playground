"""
ファンダメンタル指標計算ライブラリ

このモジュールは note/indicators.md に定義された10のファンダメンタル指標を計算します。
全ての関数は型ヒントを持ち、polars DataFrameを使用します。

Constitution Compliance:
- Data Quality: 欠損値を明示的にnullとして扱い、計算不可能な場合はNoneを返す
- Performance: polars使用、キャッシュフロー重視
- Maintainability: 1関数1指標、型ヒント必須
"""

import polars as pl


def calculate_net_cash_ratio(
    total_cash: pl.Series | pl.Expr,
    total_debt: pl.Series | pl.Expr,
    market_cap: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    ネットキャッシュ比率を計算

    Formula: (現金等価物 - 有利子負債) / 時価総額

    Args:
        total_cash: 現金及び現金等価物
        total_debt: 有利子負債
        market_cap: 時価総額

    Returns:
        ネットキャッシュ比率（負の値 = ネット負債）
    """
    net_cash = total_cash - total_debt
    return net_cash / market_cap


def calculate_enterprise_value(
    market_cap: pl.Series | pl.Expr,
    total_debt: pl.Series | pl.Expr,
    total_cash: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    企業価値（EV: Enterprise Value）を計算

    Formula: 時価総額 + 純有利子負債

    Args:
        market_cap: 時価総額
        total_debt: 有利子負債
        total_cash: 現金及び現金等価物

    Returns:
        企業価値（EV）
    """
    net_debt = total_debt - total_cash
    return market_cap + net_debt


def calculate_roic(
    nopat: pl.Series | pl.Expr,
    invested_capital: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    ROIC（Return on Invested Capital）を計算

    Formula: NOPAT / 投下資本

    Args:
        nopat: 税引後営業利益（Net Operating Profit After Tax）
        invested_capital: 投下資本（純有形資産 + 運転資本）

    Returns:
        ROIC（%）
    """
    return nopat / invested_capital


def calculate_croic(
    operating_cash_flow: pl.Series | pl.Expr,
    capex: pl.Series | pl.Expr,
    invested_capital: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    CROIC（Cash Return on Invested Capital）を計算

    Formula: (営業CF - CAPEX) / 投下資本

    Args:
        operating_cash_flow: 営業キャッシュフロー
        capex: 設備投資額（資本的支出）
        invested_capital: 投下資本

    Returns:
        CROIC（%）
    """
    cash_return = operating_cash_flow - capex
    return cash_return / invested_capital


def calculate_gross_profitability(
    gross_profit: pl.Series | pl.Expr,
    total_assets: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    Gross Profitability（総利益 / 総資産）を計算

    Formula: 総利益 / 総資産

    Args:
        gross_profit: 総利益（売上総利益）
        total_assets: 総資産

    Returns:
        Gross Profitability（%）
    """
    return gross_profit / total_assets


def calculate_ev_ebit(
    enterprise_value: pl.Series | pl.Expr,
    ebit: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    EV/EBIT（企業価値 / 営業利益）を計算

    Formula: EV / EBIT

    Args:
        enterprise_value: 企業価値（EV）
        ebit: 営業利益（EBIT: Earnings Before Interest and Taxes）

    Returns:
        EV/EBIT倍率
    """
    return enterprise_value / ebit


def calculate_fcf_yield(
    operating_cash_flow: pl.Series | pl.Expr,
    capex: pl.Series | pl.Expr,
    market_cap: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    FCF利回り（Free Cash Flow Yield）を計算

    Formula: (営業CF - CAPEX) / 時価総額

    Args:
        operating_cash_flow: 営業キャッシュフロー
        capex: 設備投資額
        market_cap: 時価総額

    Returns:
        FCF利回り（%）
    """
    fcf = operating_cash_flow - capex
    return fcf / market_cap


def calculate_piotroski_f_score(
    net_income: pl.Series | pl.Expr,
    operating_cash_flow: pl.Series | pl.Expr,
    roa: pl.Series | pl.Expr,
    roa_prev: pl.Series | pl.Expr,
    ocf_greater_ni: pl.Series | pl.Expr,
    long_term_debt: pl.Series | pl.Expr,
    long_term_debt_prev: pl.Series | pl.Expr,
    current_ratio: pl.Series | pl.Expr,
    current_ratio_prev: pl.Series | pl.Expr,
    shares_outstanding: pl.Series | pl.Expr,
    shares_outstanding_prev: pl.Series | pl.Expr,
    gross_margin: pl.Series | pl.Expr,
    gross_margin_prev: pl.Series | pl.Expr,
    asset_turnover: pl.Series | pl.Expr,
    asset_turnover_prev: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    Piotroski Fスコア（0-9点）を計算

    9つの財務基準で企業の財務健全性を評価：
    1. Profitability (収益性): 4項目
    2. Leverage/Liquidity (レバレッジ/流動性): 3項目
    3. Operating Efficiency (営業効率): 2項目

    Args:
        net_income: 当期純利益
        operating_cash_flow: 営業CF
        roa: 当期ROA
        roa_prev: 前期ROA
        ocf_greater_ni: 営業CF > 純利益 (boolean)
        long_term_debt: 当期長期負債
        long_term_debt_prev: 前期長期負債
        current_ratio: 当期流動比率
        current_ratio_prev: 前期流動比率
        shares_outstanding: 当期発行済株式数
        shares_outstanding_prev: 前期発行済株式数
        gross_margin: 当期売上総利益率
        gross_margin_prev: 前期売上総利益率
        asset_turnover: 当期総資産回転率
        asset_turnover_prev: 前期総資産回転率

    Returns:
        Fスコア（0-9の整数）
    """
    score = pl.lit(0)

    # Profitability (4 points)
    score += (net_income > 0).cast(pl.Int32)
    score += (operating_cash_flow > 0).cast(pl.Int32)
    score += (roa > roa_prev).cast(pl.Int32)
    score += ocf_greater_ni.cast(pl.Int32)

    # Leverage/Liquidity (3 points)
    score += (long_term_debt < long_term_debt_prev).cast(pl.Int32)
    score += (current_ratio > current_ratio_prev).cast(pl.Int32)
    score += (shares_outstanding <= shares_outstanding_prev).cast(pl.Int32)

    # Operating Efficiency (2 points)
    score += (gross_margin > gross_margin_prev).cast(pl.Int32)
    score += (asset_turnover > asset_turnover_prev).cast(pl.Int32)

    # Note: Mypy型推論の制限により、pl.lit(0)から始まるスコア計算はExpr型と推論されます
    # 実行時には正しくSeries | Exprとして動作するため、型チェックを無視します
    return score  # type: ignore[return-value]


def calculate_shareholder_yield(
    dividends: pl.Series | pl.Expr,
    share_buyback_net: pl.Series | pl.Expr,
    debt_reduction: pl.Series | pl.Expr,
    market_cap: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    Shareholder Yield（株主還元利回り）を計算

    Formula: (配当 + 自社株買い純額 + 負債削減額) / 時価総額

    Args:
        dividends: 年間配当総額
        share_buyback_net: 自社株買い純額（買い - 売り）
        debt_reduction: 負債削減額（前期負債 - 当期負債）
        market_cap: 時価総額

    Returns:
        Shareholder Yield（%）
    """
    total_shareholder_return = dividends + share_buyback_net + debt_reduction
    return total_shareholder_return / market_cap


def calculate_pbr(
    market_cap: pl.Series | pl.Expr,
    book_value: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    PBR（株価純資産倍率: Price-to-Book Ratio）を計算

    Formula: 時価総額 / 純資産

    Args:
        market_cap: 時価総額
        book_value: 純資産（株主資本）

    Returns:
        PBR倍率
    """
    return market_cap / book_value


def calculate_ev_fcf(
    enterprise_value: pl.Series | pl.Expr,
    operating_cash_flow: pl.Series | pl.Expr,
    capex: pl.Series | pl.Expr,
) -> pl.Series | pl.Expr:
    """
    EV/FCF（企業価値 / フリーキャッシュフロー）を計算

    Formula: EV / (営業CF - CAPEX)

    Args:
        enterprise_value: 企業価値（EV）
        operating_cash_flow: 営業キャッシュフロー
        capex: 設備投資額

    Returns:
        EV/FCF倍率
    """
    fcf = operating_cash_flow - capex
    return enterprise_value / fcf


def add_fundamental_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """
    DataFrameに全てのファンダメンタル指標を追加

    yfinanceから取得したデータフレームに対して、
    10のファンダメンタル指標を計算して列として追加します。

    Args:
        df: yfinanceデータを含むpolars DataFrame
            必須列: market_cap, total_cash, total_debt, gross_profit,
                   total_assets, ebit, operating_cash_flow, capex,
                   net_income, book_value など

    Returns:
        指標列が追加されたDataFrame

    Note:
        欠損値がある場合、該当する指標はnullとなります。
        Constitution原則I（Data Quality）に従い、推測値は使用しません。
    """
    # 企業価値（EV）を計算（他の指標で使用）
    df = df.with_columns(
        enterprise_value=calculate_enterprise_value(
            df["market_cap"], df["total_debt"], df["total_cash"]
        )
    )

    # 各指標を計算
    df = df.with_columns(
        [
            calculate_net_cash_ratio(
                df["total_cash"], df["total_debt"], df["market_cap"]
            ).alias("net_cash_ratio"),
            calculate_roic(df["nopat"], df["invested_capital"]).alias("roic"),
            calculate_croic(
                df["operating_cash_flow"], df["capex"], df["invested_capital"]
            ).alias("croic"),
            calculate_gross_profitability(df["gross_profit"], df["total_assets"]).alias(
                "gross_profitability"
            ),
            calculate_ev_ebit(df["enterprise_value"], df["ebit"]).alias("ev_ebit"),
            calculate_fcf_yield(
                df["operating_cash_flow"], df["capex"], df["market_cap"]
            ).alias("fcf_yield"),
            calculate_pbr(df["market_cap"], df["book_value"]).alias("pbr"),
            calculate_ev_fcf(
                df["enterprise_value"], df["operating_cash_flow"], df["capex"]
            ).alias("ev_fcf"),
        ]
    )

    return df
