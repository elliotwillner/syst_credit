from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def _apply_group_cap(
    portfolio: pd.DataFrame,
    group_col: str,
    weight_col: str,
    cap: float,
    max_iter: int = 10,
) -> pd.DataFrame:
    """
    Apply a simple group cap by scaling down overweight groups and redistributing.
    """
    portfolio = portfolio.copy()

    for _ in range(max_iter):
        group_weights = portfolio.groupby(group_col)[weight_col].sum()
        over_cap = group_weights[group_weights > cap]

        if over_cap.empty:
            break

        for group, group_weight in over_cap.items():
            mask = portfolio[group_col] == group
            scale = cap / group_weight
            portfolio.loc[mask, weight_col] *= scale

        total_weight = portfolio[weight_col].sum()

        if total_weight > 0:
            portfolio[weight_col] /= total_weight

    return portfolio


def build_monthly_portfolio(
    group: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """
    Build target portfolio for one rebalance month using a top-percentile
    selection rule and simple long-only constraints.
    """
    portfolio_cfg = config["portfolio"]

    selection_pct = portfolio_cfg.get("selection_pct", 0.10)
    min_bonds = portfolio_cfg.get("min_bonds", 100)
    max_issuer_weight = portfolio_cfg.get("max_issuer_weight", 0.05)
    max_sector_weight = portfolio_cfg.get("max_sector_weight", 0.50)
    max_ccc_weight = portfolio_cfg.get("max_ccc_weight", 0.15)

    if group.empty:
        return group.copy()

    n_select = max(min_bonds, int(len(group) * selection_pct))
    n_select = min(n_select, len(group))

    selected = (
    group.sort_values("signal_score", ascending=False)
    .head(n_select)
    .copy()
    )

    if selected.empty:
        return selected

    selected["Date"] = group["Date"].iloc[0]
    selected["target_weight"] = 1.0 / len(selected)

    # Issuer cap
    selected = _apply_group_cap(
        selected,
        group_col="Ticker",
        weight_col="target_weight",
        cap=max_issuer_weight,
    )

    # Sector cap
    selected = _apply_group_cap(
        selected,
        group_col="Class2",
        weight_col="target_weight",
        cap=max_sector_weight,
    )

    # CCC cap
    selected["ccc_bucket"] = selected["Eff_Rating_Group"].eq("CCC").map(
        {True: "CCC", False: "Non-CCC"}
    )

    selected = _apply_group_cap(
        selected,
        group_col="ccc_bucket",
        weight_col="target_weight",
        cap=max_ccc_weight,
    )

    selected = selected.drop(columns=["ccc_bucket"])

    # Final normalization
    selected["target_weight"] = selected["target_weight"] / selected["target_weight"].sum()

    return selected


def build_portfolio(
    signal_df: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """
    Build constrained monthly long-only portfolios from bond signal scores.
    """
    required_cols = [
        "Date",
        "ISIN",
        "Ticker",
        "Class2",
        "Eff_Rating_Group",
        "signal_score",
        "next_excess_return",
    ]

    missing_cols = [col for col in required_cols if col not in signal_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for portfolio construction: {missing_cols}")

    df = signal_df.copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.to_period("M").dt.to_timestamp()

    portfolios = []

    for date, group in df.groupby("Date"):
        monthly_portfolio = build_monthly_portfolio(group, config)

        if monthly_portfolio.empty:
            continue

        monthly_portfolio = monthly_portfolio.copy()
        monthly_portfolio["Date"] = date
        portfolios.append(monthly_portfolio)

    if not portfolios:
        raise ValueError("No monthly portfolios were created.")

    portfolio = pd.concat(portfolios, ignore_index=True)

    logger.info(
        "Built portfolio with %s rows across %s months.",
        len(portfolio),
        portfolio["Date"].nunique(),
    )

    return portfolio

    
    """
    Build constrained monthly long-only portfolios from bond signal scores.

    Parameters
    ----------
    signal_df : pd.DataFrame
        Bond-level dataframe with signal_score and next_excess_return.
    config : dict
        Project config.

    Returns
    -------
    pd.DataFrame
        Selected portfolio holdings by Date with target weights.
    """
    required_cols = [
        "Date",
        "ISIN",
        "Ticker",
        "Class2",
        "Eff_Rating_Group",
        "signal_score",
        "next_excess_return",
    ]

    missing_cols = [col for col in required_cols if col not in signal_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for portfolio construction: {missing_cols}")

    df = signal_df.copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.to_period("M").dt.to_timestamp()

    portfolio = (
        df.groupby("Date", group_keys=False)
        .apply(lambda x: build_monthly_portfolio(x, config))
        .reset_index(drop=True)
    )

    logger.info(
        "Built portfolio with %s rows across %s months.",
        len(portfolio),
        portfolio["Date"].nunique(),
    )

    return portfolio


def summarize_portfolio_exposures(portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly weighted portfolio exposures.
    """
    required_cols = ["Date", "target_weight", "OAS", "DTS", "OAD", "Yield_To_Worst"]

    missing_cols = [col for col in required_cols if col not in portfolio.columns]
    if missing_cols:
        raise ValueError(f"Missing columns for exposure summary: {missing_cols}")

    exposures = (
        portfolio.groupby("Date")
        .apply(
            lambda x: pd.Series(
                {
                    "n_bonds": x["ISIN"].nunique(),
                    "n_issuers": x["Ticker"].nunique(),
                    "avg_oas": (x["target_weight"] * x["OAS"]).sum(),
                    "avg_dts": (x["target_weight"] * x["DTS"]).sum(),
                    "avg_oad": (x["target_weight"] * x["OAD"]).sum(),
                    "avg_ytw": (x["target_weight"] * x["Yield_To_Worst"]).sum(),
                    "ccc_weight": x.loc[
                        x["Eff_Rating_Group"] == "CCC", "target_weight"
                    ].sum(),
                    "top_issuer_weight": x.groupby("Ticker")["target_weight"].sum().max(),
                    "top_sector_weight": x.groupby("Class2")["target_weight"].sum().max(),
                }
            )
        )
        .reset_index()
    )

    return exposures