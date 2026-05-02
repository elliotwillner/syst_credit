from src.features.credit_features import build_internal_oas_proxy
from src.features.macro_features import build_macro_features
from src.signals.regime import build_regime_signal
from src.signals.bond_signal import build_bond_signal
from src.portfolio.construction import build_portfolio
from src.portfolio.backtest import run_backtest
from src.evaluation.metrics import combine_metrics


def test_portfolio_backtest_outputs_are_valid(sample_bond_data, sample_config):
    internal_oas = build_internal_oas_proxy(
        sample_bond_data,
        method=sample_config["features"]["oas_proxy_method"],
        z_window=sample_config["features"]["z_window"],
    )
    macro = build_macro_features(sample_config, internal_oas)
    regime = build_regime_signal(macro, sample_config)
    signal_df = build_bond_signal(sample_bond_data, regime, sample_config)

    portfolio = build_portfolio(signal_df, sample_config)
    backtest = run_backtest(portfolio)
    metrics = combine_metrics(backtest, portfolio)

    weight_sums = portfolio.groupby("Date")["target_weight"].sum()

    assert weight_sums.between(0.9999, 1.0001).all()
    assert (portfolio["target_weight"] >= 0).all()

    assert "portfolio_excess_return" in backtest.columns
    assert "wealth_index" in backtest.columns
    assert "drawdown" in backtest.columns

    assert "sharpe_ratio" in metrics.index
    assert "max_drawdown" in metrics.index