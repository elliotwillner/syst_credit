from __future__ import annotations

import logging
from typing import Literal

import pandas as pd

logger = logging.getLogger(__name__)


def build_internal_oas_proxy(
    bond_df: pd.DataFrame,
    date_col: str = "Date",
    oas_col: str = "OAS",
    method: Literal["median", "mean"] = "median",
    z_window: int = 36,
) -> pd.DataFrame:
    """
    Build an internal high-yield OAS proxy from the bond-level universe.

    This creates a monthly credit spread proxy using the same investable universe
    as the portfolio model. Median OAS is preferred because HY data can contain
    distressed outliers.

    Parameters
    ----------
    bond_df : pd.DataFrame
        Bond-level dataframe containing at least Date and OAS.
    date_col : str
        Name of the date column.
    oas_col : str
        Name of the OAS column.
    method : {"median", "mean"}
        Main aggregation method used for the proxy.
    z_window : int
        Rolling window, in months, used for z-score calculation.

    Returns
    -------
    pd.DataFrame
        Monthly dataframe indexed by Date with internal OAS features.
    """
    required_cols = {date_col, oas_col}
    missing_cols = required_cols - set(bond_df.columns)

    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df = bond_df[[date_col, oas_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df[oas_col] = pd.to_numeric(df[oas_col], errors="coerce")

    before_rows = len(df)
    df = df.dropna(subset=[date_col, oas_col])
    after_rows = len(df)

    if after_rows < before_rows:
        logger.warning("Dropped %s rows with missing Date/OAS.", before_rows - after_rows)

    df[date_col] = df[date_col].dt.to_period("M").dt.to_timestamp()

    monthly = df.groupby(date_col)[oas_col].agg(
        hy_oas_median="median",
        hy_oas_mean="mean",
        hy_oas_p25=lambda x: x.quantile(0.25),
        hy_oas_p75=lambda x: x.quantile(0.75),
        n_bonds="count",
    )

    monthly["hy_oas_dispersion"] = monthly["hy_oas_p75"] - monthly["hy_oas_p25"]

    main_col = f"hy_oas_{method}"
    monthly["hy_oas_proxy"] = monthly[main_col]

    monthly["hy_oas_chg"] = monthly["hy_oas_proxy"].diff()

    rolling_mean = monthly["hy_oas_proxy"].rolling(z_window, min_periods=z_window).mean()
    rolling_std = monthly["hy_oas_proxy"].rolling(z_window, min_periods=z_window).std()

    monthly["hy_oas_z"] = (
        monthly["hy_oas_proxy"] - rolling_mean
    ) / rolling_std

    monthly.index.name = "Date"

    logger.info(
        "Built internal OAS proxy from %s to %s using %s aggregation.",
        monthly.index.min().date(),
        monthly.index.max().date(),
        method,
    )

    return monthly