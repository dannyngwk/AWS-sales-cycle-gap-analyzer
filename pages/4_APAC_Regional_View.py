"""
Page 4: APAC Regional View — Geographic Performance Breakdown
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from data.sample_data import generate_opportunities
from utils.traffic_light import traffic_light_badge, get_status, correlation_badge
from utils.metrics import format_currency, calculate_correlation_with_ci

st.set_page_config(page_title="APAC Regional View", page_icon="\U0001F30F", layout="wide")

@st.cache_data
def load_data():
    return generate_opportunities(n=150)

df = load_data()
regions = st.session_state.get("selected_regions", df["region"].unique().tolist())
df = df[df["region"].isin(regions)]

st.markdown("# APAC Regional Performance")
st.markdown("Comparative analysis across {} regions.".format(len(regions)))
st.markdown("---")

# --- REGIONAL SUMMARY TABLE ---
st.markdown("## Regional Scorecard")
regional_stats = df.groupby("region").agg(
    deals=("opportunity_id", "count"),
    pipeline=("deal_value_usd", "sum"),
    avg_win_rate=("win_probability", "mean"),
    avg_enablement=("enablement_score", "mean"),
    avg_genai=("genai_readiness", "mean"),
    avg_meddpicc=("meddpicc_avg", "mean"),
    avg_cycle=("cycle_days_actual", "mean"),
    avg_gap=("gap_days", "mean"),
    high_risk=("risk_flag", lambda x: (x == "High").sum())
).reset_index().sort_values("pipeline", ascending=False)

st.dataframe(
    regional_stats,
    use_container_width=True, hide_index=True,
    column_config={
        "region": "Region",
        "deals": "Deals",
        "pipeline": st.column_config.NumberColumn("Pipeline", format="$%d"),
        "avg_win_rate": st.column_config.NumberColumn("Win Rate %", format="%.1f"),
        "avg_enablement": st.column_config.NumberColumn("Enablement", format="%.1f"),
        "avg_genai": st.column_config.NumberColumn("GenAI Ready", format="%.1f"),
        "avg_meddpicc": st.column_config.NumberColumn("MEDDPICC", format="%.1f"),
        "avg_cycle": st.column_config.NumberColumn("Cycle Days", format="%.0f"),
        "avg_gap": st.column_config.NumberColumn("Gap Days", format="%+.0f"),
        "high_risk": "High Risk",
    }
)

st.markdown("---")

# --- RADAR CHART ---
st.markdown("## Regional Capability Radar")
categories = ["Win Rate", "Enablement", "GenAI", "MEDDPICC", "Velocity"]

fig = go.Figure()
colors = ["#FF9900", "#58A6FF", "#69F0AE", "#9C27B0", "#FFD54F", "#FF6B6B"]

for i, region in enumerate(regional_stats["region"].values[:6]):
    rdf = df[df["region"] == region]
    values = [
        rdf["win_probability"].mean(),
        rdf["enablement_score"].mean(),
        rdf["genai_readiness"].mean(),
        rdf["meddpicc_avg"].mean(),
        rdf["velocity_weekly_usd"].mean() / 1000,
    ]
    # Normalize to 0-100 scale
    max_vals = [100, 100, 100, 100, max(df["velocity_weekly_usd"].mean() / 500, 1)]
    normalized = [min(v / m * 100, 100) for v, m in zip(values, max_vals)]
    normalized.append(normalized[0])  # close the polygon

    fig.add_trace(go.Scatterpolar(
        r=normalized,
        theta=categories + [categories[0]],
        name=region,
        line=dict(color=colors[i % len(colors)])
    ))

fig.update_layout(
    polar=dict(
        bgcolor="#161B22",
        radialaxis=dict(visible=True, range=[0, 100], gridcolor="#30363D"),
        angularaxis=dict(gridcolor="#30363D")
    ),
    paper_bgcolor="#0D1117",
    font=dict(color="#F0F6FC"),
    height=500, showlegend=True
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- REGIONAL GAP ANALYSIS ---
st.markdown("## Cycle Gap by Region")
fig2 = px.bar(
    regional_stats, x="region", y="avg_gap",
    color="avg_enablement",
    color_continuous_scale=["#FF3D00", "#FFB300", "#69F0AE"],
    text="avg_gap"
)
fig2.update_traces(texttemplate="%{text:+.0f}d", textposition="outside")
fig2.update_layout(
    paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
    font=dict(color="#F0F6FC"), height=350,
    xaxis=dict(title="", gridcolor="#30363D"),
    yaxis=dict(title="Gap vs Benchmark (days)", gridcolor="#30363D")
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# --- REGIONAL CORRELATION ---
st.markdown("## Enablement-Win Rate Correlation by Region")
for region in sorted(df["region"].unique()):
    rdf = df[df["region"] == region]
    if len(rdf) > 5:
        result = calculate_correlation_with_ci(rdf["enablement_score"], rdf["win_probability"])
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("**{}**".format(region))
        with col2:
            st.markdown(correlation_badge(result["r"],
                "r={:.2f}, p={:.4f}, n={}".format(result["r"], result["p"], result["n"])),
                unsafe_allow_html=True)
