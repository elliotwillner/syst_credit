from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


def _ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_wealth_index(
    backtest: pd.DataFrame,
    output_dir: str | Path = "outputs/charts",
) -> Path:
    output_dir = _ensure_dir(output_dir)
    output_path = output_dir / "wealth_index.png"

    fig, ax = plt.subplots(figsize=(10, 5))
    backtest["wealth_index"].plot(ax=ax)
    ax.set_title("Strategy Wealth Index")
    ax.set_xlabel("Date")
    ax.set_ylabel("Wealth Index")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Saved wealth index chart to %s", output_path)
    return output_path


def plot_drawdown(
    backtest: pd.DataFrame,
    output_dir: str | Path = "outputs/charts",
) -> Path:
    output_dir = _ensure_dir(output_dir)
    output_path = output_dir / "drawdown.png"

    fig, ax = plt.subplots(figsize=(10, 5))
    backtest["drawdown"].plot(ax=ax)
    ax.set_title("Strategy Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Saved drawdown chart to %s", output_path)
    return output_path


def plot_turnover(
    turnover: pd.DataFrame,
    output_dir: str | Path = "outputs/charts",
) -> Path:
    output_dir = _ensure_dir(output_dir)
    output_path = output_dir / "turnover.png"

    fig, ax = plt.subplots(figsize=(10, 5))
    turnover["turnover"].plot(ax=ax)
    ax.set_title("Monthly Portfolio Turnover")
    ax.set_xlabel("Date")
    ax.set_ylabel("Turnover")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Saved turnover chart to %s", output_path)
    return output_path


def plot_portfolio_exposures(
    exposures: pd.DataFrame,
    output_dir: str | Path = "outputs/charts",
) -> Path:
    output_dir = _ensure_dir(output_dir)
    output_path = output_dir / "portfolio_exposures.png"

    exposures = exposures.copy()
    exposures["Date"] = pd.to_datetime(exposures["Date"])
    exposures = exposures.set_index("Date")

    cols = ["avg_oas", "avg_dts", "avg_oad", "ccc_weight"]
    cols = [c for c in cols if c in exposures.columns]

    fig, ax = plt.subplots(figsize=(10, 5))
    exposures[cols].plot(ax=ax)
    ax.set_title("Portfolio Exposure Diagnostics")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Saved exposure chart to %s", output_path)
    return output_path


def plot_regime_score(
    regime: pd.DataFrame,
    output_dir: str | Path = "outputs/charts",
) -> Path:
    output_dir = _ensure_dir(output_dir)
    output_path = output_dir / "regime_score.png"

    fig, ax = plt.subplots(figsize=(10, 5))
    regime["regime_score"].plot(ax=ax)
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_title("Macro Regime Score")
    ax.set_xlabel("Date")
    ax.set_ylabel("Regime Score")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Saved regime score chart to %s", output_path)
    return output_path


def save_all_plots(
    backtest,
    turnover,
    exposures,
    regime,
    output_dir="outputs/charts",
) -> None:
    plot_wealth_index(backtest, output_dir)
    plot_drawdown(backtest, output_dir)
    plot_turnover(turnover, output_dir)
    plot_portfolio_exposures(exposures, output_dir)
    plot_regime_score(regime, output_dir)