import pandas as pd
import pytest

from humanlifesim.experiment import run_experiment
from humanlifesim.model import SCENARIOS, simulate


def test_simulation_has_start_and_future_years():
    metrics, trajectories = simulate(seed=7, population_size=500, years=5)
    assert metrics["year"].tolist() == [0, 1, 2, 3, 4, 5]
    assert len(metrics) == 6
    assert set(["population", "employment_rate", "mean_happiness"]).issubset(metrics.columns)
    assert trajectories["agent_id"].nunique() == 12


def test_fixed_seed_is_reproducible():
    first, first_paths = simulate(seed=123, population_size=500, years=2)
    second, second_paths = simulate(seed=123, population_size=500, years=2)
    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(first_paths, second_paths)


def test_metrics_are_bounded():
    metrics, _ = simulate(seed=4, population_size=500, years=3)
    assert (metrics["population"] > 0).all()
    assert metrics["employment_rate"].between(0, 100).all()
    assert metrics["unemployment_rate"].between(0, 100).all()
    assert metrics["mean_happiness"].between(0, 100).all()
    assert metrics["mean_health"].between(0, 100).all()
    assert metrics["gini_income"].between(0, 1).all()


def test_all_scenarios_are_available():
    assert set(SCENARIOS) == {"Baseline", "Growth", "Downturn"}
    for name in SCENARIOS:
        metrics, _ = simulate(seed=10, population_size=300, years=1, scenario_name=name)
        assert len(metrics) == 2


def test_experiment_creates_percentile_bands():
    replicates, bands, paths = run_experiment(
        population_size=300, years=2, replications=2, seed=8
    )
    assert set(replicates["scenario"]) == {"Baseline", "Growth", "Downturn"}
    assert set(bands["year"]) == {0, 1, 2}
    assert "population_p05" in bands.columns
    assert "population_p95" in bands.columns
    assert not paths.empty


def test_invalid_parameters_raise_errors():
    with pytest.raises(ValueError):
        simulate(population_size=50)
    with pytest.raises(ValueError):
        simulate(years=0)
