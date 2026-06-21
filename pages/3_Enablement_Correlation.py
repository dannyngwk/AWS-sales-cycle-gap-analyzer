"""
Page 3: Enablement Correlation — Statistical Deep Dive
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from data.sample_data import generate_opportunities, generate_enablement_data, generate_correlation_matrix
from utils.traffic_light import correlation_badge, traffic_light_badge, get_status
from utils.metrics import calculate_correlation_with_ci, calculate_cohort_delta, format_currency

st.set_page_config(page_title="Enablement Correlation", page_icon="\U0001F4C8", layout="wide")

@st.cache_data
def load_data():
    return generate_opportunities(n=150), generate_enablement_data(n=80), generate_correlation_matrix()

df, df_en, corr_matrix = load_data()
regions = st.session_state.get("selected_regions", df["region"].unique().tolist())
df = df[df["region"].isin(regions)]

st.markdown("# Enablement-Revenue Correlation Engine")
st.markdown("Statistical proof that enablement investment drives revenue outcomes.")
st.markdown("---")

# --- CORRELATION BADGES ---
st.markdown("## Key Correlations (Portfolio-Wide)")
b1, b2, b3, b4, b5 = st.columns(5)
with b1:
    st.markdown(correlation_badge(corr_matrix["enablement_win_rate"]["r"], "Enablement → Win Rate"), unsafe_allow_html=True)
with b2:
    st.markdown(correlation_badge(corr_matrix["genai_win_rate"]["r"], "GenAI → Win Rate"), unsafe_allow_html=True)
with b3:
    st.markdown(correlation_badge(corr_matrix["meddpicc_win_rate"]["r"], "MEDDPICC → Win Rate"), unsafe_allow_html=True)
with b4:
    st.markdown(correlation_badge(corr_matrix["training_enablement"]["r"], "Training → Enablement"), unsafe_allow_html=True)
with b5:
    st.markdown(correlation_badge(corr_matrix["enablement_cycle"]["r"], "Enablement → Cycle Time"), unsafe_allow_html=True)

st.markdown("---")

# --- SCATTER WITH REGRESSION ---
st.markdown("## Enablement Score vs Win Probability")
if len(df) > 5:
    corr_result = calculate_correlation_with_ci(df["enablement_score"], df["win_probability"])

    fig = px.scatter(
        df, x="enablement_score", y="win_probability",
        color="enablement_cohort", size="deal_value_usd",
        hover_data=["opportunity_id", "region", "stage"],
        color_discrete_map={"Enabled": "#69F0AE", "Under-Enabled": "#FF8A65"},
        trendline="ols"
    )
    fig.update_layout(
        paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
        font=dict(color="#F0F6FC"), height=450,
        xaxis=dict(title="Enablement Score", gridcolor="#30363D"),
        yaxis=dict(title="Win Probability (%)", gridcolor="#30363D"),
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

    ci_text = "r = {:.3f} | 95% CI [{:.3f}, {:.3f}] | p = {:.6f} | n = {}".format(
        corr_result["r"], corr_result["ci_low"], corr_result["ci_high"],
        corr_result["p"], corr_result["n"])
    st.markdown("**Statistical Result:** {}".format(ci_text))

st.markdown("---")

# --- COHORT ANALYSIS ---
st.markdown("## Cohort Impact Analysis")
threshold = st.session_state.get("enablement_threshold", 60)
delta = calculate_cohort_delta(df, threshold)

d1, d2, d3, d4 = st.columns(4)
d1.metric("Win Rate Delta", "+{:.1f}%".format(delta["win_rate_delta"]))
d2.metric("Cycle Time Saved", "{:.0f} days".format(delta["cycle_delta"]))
d3.metric("Deal Size Lift", "+{:.0f}%".format(delta["deal_size_delta_pct"]))
sig = "Yes (p<0.05)" if delta["p_value_win"] < 0.05 else "No"
d4.metric("Statistically Significant", sig)

st.markdown("---")

# --- ENABLEMENT PROGRAM ROI ---
st.markdown("## Enablement Program ROI")
if len(df_en) > 0:
    program_roi = df_en.groupby("program_name").agg(
        avg_roi=("roi_multiple", "mean"),
        total_revenue=("revenue_impact_usd", "sum"),
        avg_lift=("win_rate_lift", "mean"),
        participants=("participants", "sum")
    ).reset_index().sort_values("avg_roi", ascending=False)

    fig3 = px.bar(
        program_roi, x="program_name", y="avg_roi",
        color="avg_lift", text="avg_roi",
        color_continuous_scale=["#FF3D00", "#FFB300", "#69F0AE"]
    )
    fig3.update_traces(texttemplate="%{text:.1f}x", textposition="outside")
    fig3.update_layout(
        paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
        font=dict(color="#F0F6FC"), height=400,
        xaxis=dict(title="", tickangle=-45, gridcolor="#30363D"),
        yaxis=dict(title="ROI Multiple", gridcolor="#30363D")
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### Program Details")
    st.dataframe(
        program_roi.rename(columns={
            "program_name": "Program", "avg_roi": "Avg ROI (x)",
            "total_revenue": "Revenue Impact ($)", "avg_lift": "Win Rate Lift (%)",
            "participants": "Total Participants"
        }),
        use_container_width=True, hide_index=True,
        column_config={
            "Revenue Impact ($)": st.column_config.NumberColumn(format="$%d"),
            "Avg ROI (x)": st.column_config.NumberColumn(format="%.1fx"),
        }
    )

st.markdown("---")

# --- REGIONAL CORRELATION BREAKDOWN ---
st.markdown("## Regional Correlation Breakdown")
regional_corr = []
for region in df["region"].unique():
    rdf = df[df["region"] == region]
    if len(rdf) > 5:
        result = calculate_correlation_with_ci(rdf["enablement_score"], rdf["win_probability"])
        regional_corr.append({
            "Region": region,
            "r": result["r"],
            "p-value": result["p"],
            "CI Low": result["ci_low"],
            "CI High": result["ci_high"],
            "n": result["n"]
        })

if regional_corr:
    rc_df = pd.DataFrame(regional_corr).sort_values("r", ascending=False)
    st.dataframe(rc_df, use_container_width=True, hide_index=True,
                 column_config={
                     "r": st.column_config.NumberColumn(format="%.3f"),
                     "p-value": st.column_config.NumberColumn(format="%.5f"),
                     "CI Low": st.column_config.NumberColumn(format="%.3f"),
                     "CI High": st.column_config.NumberColumn(format="%.3f"),
                 })
