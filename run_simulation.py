"""Run HumanLifeSim without the dashboard and export CSV results."""
import argparse
from pathlib import Path

from humanlifesim.experiment import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the HumanLifeSim agent-based experiment.")
    parser.add_argument("--population", type=int, default=10_000)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--runs", type=int, default=20, help="Monte Carlo runs per scenario (2–100)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    replicates, bands, trajectories = run_experiment(
        population_size=args.population, years=args.years,
        replications=args.runs, seed=args.seed,
    )
    replicates.to_csv(args.output / "simulation_runs.csv", index=False)
    bands.to_csv(args.output / "forecast_bands.csv", index=False)
    trajectories.to_csv(args.output / "life_trajectories.csv", index=False)
    print(f"Finished {args.runs} runs per scenario.")
    print(f"CSV files written to: {args.output.resolve()}")
    print("\nBaseline forecast:")
    print(bands[bands["scenario"] == "Baseline"][[
        "year", "population_median", "employment_rate_median",
        "median_income_median", "mean_happiness_median"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
