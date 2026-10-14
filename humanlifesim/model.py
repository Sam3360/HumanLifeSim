"""Vectorized agent-based simulation of a fictional human society.

All values and transition rates are illustrative model assumptions, not
empirical estimates about any real country or person.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

ScenarioName = Literal["Baseline", "Growth", "Downturn"]


@dataclass(frozen=True)
class Scenario:
    name: ScenarioName
    employment_shift: float
    wage_growth: float
    fertility_multiplier: float
    mortality_multiplier: float
    description: str


SCENARIOS: dict[str, Scenario] = {
    "Baseline": Scenario(
        "Baseline", employment_shift=0.0, wage_growth=0.025,
        fertility_multiplier=1.0, mortality_multiplier=1.0,
        description="Starting assumptions continue without a deliberate shock.",
    ),
    "Growth": Scenario(
        "Growth", employment_shift=0.035, wage_growth=0.045,
        fertility_multiplier=1.03, mortality_multiplier=0.98,
        description="More job openings and faster wage growth; slightly lower mortality.",
    ),
    "Downturn": Scenario(
        "Downturn", employment_shift=-0.055, wage_growth=0.005,
        fertility_multiplier=0.94, mortality_multiplier=1.03,
        description="Fewer job openings, slower wage growth, and slightly higher mortality.",
    ),
}

METRIC_LABELS = {
    "population": "Population",
    "employment_rate": "Employment rate",
    "unemployment_rate": "Unemployment rate",
    "median_income": "Median annual income (model units)",
    "mean_happiness": "Mean happiness (0–100)",
    "mean_health": "Mean health (0–100)",
    "poverty_rate": "Low-income share",
    "gini_income": "Income inequality (Gini)",
}


def _gini(values: np.ndarray) -> float:
    """Gini coefficient for non-negative values; returns 0 for an empty/zero set."""
    values = np.asarray(values, dtype=float)
    if values.size == 0 or np.all(values <= 0):
        return 0.0
    values = np.clip(values, 0, None)
    total = values.sum()
    if total <= 0:
        return 0.0
    sorted_values = np.sort(values)
    n = len(sorted_values)
    ranks = np.arange(1, n + 1)
    return float((2 * np.sum(ranks * sorted_values) / (n * total)) - (n + 1) / n)


def _initial_population(rng: np.random.Generator, size: int) -> dict[str, np.ndarray]:
    """Create a fictional starting population with a broad age distribution."""
    age = np.clip(rng.gamma(shape=3.2, scale=13.5, size=size), 0, 92).astype(int)
    sex = rng.integers(0, 2, size=size)  # 0/1 used only for a simplified birth model

    # Education levels: 0 basic, 1 secondary, 2 further, 3 higher.
    education = np.zeros(size, dtype=np.int8)
    education[(age >= 15) & (rng.random(size) < 0.72)] = 1
    education[(age >= 18) & (rng.random(size) < 0.52)] = 2
    education[(age >= 22) & (rng.random(size) < 0.30)] = 3
    education[age < 6] = 0

    working_age = (age >= 18) & (age < 66)
    work_probability = np.clip(
        0.48 + education * 0.09 - np.maximum(age - 58, 0) * 0.012, 0.05, 0.92
    )
    employed = working_age & (rng.random(size) < work_probability)

    income = np.zeros(size, dtype=float)
    income[employed] = np.maximum(
        7000,
        17000 + education[employed].astype(float) * 6500
        + np.minimum(age[employed], 55) * 260
        + rng.normal(0, 6500, employed.sum()),
    )
    savings = np.maximum(0, income * rng.lognormal(mean=-0.1, sigma=0.8, size=size) * 0.35)
    health = np.clip(96 - age * 0.38 + rng.normal(0, 8, size), 15, 100)
    happiness = np.clip(
        61 + employed.astype(float) * 5 + education * 1.2
        - np.maximum(age - 70, 0) * 0.12 + rng.normal(0, 11, size),
        0, 100,
    )
    return {
        "id": np.arange(1, size + 1, dtype=np.int64),
        "age": age,
        "sex": sex,
        "education": education,
        "employed": employed,
        "income": income,
        "savings": savings,
        "health": health,
        "happiness": happiness,
    }


def _metrics(pop: dict[str, np.ndarray], year: int) -> dict[str, float | int]:
    age = pop["age"]
    employed = pop["employed"]
    income = pop["income"]
    health = pop["health"]
    happiness = pop["happiness"]
    working_age = (age >= 18) & (age < 66)
    labour_force = working_age & (employed | (income == 0))
    labour_count = int(labour_force.sum())
    employed_count = int((working_age & employed).sum())
    unemployed_count = max(0, labour_count - employed_count)
    working_income = income[income > 0]
    return {
        "year": year,
        "population": int(len(age)),
        "employment_rate": float(employed_count / max(1, int(working_age.sum())) * 100),
        "unemployment_rate": float(unemployed_count / max(1, labour_count) * 100),
        "median_income": float(np.median(working_income)) if working_income.size else 0.0,
        "mean_happiness": float(np.mean(happiness)) if len(happiness) else 0.0,
        "mean_health": float(np.mean(health)) if len(health) else 0.0,
        "poverty_rate": float(np.mean((income > 0) & (income < 15000)) * 100) if len(income) else 0.0,
        "gini_income": _gini(income),
    }


def _append_newborns(pop: dict[str, np.ndarray], count: int, next_id: int,
                     rng: np.random.Generator) -> tuple[dict[str, np.ndarray], int]:
    if count <= 0:
        return pop, next_id
    new = {
        "id": np.arange(next_id, next_id + count, dtype=np.int64),
        "age": np.zeros(count, dtype=np.int16),
        "sex": rng.integers(0, 2, size=count),
        "education": np.zeros(count, dtype=np.int8),
        "employed": np.zeros(count, dtype=bool),
        "income": np.zeros(count, dtype=float),
        "savings": np.zeros(count, dtype=float),
        "health": np.clip(rng.normal(97, 2.0, count), 85, 100),
        "happiness": np.clip(rng.normal(65, 7.0, count), 0, 100),
    }
    combined = {key: np.concatenate([pop[key], new[key]]) for key in pop}
    return combined, next_id + count


def simulate(
    seed: int = 42,
    population_size: int = 10_000,
    years: int = 5,
    scenario_name: ScenarioName = "Baseline",
    track_agents: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run one simulation and return yearly metrics and sample life trajectories."""
    if population_size < 100:
        raise ValueError("population_size must be at least 100")
    if years < 1 or years > 30:
        raise ValueError("years must be between 1 and 30")
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    rng = np.random.default_rng(seed)
    scenario = SCENARIOS[scenario_name]
    pop = _initial_population(rng, population_size)
    tracked_ids = set(range(1, min(track_agents, population_size) + 1))
    trajectories: list[dict] = []
    metric_rows: list[dict] = []
    next_id = population_size + 1

    def record_trajectories(year: int) -> None:
        tracked = pop["id"]
        for agent_id in tracked_ids:
            indexes = np.flatnonzero(tracked == agent_id)
            if indexes.size:
                i = int(indexes[0])
                trajectories.append({
                    "year": year, "agent_id": agent_id,
                    "age": int(pop["age"][i]),
                    "income": float(pop["income"][i]),
                    "happiness": float(pop["happiness"][i]),
                    "health": float(pop["health"][i]),
                    "employed": bool(pop["employed"][i]),
                    "education": int(pop["education"][i]),
                    "status": "Alive",
                })
            else:
                # Keep the line visible as a deceased marker in the trajectory table.
                trajectories.append({
                    "year": year, "agent_id": agent_id, "age": np.nan,
                    "income": np.nan, "happiness": np.nan, "health": np.nan,
                    "employed": False, "education": np.nan, "status": "Died",
                })

    metric_rows.append(_metrics(pop, 0))
    record_trajectories(0)

    for year in range(1, years + 1):
        age = pop["age"]
        age += 1

        # Mortality is a toy age-dependent probability, not a life-expectancy model.
        mortality = 0.0008 + np.maximum(age - 35, 0) ** 2 * 0.000012
        mortality = np.clip(mortality * scenario.mortality_multiplier, 0.0002, 0.25)
        died = rng.random(len(age)) < mortality
        female_reproductive = (pop["sex"] == 1) & (age >= 20) & (age <= 40) & ~died
        births = int(rng.poisson(female_reproductive.sum() * 0.045 * scenario.fertility_multiplier))

        survivors = ~died
        pop = {key: values[survivors] for key, values in pop.items()}

        # Education can advance for some young adults still in education.
        can_study = (pop["age"] >= 16) & (pop["age"] <= 25) & (pop["education"] < 3)
        study_probability = np.where(pop["age"] < 20, 0.20, 0.10)
        study = can_study & (rng.random(len(pop["age"])) < study_probability)
        pop["education"][study] += 1

        age = pop["age"]
        working_age = (age >= 18) & (age < 66)
        employed = pop["employed"].copy()

        # Annual job transitions.
        job_loss_probability = np.clip(0.035 - scenario.employment_shift * 0.20, 0.01, 0.12)
        loses_job = employed & (rng.random(len(age)) < job_loss_probability)
        employed[loses_job] = False
        seeking = working_age & ~employed
        find_probability = np.clip(
            0.30 + pop["education"] * 0.055 + scenario.employment_shift, 0.04, 0.75
        )
        finds_job = seeking & (rng.random(len(age)) < find_probability)
        employed[finds_job] = True
        employed[~working_age] = False
        pop["employed"] = employed

        # Income is annual model currency, not a real-world currency forecast.
        education = pop["education"]
        target_income = np.maximum(
            7000,
            17000 + education.astype(float) * 6500 + np.minimum(age, 55) * 260
            + rng.normal(0, 6500, len(age)),
        )
        prior_income = pop["income"]
        income = np.where(employed, np.maximum(target_income, prior_income * (1 + scenario.wage_growth)), 0.0)
        income *= np.where(employed, 1 + rng.normal(scenario.wage_growth, 0.035, len(age)), 1.0)
        pop["income"] = np.clip(income, 0, 500_000)

        living_cost = np.where(employed, pop["income"] * 0.72, 9000.0)
        pop["savings"] = np.clip(pop["savings"] + pop["income"] - living_cost, 0, 5_000_000)

        health_change = rng.normal(-0.15, 1.6, len(age)) - np.maximum(age - 55, 0) * 0.035
        health_change += np.where(employed, 0.08, -0.18)
        pop["health"] = np.clip(pop["health"] + health_change, 0, 100)

        income_signal = np.clip((pop["income"] - 18000) / 30000, -1, 1)
        happiness_change = (
            np.where(employed, 0.45, -0.65)
            + income_signal * 0.65
            + (pop["health"] - 60) * 0.012
            + rng.normal(0, 2.4, len(age))
        )
        pop["happiness"] = np.clip(pop["happiness"] + happiness_change, 0, 100)

        pop, next_id = _append_newborns(pop, births, next_id, rng)
        metric_rows.append(_metrics(pop, year))
        record_trajectories(year)

    return pd.DataFrame(metric_rows), pd.DataFrame(trajectories)
