import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def sample_bond_data():
    dates = pd.date_range("2010-01-01", periods=24, freq="MS")
    rows = []

    for date in dates:
        for i in range(6):
            rows.append({
                "Date": date,
                "ISIN": f"ISIN{i}",
                "Ticker": f"TICK{i // 2}",
                "Class2": "Industrial" if i < 4 else "Financial_Institutions",
                "Eff_Rating_Group": ["BB", "B", "CCC", "BB", "B", "BB"][i],
                "OAS": 300 + 20 * i + 2 * dates.get_loc(date),
                "DTS": 10 + i,
                "OAD": 3 + 0.1 * i,
                "Yield_To_Worst": 6 + 0.2 * i,
                "Excess_Return_MTD": 0.2 + 0.01 * i,
            })

    return pd.DataFrame(rows)


@pytest.fixture
def sample_config(tmp_path):
    macro_dir = tmp_path / "macro"
    macro_dir.mkdir()

    dates = pd.date_range("2010-01-01", periods=24, freq="MS")

    series_values = {
        "UNRATE.csv": [5.0 + 0.02 * i for i in range(len(dates))],
        "FEDFUNDS.csv": [1.0 + 0.01 * i for i in range(len(dates))],
        "T10Y2Y.csv": [1.5 - 0.01 * i for i in range(len(dates))],
        "VIXCLS.csv": [20.0 + 0.10 * i for i in range(len(dates))],
    }

    for filename, values in series_values.items():
        pd.DataFrame({
            "DATE": dates,
            filename.replace(".csv", ""): values,
        }).to_csv(macro_dir / filename, index=False)

    return {
        "paths": {"raw_macro_dir": str(macro_dir)},
        "data": {
            "start_date": "2010-01-01",
            "end_date": "2011-12-01",
        },
        "features": {
            "oas_proxy_method": "median",
            "z_window": 6,
        },
        "regime": {
            "risk_on_threshold": -0.75,
            "risk_off_threshold": 0.75,
            "weights": {
                "unemployment_z": 0.25,
                "vix_z": 0.25,
                "hy_oas_proxy_z": 0.30,
                "yield_curve_z": -0.20,
            },
        },
        "portfolio": {
            "selection_pct": 0.50,
            "min_bonds": 2,
            "max_issuer_weight": 0.60,
            "max_sector_weight": 0.70,
            "max_ccc_weight": 0.50,
        },
    }