from src.features.credit_features import build_internal_oas_proxy
from src.features.macro_features import build_macro_features
from src.signals.regime import build_regime_signal
from src.signals.bond_signal import build_bond_signal


def test_signal_pipeline_creates_regime_and_bond_scores(sample_bond_data, sample_config):
    internal_oas = build_internal_oas_proxy(
        sample_bond_data,
        method=sample_config["features"]["oas_proxy_method"],
        z_window=sample_config["features"]["z_window"],
    )

    macro = build_macro_features(sample_config, internal_oas)
    regime = build_regime_signal(macro, sample_config)
    signal_df = build_bond_signal(sample_bond_data, regime, sample_config)

    assert "hy_oas_proxy" in internal_oas.columns
    assert "regime_score" in regime.columns
    assert "regime" in regime.columns
    assert "signal_score" in signal_df.columns
    assert "next_excess_return" in signal_df.columns
    assert signal_df["signal_score"].notna().all()