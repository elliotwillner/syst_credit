from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def _cross_sectional_zscore(x: pd.Series) -> pd.Series:
    """Compute cross-sectional z-score for one date."""
    std = x.std()

    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=x.index)

    return (x - x.mean()) / std


def build_bond_signal(
    bond_df: pd.DataFrame,
    regime: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """
    Build a bond-level systematic credit score.

    The signal favors higher spread/yield bonds but penalizes riskier bonds,
    especially during risk-off macro regimes.

    Parameters
    ----------
    bond_df : pd.DataFrame
        Bond-level dataframe.
    regime : pd.DataFrame
        Monthly regime dataframe indexed by Date.
    config : dict
        Project config loaded from YAML.

    Returns
    -------
    pd.DataFrame
        Bond-level dataframe with signal features and final signal_score.
    """
    required_cols = [
        "Date",
        "ISIN",
        "Ticker",
        "Eff_Rating_Group",
        "Class2",
        "OAS",
        "DTS",
        "OAD",
        "Yield_To_Worst",
        "Excess_Return_MTD",
    ]

    missing_cols = [col for col in required_cols if col not in bond_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required bond columns: {missing_cols}")

    df = bond_df.copy()

    df["Date"] = pd.to_datetime(df["Date"]).dt.to_period("M").dt.to_timestamp()
    df = df.sort_values(["Date", "ISIN"])

    numeric_cols = ["OAS", "DTS", "OAD", "Yield_To_Worst", "Excess_Return_MTD"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(
        subset=[
            "Date",
            "ISIN",
            "Ticker",
            "Eff_Rating_Group",
            "Class2",
            "OAS",
            "DTS",
            "OAD",
            "Yield_To_Worst",
            "Excess_Return_MTD",
        ]
    ).copy()

    logger.info("Dropped %s rows before bond signal construction.", before - len(df))

    # Next-month return avoids lookahead bias.
    df["next_excess_return"] = df.groupby("ISIN")["Excess_Return_MTD"].shift(-1)

    df = df.dropna(subset=["next_excess_return"]).copy()

    # Cross-sectional features by month.
    for col in ["OAS", "DTS", "OAD", "Yield_To_Worst"]:
        df[f"{col.lower()}_z"] = df.groupby("Date")[col].transform(_cross_sectional_zscore)

    # Merge macro regime.
    regime = regime.copy()
    regime.index = pd.to_datetime(regime.index).to_period("M").to_timestamp()

    df = df.merge(
        regime[["regime_score", "regime"]],
        left_on="Date",
        right_index=True,
        how="left",
    )

    # Drop warm-up period where regime is unavailable.
    before_regime = len(df)
    df = df[df["regime"].notna() & (df["regime"] != "unknown")].copy()

    logger.info("Dropped %s rows with unavailable regime.", before_regime - len(df))

    # Base rating penalty.
    base_rating_penalty = {
        "BB": 0.00,
        "B": -0.20,
        "CCC": -0.75,
    }

    df["rating_penalty"] = df["Eff_Rating_Group"].map(base_rating_penalty).fillna(-0.25)

    # Regime-dependent risk penalty.
    # In risk-off environments, penalize DTS, duration, and CCC more heavily.
    regime_risk_multiplier = {
        "risk_on": 0.75,
        "neutral": 1.00,
        "risk_off": 1.50,
    }

    df["risk_multiplier"] = df["regime"].map(regime_risk_multiplier).fillna(1.0)

    df["ccc_flag"] = (df["Eff_Rating_Group"] == "CCC").astype(int)

    df["signal_score"] = (
        0.40 * df["yield_to_worst_z"]
        + 0.35 * df["oas_z"]
        - df["risk_multiplier"] * (
            0.30 * df["dts_z"]
            + 0.15 * df["oad_z"]
            + 0.40 * df["ccc_flag"]
        )
        + df["rating_penalty"]
    )

    logger.info(
        "Built bond signal with %s rows across %s months.",
        len(df),
        df["Date"].nunique(),
    )

    return df