from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def _load_fred_csv(path: Path, output_name: str) -> pd.DataFrame:
    """
    Load a single FRED CSV and standardize it to Date-indexed format.
    Expected columns are usually DATE and the series code.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing FRED file: {path}")

    df = pd.read_csv(path)

    if len(df.columns) != 2:
        raise ValueError(f"Expected 2 columns in {path.name}, got {df.columns.tolist()}")

    df.columns = ["Date", output_name]
    df["Date"] = pd.to_datetime(df["Date"])
    df[output_name] = pd.to_numeric(df[output_name].replace(".", pd.NA), errors="coerce")

    return df.set_index("Date").sort_index()


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    """Compute rolling z-score with a fixed lookback window."""
    rolling_mean = series.rolling(window, min_periods=window).mean()
    rolling_std = series.rolling(window, min_periods=window).std()

    return (series - rolling_mean) / rolling_std


def build_macro_features(
    config: dict,
    internal_oas: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build monthly macro features using downloaded FRED data plus internal HY OAS.

    Parameters
    ----------
    config : dict
        Project config loaded from YAML.
    internal_oas : pd.DataFrame
        Monthly internal OAS proxy indexed by Date.

    Returns
    -------
    pd.DataFrame
        Monthly macro feature dataframe indexed by Date.
    """
    macro_dir = Path(config["paths"]["raw_macro_dir"])
    z_window = config["features"].get("z_window", 36)

    fred_files = {
        "UNRATE.csv": "unemployment",
        "FEDFUNDS.csv": "fed_funds",
        "T10Y2Y.csv": "yield_curve",
        "VIXCLS.csv": "vix",
    }

    macro_parts = []

    for filename, output_name in fred_files.items():
        path = macro_dir / filename
        logger.info("Loading macro series: %s", path)
        macro_parts.append(_load_fred_csv(path, output_name))

    macro = pd.concat(macro_parts, axis=1).sort_index()

    # Convert all macro data to month-end observation, then timestamp as month-start
    # to match the bond data dates like 2010-01-01.
    macro = macro.resample("ME").last().ffill()
    macro.index = macro.index.to_period("M").to_timestamp()

    # Merge internal OAS proxy.
    if "hy_oas_proxy" not in internal_oas.columns:
        raise ValueError("internal_oas must contain column: hy_oas_proxy")

    internal_oas = internal_oas.copy()
    internal_oas.index = pd.to_datetime(internal_oas.index).to_period("M").to_timestamp()

    macro = macro.merge(
        internal_oas[["hy_oas_proxy"]],
        left_index=True,
        right_index=True,
        how="left",
    )

    # Restrict date range.
    start_date = pd.to_datetime(config["data"]["start_date"])
    end_date = pd.to_datetime(config["data"]["end_date"])

    macro = macro.loc[(macro.index >= start_date) & (macro.index <= end_date)].copy()

    # Fill any remaining macro gaps after alignment.
    macro = macro.ffill()

    # Level changes.
    for col in ["unemployment", "fed_funds", "yield_curve", "vix", "hy_oas_proxy"]:
        macro[f"{col}_chg"] = macro[col].diff()

    # Rolling z-scores.
    for col in ["unemployment", "fed_funds", "yield_curve", "vix", "hy_oas_proxy"]:
        macro[f"{col}_z"] = _rolling_zscore(macro[col], z_window)

    # Useful explicit recession/risk proxy.
    macro["curve_inverted"] = (macro["yield_curve"] < 0).astype(int)

    logger.info(
        "Built macro features from %s to %s with %s rows.",
        macro.index.min().date(),
        macro.index.max().date(),
        len(macro),
    )

    return macro