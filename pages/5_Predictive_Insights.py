"""
Page 5: Predictive Insights — ML-Powered Forecasting & What-If Scenarios
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from data.sample_data import generate_opportunities
from utils.traffic_light import traffic_light_badge, get_status, correlation_badge
from utils.metrics import format_currency

st.set_page_config(page_title="Predictive Insights", page_icon="\U0001F52E", layout="wide")

@st.cache_data
def load_data():
    return generate_opportunities(n=150)

df = load_data()
regions = st.session_state.get("selected_regions", df["region"].unique().tolist())
df = df[df["region"].isin(regions)]
active = df[~df["stage"].isin(["Closed Won", "Closed Lost"])]

st.markdown("# Predictive Insights")
st.markdown("ML-powered forecasting and what-if scenario modeling.")
st.markdown("---")

# --- WHAT-IF SIMULATOR ---
st.markdown("## What-If Scenario Simulator")
st.markdown("Adjust enablement investment to see projected revenue impact.")

w1, w2, w3 = st.columns(3)
with w1:
    enablement_boost = st.slider("Enablement Score Boost (+pts)", 0, 30, 10)
with w2:
    genai_boost = st.slider("GenAI Readiness Boost (+pts)", 0, 30, 10)
with w3:
    target_region = st.selectbox("Target Region", ["All"] + sorted(df["region"].unique().tolist()))

# Apply scenario
if target_region == "All":
    scenario_df = active.copy()
else:
    scenario_df = active[active["region"] == target_region].copy()

if len(scenario_df) > 0:
    baseline_wr = scenario_df["win_probability"].mean()
    baseline_pipeline = scenario_df["deal_value_usd"].sum()
    baseline_velocity = scenario_df["velocity_weekly_usd"].sum()

    # Model: each enablement point = ~0.55% win rate lift (from correlation)
    projected_wr = np.clip(baseline_wr + enablement_boost * 0.55 + genai_boost * 0.38, 0, 95)
    wr_lift = projected_wr - baseline_wr
    revenue_lift = baseline_pipeline * (wr_lift / 100)
    cycle_reduction = enablement_boost * 0.8 + genai_boost * 0.5

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Projected Win Rate", "{:.1f}%".format(projected_wr),
              "+{:.1f}%".format(wr_lift))
    r2.metric("Revenue Uplift", format_currency(revenue_lift),
              "+{:.1f}%".format(wr_lift))
    r3.metric("Cycle Reduction", "-{:.0f} days".format(cycle_reduction))
    r4.metric("Deals Impacted", "{}".format(len(scenario_df)))

    st.markdown("---")

    # --- FORECAST VISUALIZATION ---
    st.markdown("## Revenue Forecast: Baseline vs Scenario")
    weeks = list(range(1, 13))
    baseline_rev = [baseline_pipeline * (baseline_wr / 100) * (w / 12) for w in weeks]
    scenario_rev = [baseline_pipeline * (projected_wr / 100) * (w / 12) for w in weeks]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weeks, y=baseline_rev, mode="lines+markers",
        name="Baseline", line=dict(color="#8B949E", dash="dash")))
    fig.add_trace(go.Scatter(
        x=weeks, y=scenario_rev, mode="lines+markers",
        name="With Enablement Boost", line=dict(color="#FF9900")))
    fig.add_trace(go.Scatter(
        x=weeks, y=[s - b for s, b in zip(scenario_rev, baseline_rev)],
        mode="lines", name="Incremental Lift",
        line=dict(color="#69F0AE", dash="dot")))
    fig.update_layout(
        paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
        font=dict(color="#F0F6FC"), height=400,
        xaxis=dict(title="Weeks", gridcolor="#30363D"),
        yaxis=dict(title="Cumulative Revenue ($)", gridcolor="#30363D"),
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- FEATURE IMPORTANCE ---
st.markdown("## Win Probability Drivers (Feature Importance)")
if len(df) > 20:
    features = ["enablement_score", "genai_readiness", "meddpicc_avg",
                "training_hours_30d", "cert_numeric", "days_since_last_activity"]
    feature_labels = ["Enablement Score", "GenAI Readiness", "MEDDPICC Avg",
                      "Training Hours (30d)", "Certification Level", "Days Since Activity"]

    X = df[features].fillna(0).values
    y = df["win_probability"].values

    model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X, y)
    importances = model.feature_importances_

    imp_df = pd.DataFrame({
        "Feature": feature_labels,
        "Importance": importances
    }).sort_values("Importance", ascending=True)

    fig2 = px.bar(
        imp_df, x="Importance", y="Feature", orientation="h",
        color="Importance", color_continuous_scale=["#30363D", "#FF9900"]
    )
    fig2.update_layout(
        paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
        font=dict(color="#F0F6FC"), height=350,
        xaxis=dict(title="Relative Importance", gridcolor="#30363D"),
        yaxis=dict(title="", gridcolor="#30363D"),
        showlegend=False
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# --- RISK PREDICTION ---
st.markdown("## At-Risk Deal Predictions")
if len(active) > 0:
    high_risk = active[active["risk_flag"] == "High"].sort_values(
        "deal_value_usd", ascending=False).head(10)

    if len(high_risk) > 0:
        st.markdown("**{} high-risk deals** totaling **{}** require immediate attention:".format(
            len(active[active["risk_flag"] == "High"]),
            format_currency(active[active["risk_flag"] == "High"]["deal_value_usd"].sum())))

        st.dataframe(
            high_risk[["opportunity_id", "region", "stage", "deal_value_usd",
                       "win_probability", "enablement_score", "days_since_last_activity",
                       "competitor_present", "aging_status"]],
            use_container_width=True, hide_index=True,
            column_config={
                "deal_value_usd": st.column_config.NumberColumn("Deal Value", format="$%d"),
                "win_probability": st.column_config.ProgressColumn("Win %", min_value=0, max_value=100),
                "enablement_score": st.column_config.ProgressColumn("Enablement", min_value=0, max_value=100),
            }
        )
    else:
        st.success("No high-risk deals in current selection.")
