from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from humanlifesim.experiment import FORECAST_METRICS, run_experiment
from humanlifesim.model import METRIC_LABELS, SCENARIOS

st.set_page_config(
    page_title="HumanLifeSim",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1500px;}
    div[data-testid="stMetric"] {background: rgba(120,120,120,.07); padding: 14px 16px; border-radius: 12px;}
    .small-note {font-size: .9rem; opacity: .8;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("HumanLifeSim")
st.caption("An agent-based experiment in how individual lives can shape society-wide trends.")
st.warning(
    "This is a fictional educational model. Its forecasts are generated from configurable "
    "assumptions, not real-world demographic or economic predictions."
)

with st.sidebar:
    st.header("Simulation controls")
    population = st.slider("Starting population", 1_000, 50_000, 10_000, 1_000)
    years = st.slider("Forecast horizon (years)", 1, 5, 5)
    replications = st.slider("Runs per scenario", 5, 40, 20, 5)
    seed = st.number_input("Random seed", min_value=0, max_value=2_000_000_000, value=42, step=1)
    st.markdown("---")
    st.markdown("**Scenarios**")
    for name, scenario in SCENARIOS.items():
        st.write(f"**{name}** — {scenario.description}")
    run = st.button("Run simulation", type="primary", use_container_width=True)
    st.caption("Same settings + same seed = reproducible results.")

if "results" not in st.session_state:
    st.session_state.results = None

if run or st.session_state.results is None:
    with st.spinner("Simulating virtual lives across scenarios…"):
        st.session_state.results = run_experiment(
            population_size=int(population),
            years=int(years),
            replications=int(replications),
            seed=int(seed),
        )
        st.session_state.settings = (int(population), int(years), int(replications), int(seed))

replicates, bands, trajectories = st.session_state.results
settings = st.session_state.get("settings", (population, years, replications, seed))
if settings != (int(population), int(years), int(replications), int(seed)):
    st.info("Controls changed. Click **Run simulation** to recalculate the charts.")

scenario_names = list(SCENARIOS)
latest_year = int(bands["year"].max())
baseline_latest = bands[(bands["scenario"] == "Baseline") & (bands["year"] == latest_year)].iloc[0]
baseline_start = bands[(bands["scenario"] == "Baseline") & (bands["year"] == 0)].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Starting population", f"{int(baseline_start['population_median']):,}")
c2.metric(
    f"Baseline population · year {latest_year}",
    f"{int(baseline_latest['population_median']):,}",
    f"{int(baseline_latest['population_median'] - baseline_start['population_median']):+,}",
)
c3.metric("Employment rate", f"{baseline_latest['employment_rate_median']:.1f}%")
c4.metric("Mean happiness", f"{baseline_latest['mean_happiness_median']:.1f}/100")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Society overview", "Scenario comparison", "Individual lives", "Data & assumptions"]
)

