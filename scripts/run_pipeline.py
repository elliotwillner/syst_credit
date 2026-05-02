import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.data_loader import load_bond_data
from src.validation import validate_bond_data
from src.features.credit_features import build_internal_oas_proxy
from src.features.macro_features import build_macro_features
from src.signals.regime import build_regime_signal
from src.signals.bond_signal import build_bond_signal
from src.portfolio.construction import build_portfolio
from src.portfolio.backtest import run_backtest
from src.evaluation.metrics import combine_metrics
from src.utils.logging import setup_logging
import logging

logger = logging.getLogger(__name__)


def main(config_path: str):
    setup_logging()
    config = load_config(config_path)

    # 1. Load + clean bonds
    df = load_bond_data(config)
    validate_bond_data(df)

    # 2. Credit features
    oas_proxy = build_internal_oas_proxy(df)

    # 3. Macro
    macro = build_macro_features(config, oas_proxy)

    # 4. Regime
    regime = build_regime_signal(macro, config)

    # 5. Bond signal
    df = build_bond_signal(df, regime, config)

    # 6. Portfolio
    portfolio = build_portfolio(df, config)

    # 7. Backtest
    results = run_backtest(portfolio)

    # 8. Metrics
    metrics = combine_metrics(results, portfolio)

    # 9. Save outputs
    results.to_csv("outputs/results.csv")
    metrics.to_csv("outputs/metrics.csv")

    logger.info("Saved results to outputs/results.csv")
    logger.info("Saved metrics to outputs/metrics.csv")

if __name__ == "__main__":
    main("config/base.yaml")