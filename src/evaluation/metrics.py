from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_performance_metrics(
    backtest: pd.DataFrame,
    return_col: str = "portfolio_excess_return",
    periods_per_year: int = 12,
) -> pd.Series:
    """
    Compute standard monthly backtest performance metrics.
    """
    if return_col not in backtest.columns:
        raise ValueError(f"Missing return column: {return_col}")

    returns = pd.to_numeric(backtest[return_col], errors="coerce").dropna()

    if returns.empty:
        raise ValueError("No valid returns available for performance metrics.")

    wealth = (1 + returns).cumprod()
    drawdown = wealth / wealth.cummax() - 1

    ann_return = returns.mean() * periods_per_year
    ann_vol = returns.std() * np.sqrt(periods_per_year)
    sharpe = ann_return / ann_vol if ann_vol != 0 else np.nan

    metrics = pd.Series(
        {
            "start_date": returns.index.min(),
            "end_date": returns.index.max(),
            "n_months": len(returns),
            "annualized_excess_return": ann_return,
            "annualized_volatility": ann_vol,
            "sharpe_ratio": sharpe,
            "cumulative_excess_return": wealth.iloc[-1] - 1,
            "max_drawdown": drawdown.min(),
            "hit_rate": (returns > 0).mean(),
            "best_month": returns.max(),
            "worst_month": returns.min(),
            "avg_monthly_return": returns.mean(),
        }
    )

    logger.info("Computed performance metrics.")

    return metrics


def compute_turnover(portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly one-way turnover from target weights.

    Turnover is defined as:
        0.5 * sum(abs(w_t - w_{t-1}))

    Missing holdings are treated as zero.
    """
    required_cols = ["Date", "ISIN", "target_weight"]

    missing_cols = [col for col in required_cols if col not in portfolio.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for turnover: {missing_cols}")

    df = portfolio[required_cols].copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.to_period("M").dt.to_timestamp()

    weights = (
        df.pivot_table(
            index="Date",
            columns="ISIN",
            values="target_weight",
            aggfunc="sum",
            fill_value=0.0,
        )
        .sort_index()
    )

    turnover = 0.5 * weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = np.nan

    result = turnover.rename("turnover").to_frame()

    logger.info("Computed turnover for %s months.", len(result))

    return result


def combine_metrics(
    backtest: pd.DataFrame,
    portfolio: pd.DataFrame,
) -> pd.Series:
    """
    Combine performance and turnover metrics into one summary.
    """
    perf = compute_performance_metrics(backtest)
    turnover = compute_turnover(portfolio)

    perf["avg_monthly_turnover"] = turnover["turnover"].mean()
    perf["max_monthly_turnover"] = turnover["turnover"].max()

    return perf