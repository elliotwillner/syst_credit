from pathlib import Path
import pandas as pd


def load_bond_data(config: dict) -> pd.DataFrame:
    p1 = Path(config["paths"]["raw_bond_part_1"])
    p2 = Path(config["paths"]["raw_bond_part_2"])

    df1 = pd.read_csv(p1)
    df2 = pd.read_csv(p2)

    df = pd.concat([df1, df2], ignore_index=True)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Date", "ISIN"])

    logger.info("Loaded %s rows of bond data", len(df))
    return df