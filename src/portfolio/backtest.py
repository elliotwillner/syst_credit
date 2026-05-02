from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def run_backtest(portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    Run monthly portfolio backtest from target weights and next-month returns.

    Assumes:
    - target_weight is formed at Date t
    - next_excess_return is the realized return for t+1
    - next_excess_return is in percent units, e.g. 1.25 means 1.25%

    Parameters
    ----------
    portfolio : pd.DataFrame
        Portfolio holdings by Date with target_weight and next_excess_return.

    Returns
    -------
    pd.DataFrame
        Monthly backtest results indexed by Date.
    """
    required_cols = ["Date", "target_weight", "next_excess_return"]

    missing_cols = [col for col in required_cols if col not in portfolio.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for backtest: {missing_cols}")

    df = portfolio.copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.to_period("M").dt.to_timestamp()
    df["target_weight"] = pd.to_numeric(df["target_weight"], errors="coerce")
    df["next_excess_return"] = pd.to_numeric(df["next_excess_return"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["Date", "target_weight", "next_excess_return"]).copy()

    if before > len(df):
        logger.warning("Dropped %s rows before backtest.", before - len(df))

    # Convert percent return to decimal return.
    df["weighted_return"] = df["target_weight"] * (df["next_excess_return"] / 100)

    returns = (
        df.groupby("Date")["weighted_return"]
        .sum()
        .rename("portfolio_excess_return")
        .to_frame()
        .sort_index()
    )

    returns["cumulative_excess_return"] = (
        1 + returns["portfolio_excess_return"]
    ).cumprod() - 1

    returns["wealth_index"] = (
        1 + returns["portfolio_excess_return"]
    ).cumprod()

    returns["running_peak"] = returns["wealth_index"].cummax()
    returns["drawdown"] = returns["wealth_index"] / returns["running_peak"] - 1

    logger.info(
        "Ran backtest from %s to %s with %s monthly observations.",
        returns.index.min().date(),
        returns.index.max().date(),
        len(returns),
    )

    return returns