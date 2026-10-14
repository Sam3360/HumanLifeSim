"""Monte Carlo scenario comparison and forecast intervals."""
from __future__ import annotations

import pandas as pd

from .model import SCENARIOS, simulate

FORECAST_METRICS = [
    "population", "employment_rate", "unemployment_rate", "median_income",
    "mean_happiness", "mean_health", "poverty_rate", "gini_income",
]


def run_experiment(
    population_size: int = 10_000,
    years: int = 5,
    replications: int = 20,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return aggregate replicate data, confidence bands, and sample trajectories.

    The 5th–95th percentile interval describes variation between model runs;
    it is not a real-world statistical confidence interval.
    """
    if replications < 2 or replications > 100:
        raise ValueError("replications must be between 2 and 100")

    replicate_rows: list[pd.DataFrame] = []
    for scenario_index, scenario_name in enumerate(SCENARIOS):
        for replication in range(replications):
            run_seed = seed + scenario_index * 1_000_003 + replication * 9_176
            metrics, _ = simulate(
                seed=run_seed,
                population_size=population_size,
                years=years,
                scenario_name=scenario_name,
                track_agents=0,
            )
            metrics["scenario"] = scenario_name
            metrics["replication"] = replication
            replicate_rows.append(metrics)

    replicates = pd.concat(replicate_rows, ignore_index=True)
    grouped = replicates.groupby(["scenario", "year"])[FORECAST_METRICS]
    medians = grouped.median().add_suffix("_median")
    lows = grouped.quantile(0.05).add_suffix("_p05")
    highs = grouped.quantile(0.95).add_suffix("_p95")
    bands = pd.concat([medians, lows, highs], axis=1).reset_index()

    # Individual sample paths for the baseline scenario are illustrative, not representative.
    _, trajectories = simulate(
        seed=seed,
        population_size=population_size,
        years=years,
        scenario_name="Baseline",
        track_agents=12,
    )
    return replicates, bands, trajectories