with tab1:
    st.subheader("How the fictional society changes")
    metric_choice = st.selectbox(
        "Choose a trend",
        options=FORECAST_METRICS,
        format_func=lambda value: METRIC_LABELS[value],
        key="overview_metric",
    )
    chart = go.Figure()
    for scenario_name in scenario_names:
        frame = bands[bands["scenario"] == scenario_name].sort_values("year")
        low = frame[f"{metric_choice}_p05"]
        high = frame[f"{metric_choice}_p95"]
        median = frame[f"{metric_choice}_median"]
        chart.add_trace(go.Scatter(
            x=frame["year"], y=high, mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip", name=f"{scenario_name} upper range",
        ))
        chart.add_trace(go.Scatter(
            x=frame["year"], y=low, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(100, 116, 139, 0.12)",
            showlegend=False, hoverinfo="skip", name=f"{scenario_name} range",
        ))
        chart.add_trace(go.Scatter(
            x=frame["year"], y=median, mode="lines+markers", name=scenario_name,
            line=dict(width=3),
        ))
    chart.update_layout(
        template="plotly_white", height=440,
        xaxis_title="Simulation year (0 = starting point)",
        yaxis_title=METRIC_LABELS[metric_choice],
        legend_title="Scenario", hovermode="x unified",
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(chart, use_container_width=True)
    st.caption(
        "Lines show the median across repeated runs. Shaded bands show the 5th–95th percentile "
        "of model outcomes, not a real-world confidence interval."
    )

    left, right = st.columns(2)
    with left:
        frame = bands[bands["scenario"] == "Baseline"].sort_values("year")
        fig = px.line(frame, x="year", y="employment_rate_median", markers=True,
                      title="Baseline employment rate", labels={"year": "Year", "employment_rate_median": "% employed"})
        fig.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.line(frame, x="year", y="mean_happiness_median", markers=True,
                      title="Baseline mean happiness", labels={"year": "Year", "mean_happiness_median": "Score / 100"})
        fig.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Compare the three futures")
    compare_metric = st.selectbox(
        "Metric to compare",
        options=FORECAST_METRICS,
        format_func=lambda value: METRIC_LABELS[value],
        index=0,
        key="comparison_metric",
    )
    final_rows = bands[bands["year"] == latest_year].copy()
    final_rows = final_rows.sort_values("scenario")
    fig = go.Figure()
    for _, row in final_rows.iterrows():
        name = row["scenario"]
        fig.add_trace(go.Bar(
            name=name,
            x=[name],
            y=[row[f"{compare_metric}_median"]],
            error_y=dict(
                type="data",
                symmetric=False,
                array=[row[f"{compare_metric}_p95"] - row[f"{compare_metric}_median"]],
                arrayminus=[row[f"{compare_metric}_median"] - row[f"{compare_metric}_p05"]],
                visible=True,
            ),
        ))
    fig.update_layout(
        template="plotly_white", height=400, showlegend=False,
        title=f"{METRIC_LABELS[compare_metric]} in year {latest_year}",
        yaxis_title=METRIC_LABELS[compare_metric],
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        final_rows[["scenario"] + [
            f"{compare_metric}_p05", f"{compare_metric}_median", f"{compare_metric}_p95"
        ]].rename(columns={
            "scenario": "Scenario",
            f"{compare_metric}_p05": "5th percentile",
            f"{compare_metric}_median": "Median",
            f"{compare_metric}_p95": "95th percentile",
        }),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("**Scenario assumptions**")
    for name, scenario in SCENARIOS.items():
        st.markdown(f"- **{name}:** {scenario.description}")

with tab3:
    st.subheader("A small sample of individual life trajectories")
    st.caption(
        "These 12 people are selected from the initial population for illustration. "
        "They are not intended to represent every person's experience."
    )
    alive_ids = sorted(trajectories["agent_id"].unique().tolist())
    chosen_metric = st.selectbox(
        "Track an attribute",
        ["happiness", "health", "income", "age"],
        format_func=lambda value: {
            "happiness": "Happiness (0–100)",
            "health": "Health (0–100)",
            "income": "Annual income (model units)",
            "age": "Age",
        }[value],
    )
    chosen_agents = st.multiselect(
        "Agents to display",
        options=alive_ids,
        default=alive_ids[:6],
        format_func=lambda value: f"Person {value}",
    )
    selected = trajectories[trajectories["agent_id"].isin(chosen_agents)]
    if selected.empty:
        st.info("Choose at least one person to display their trajectory.")
    else:
        fig = px.line(
            selected, x="year", y=chosen_metric, color="agent_id", markers=True,
            hover_data=["age", "employed", "education", "status"],
            labels={"year": "Simulation year", chosen_metric: chosen_metric.title(), "agent_id": "Person"},
            title=f"Individual {chosen_metric} trajectories",
        )
        fig.update_layout(template="plotly_white", height=440)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(selected, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Model assumptions and limitations")
    st.markdown(
        """
        - **Population:** starts with a synthetic age distribution and 10,000 agents by default.
        - **Aging:** every surviving person ages by one year per simulated year.
        - **Births and deaths:** use simplified random rates. They are not calibrated to a real population.
        - **Education:** some young agents advance education levels stochastically.
        - **Employment:** working-age agents can lose or find jobs; education and scenario conditions affect transitions.
        - **Income:** generated in abstract model units using education, age, employment and random variation. It is not a currency forecast.
        - **Health and happiness:** bounded 0–100 indicators affected by age, employment, income and random variation. They are invented model scores, not clinical measures.
        - **Inequality:** Gini coefficient is calculated from non-negative model incomes, including zero incomes.
        - **Forecast bands:** percentiles across independent simulations show model variability only. They do not capture every real-world uncertainty.
        - **No personal predictions:** the model cannot predict any real person's future.
        """
    )
    st.subheader("Scenario run data")
    st.dataframe(bands, use_container_width=True, hide_index=True)
    st.download_button(
        "Download forecast bands (CSV)",
        data=bands.to_csv(index=False).encode("utf-8"),
        file_name="humanlifesim_forecast_bands.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download all Monte Carlo runs (CSV)",
        data=replicates.to_csv(index=False).encode("utf-8"),
        file_name="humanlifesim_simulation_runs.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download sample life trajectories (CSV)",
        data=trajectories.to_csv(index=False).encode("utf-8"),
        file_name="humanlifesim_life_trajectories.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption("HumanLifeSim 1.0.0 · Educational simulation · Synthetic agents · Reproducible with a fixed seed")
