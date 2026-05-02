# Systematic Credit Mini-Pipeline

Elliot Willner

## Overview

This project implements a reproducible, research pipeline for a simple systematic credit strategy using US High Yield bond data and macroeconomic indicators.

The goal is not to build an optimal strategy, but to demonstrate clean engineering design, modular code structure, and production-minded workflow that can be extended into a live systematic process.

---

## Key Features

- End-to-end pipeline from raw data → signal → portfolio → backtest → metrics
- Modular design with clear separation of responsibilities
- Config-driven parameters (no hardcoding)
- Logging and validation for robustness
- Lightweight unit tests for critical components
- Saved outputs (results, metrics, charts)

---

## Project Structure

```
syst_credit/
│
├── config/
│   └── base.yaml                  # All model + pipeline parameters
│
├── data/
│   └── raw/                       # Input bond + macro data
│
├── src/
│   ├── data_loader.py             # Load bond data
│   ├── validation.py              # Data integrity checks
│   ├── config.py                  # Config setup
│   ├── features/
│   │   ├── credit_features.py     # Internal OAS proxy
│   │   └── macro_features.py      # Macro feature construction
│   ├── signals/
│   │   ├── regime.py              # Macro regime classification
│   │   └── bond_signal.py         # Bond-level scoring
│   ├── portfolio/
│   │   ├── construction.py        # Portfolio building + constraints
│   │   └── backtest.py            # Return simulation
│   ├── evaluation/
│   │   ├── metrics.py             # Performance metrics
│   │   └── plots.py               # Chart generation
│   └── utils/
│       └── logging.py             # Logging setup
│
├── scripts/
│   └── run_pipeline.py            # Main entry point
│
├── tests/                         # Unit tests (pytest)
├── outputs/                       # Results, metrics, charts
├── requirements.txt
└── README.md
```

---

## How to Run

### 1. In the virtual environment you'd like to run in, install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the pipeline

```bash
python scripts/run_pipeline.py
```

This will:
- Load and validate data
- Build credit + macro features
- Construct regime-aware bond signals
- Build a constrained portfolio
- Run a backtest
- Save outputs to `/outputs`

---

### 3. Run tests

```bash
pytest -q
```

Tests cover:
- Data validation
- Signal pipeline
- Portfolio construction + backtest outputs

---

## Data

- **Bond data**: US High Yield index constituents (provided)
- **Macro data (FRED)**:
  - Unemployment rate
  - Fed Funds rate
  - 10y–2y yield curve slope
  - VIX

Because full HY index OAS is not freely available over the full time period, an internal OAS proxy is constructed from the dataset.

---

## Methodology

### 1. Credit Signal

The signal ranks bonds based on:

```
signal = YTW + OAS − DTS − duration − CCC penalty
```

Interpretation:
- Favor high yield and spread (compensation)
- Penalize duration and spread risk
- Penalize lowest-quality credit (CCC)

This is a **carry vs risk framework**, not a predictive model.

---

### 2. Macro Regime

A regime score is constructed using:

- Unemployment (↑ risk)
- VIX (↑ risk)
- HY OAS proxy (↑ risk)
- Yield curve slope (↓ risk)

Rolling z-scores are computed over a 36-month window:

> The 36-month window balances stability and responsiveness and is treated as a configurable model parameter.

Regimes:
- Risk-on
- Neutral
- Risk-off

The first 36 months are treated as a warm-up period and excluded from signal usage.

---

### 3. Portfolio Construction

- Long-only portfolio
- Monthly rebalancing
- Select **top X% of bonds** by signal

Why top %:

> The universe size varies over time, so percentile selection ensures consistent portfolio selectivity.

#### Constraints

- Issuer cap
- Sector cap
- CCC exposure cap

Sector considerations:

> The sample HY universe is structurally ~85–90% Industrials, so constraints focus more on issuer and credit risk rather than forcing artificial sector diversification.

---

### 4. Backtest

- Uses **next-month excess returns**
- Produces:
  - Wealth index
  - Drawdown
  - Monthly returns

---

### 5. Metrics

- Annualized return
- Volatility
- Sharpe ratio
- Max drawdown
- Hit rate
- Turnover

---

## Results & Interpretation

The Sharpe ratio is modest.

This is expected because:
- The signal is intentionally simple
- It ranks carry vs risk rather than forecasting returns
- Excess returns are inherently noisy

> The framework is designed to be extensible. Improvements such as signal weighting, regime-based exposure scaling, and additional features would likely improve performance.

---

## Failure Modes

1. **Macro regime lag**
   - Rolling normalization introduces delay
   - Detection: regime instability or rapid reversals

2. **Liquidity / turnover risk**
   - High turnover may be infeasible in practice
   - Detection: spikes in turnover or concentration shifts

---

## Design Principles

- **Separation of concerns**: each module has a single responsibility
- **Reproducibility**: one command rebuilds everything
- **Config-driven**: parameters easily adjustable
- **Robustness**: validation + logging
- **Testability**: core components covered by unit tests

---

## Future Improvements

- Replace internal OAS proxy with benchmark HY index OAS
- Add signal weighting (not equal weight)
- Incorporate transaction costs
- Add regime-based exposure scaling
- Introduce sector-relative value signals

---

## Outputs

Saved to `/outputs`:

- `results.csv` → backtest time series  
- `metrics.csv` → summary statistics  
- charts → wealth, drawdown, regime, exposures  

---

## Summary

This project demonstrates a clean, production-minded research pipeline for systematic credit investing. The emphasis is on **engineering quality, reproducibility, and extensibility**, rather than optimizing strategy performance.
