from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def build_regime_signal(
    macro_features: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """
    Build a simple macro regime score and classify each month as:
    risk_on, neutral, or risk_off.

    Higher regime_score means worse credit-risk environment.

    Parameters
    ----------
    macro_features : pd.DataFrame
        Monthly macro feature dataframe indexed by Date.
    config : dict
        Project config loaded from YAML.

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by Date with regime_score and regime.
    """
    regime_cfg = config["regime"]
    weights = regime_cfg["weights"]

    risk_on_threshold = regime_cfg.get("risk_on_threshold", -0.75)
    risk_off_threshold = regime_cfg.get("risk_off_threshold", 0.75)

    df = macro_features.copy()

    required_cols = list(weights.keys())
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"Missing macro feature columns for regime signal: {missing_cols}")

    # Weighted linear macro risk score.
    df["regime_score"] = 0.0

    for col, weight in weights.items():
        df["regime_score"] += weight * df[col]

    def classify(score: float) -> str:
        if pd.isna(score):
            return "unknown"
        if score >= risk_off_threshold:
            return "risk_off"
        if score <= risk_on_threshold:
            return "risk_on"
        return "neutral"

    df["regime"] = df["regime_score"].apply(classify)

    result = df[["regime_score", "regime"]].copy()

    logger.info("Built regime signal. Regime counts: %s", result["regime"].value_counts().to_dict())

    return result