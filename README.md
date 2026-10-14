# HumanLifeSim

HumanLifeSim is a small agent-based modeling project that simulates a **fictional society** of 10,000 virtual people and explores how individual-level changes can affect population-wide trends over five years.

It includes an interactive Streamlit dashboard, Monte Carlo scenario comparisons, sample individual life trajectories, and CSV exports.

> **Important:** This is an educational toy model, not a calibrated demographic or economic model. Its numbers are generated from explicit illustrative assumptions. The five-year outputs are scenario experiments, not predictions about any real country or person.

## Features

- 10,000 virtual agents by default, with age, education, employment, income, savings, health and happiness attributes.
- Annual aging, births, deaths, education changes, job transitions, income changes, and health/happiness changes.
- Three editable-in-code scenarios: Baseline, Growth and Downturn.
- Reproducible runs using a fixed random seed.
- Monte Carlo repetitions and 5th–95th percentile forecast bands.
- Interactive Plotly charts for population, employment, income, health, happiness and inequality.
- Sample individual trajectories for 12 initially selected agents.
- CSV downloads for forecast bands, individual trajectories and all simulation runs.
- A command-line runner and automated tests.

## Requirements

- Python 3.10 or newer
- Internet access for the initial installation of Python packages only
- No external dataset is downloaded or required

## Quick start (Windows PowerShell)

```powershell
cd HumanLifeSim
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The dashboard should open in your browser. If `streamlit` is not found, use:

```powershell
python -m streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

## Run without the dashboard

```bash
python run_simulation.py
```

Customize the run:

```bash
python run_simulation.py --population 10000 --years 5 --runs 20 --seed 42
```

The CLI writes three files into `outputs/`:

- `simulation_runs.csv`
- `forecast_bands.csv`
- `life_trajectories.csv`

## Run tests

```bash
python -m pytest
```

## How it works

Each simulation starts from a randomly generated synthetic population. Each year, the model applies simplified rules for aging, mortality, births, education, employment, income, savings, health and happiness. These rules are intentionally transparent and can be changed in `humanlifesim/model.py`.

For every scenario, the experiment runs multiple independent simulations. For each year and metric it reports the median and the 5th and 95th percentiles across runs. Those percentile bands express **variation within this toy model**; they are not statistical confidence intervals for real-world outcomes.

### Scenario definitions

| Scenario | Illustrative changes |
|---|---|
| Baseline | 2.5% annual wage-growth assumption; baseline job, birth and mortality settings |
| Growth | More job-finding, 4.5% wage-growth assumption, slightly higher birth multiplier and lower mortality multiplier |
| Downturn | Fewer job-finding opportunities, 0.5% wage-growth assumption, slightly lower birth multiplier and higher mortality multiplier |

These are scenario knobs, not empirically validated estimates. No country, currency or real-world population is represented.

## Metrics

- Population size
- Employment rate among working-age agents
- Simplified unemployment rate
- Median positive annual income in abstract model units
- Mean happiness and health scores (0–100)
- Low-income share (positive income below 15,000 model units)
- Income Gini coefficient

The income metric uses abstract model units; it is not INR, USD or any other currency. Health and happiness are invented simulation scores, not clinical measures.

## Limitations

- The model is not calibrated to census, labour-market, mortality or fertility data.
- It omits migration, public policy, household structure, regional variation, pandemics, education costs and many other factors.
- Births are generated using a simplified count of virtual agents in a reproductive-age group.
- The displayed sample of 12 lives is illustrative and is not a representative sample.
- Scenario ranges do not account for uncertainty in the model design or its assumptions.
- Do not use this model for decisions about real people, health, employment, public policy or financial outcomes.

## Project structure

```text
HumanLifeSim/
├── app.py
├── run_simulation.py
├── requirements.txt
├── pyproject.toml
├── humanlifesim/
│   ├── __init__.py
│   ├── model.py
│   ├── experiment.py
│   └── cli.py
└── tests/
    └── test_model.py
```

## License

MIT — see `LICENSE`.
