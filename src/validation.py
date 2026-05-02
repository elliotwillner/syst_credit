import logging

logger = logging.getLogger(__name__)


def validate_bond_data(df):
    required_cols = [
        "Date",
        "ISIN",
        "Ticker",
        "OAS",
        "DTS",
        "OAD",
        "Yield_To_Worst",
        "Excess_Return_MTD",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df["Date"].isnull().any():
        raise ValueError("Null values found in Date column")

    dupes = df.duplicated(subset=["Date", "ISIN"]).sum()
    if dupes > 0:
        logger.warning("Found %s duplicate (Date, ISIN) rows", dupes)

    logger.info("Bond data validation passed.")