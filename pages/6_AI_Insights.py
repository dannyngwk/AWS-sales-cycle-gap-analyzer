"""
Page 6: AI Insights — Bedrock-Powered Analysis & Natural Language Query
"""

import streamlit as st
import pandas as pd
import numpy as np
from data.sample_data import generate_opportunities, generate_enablement_data
from utils.aws_bedrock import BedrockInsightEngine
from utils.aws_s3_datalake import S3DataLake
from utils.traffic_light import traffic_light_badge, get_status
from utils.metrics import format_currency

st.set_page_config(page_title="AI Insights", page_icon="\U0001F916", layout="wide")

@st.cache_data
def load_data():
    return generate_opportunities(n=150), generate_enablement_data(n=80)

df, df_en = load_data()
regions = st.session_state.get("selected_regions", df["region"].unique().tolist())
df = df[df["region"].isin(regions)]
active = df[~df["stage"].isin(["Closed Won", "Closed Lost"])]

st.markdown("# AI-Powered Insights")
st.markdown("Amazon Bedrock GenAI analysis with rule-based fallback.")
st.markdown("---")

# Initialize engines
engine = BedrockInsightEngine()
datalake = S3DataLake()

mode_badge = "Live (Bedrock)" if engine.available else "Rule-Based Fallback"
st.markdown("**Mode:** {} | **Model:** {}".format(mode_badge, engine.config.bedrock_model_id))
st.markdown("---")

# --- PORTFOLIO SUMMARY ---
st.markdown("## Executive Portfolio Summary")
if len(active) > 0:
    portfolio_stats = {
        "pipeline_value": active["deal_value_usd"].sum(),
        "total_deals": len(active),
        "avg_win_rate": df["win_probability"].mean(),
        "avg_enablement": df["enablement_score"].mean(),
        "correlation_r": 0.74,
        "high_risk": len(df[df["risk_flag"] == "High"]),
        "top_region": df.groupby("region")["win_probability"].mean().idxmax(),
        "weak_region": df.groupby("region")["win_probability"].mean().idxmin(),
    }

    insight = engine.generate_portfolio_summary(portfolio_stats)

    st.markdown("### Summary")
    st.info(insight.summary)

    st.markdown("### Key Findings")
    for finding in insight.key_findings:
        st.markdown("- {}".format(finding))

    st.markdown("### Recommendations")
    for rec in insight.recommendations:
        if isinstance(rec, dict):
            priority = rec.get("priority", "Medium")
            action = rec.get("action", str(rec))
            color = "#FF3D00" if priority == "Critical" else "#FFB300" if priority == "High" else "#58A6FF"
            st.markdown(
                '<span style="color:{};font-weight:600;">[{}]</span> {}'.format(
                    color, priority, action),
                unsafe_allow_html=True)
        else:
            st.markdown("- {}".format(rec))

    st.markdown("*Confidence: {:.0f}% | Engine: {}*".format(
        insight.confidence * 100, insight.model_used))

st.markdown("---")

# --- NATURAL LANGUAGE QUERY ---
st.markdown("## Ask Your Pipeline")
st.markdown("Ask questions in natural language about your sales data.")

query = st.text_input("Enter your question:", placeholder="e.g., Which deals are at risk?")

if query:
    context = {
        "pipeline_value": active["deal_value_usd"].sum(),
        "total_deals": len(active),
        "avg_win_rate": df["win_probability"].mean(),
        "high_risk": len(df[df["risk_flag"] == "High"]),
        "correlation": 0.74,
        "top_region": df.groupby("region")["win_probability"].mean().idxmax(),
        "weak_region": df.groupby("region")["win_probability"].mean().idxmin(),
    }
    response = engine.natural_language_query(query, context)
    st.markdown("### Answer")
    st.success(response)

st.markdown("---")

# --- DEAL RISK ANALYSIS ---
st.markdown("## Individual Deal Risk Analysis")
if len(active) > 0:
    deal_options = active.sort_values("deal_value_usd", ascending=False)["opportunity_id"].tolist()
    selected_deal = st.selectbox("Select Deal:", deal_options[:20])

    if selected_deal:
        deal_row = active[active["opportunity_id"] == selected_deal].iloc[0]
        deal_data = deal_row.to_dict()

        risk_insight = engine.analyze_deal_risk(deal_data)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### Risk Assessment: {}".format(selected_deal))
            st.markdown(risk_insight.summary)

            st.markdown("**Risk Factors:**")
            for factor in risk_insight.key_findings:
                st.markdown("- {}".format(factor))

            st.markdown("**Recommended Actions:**")
            for action in risk_insight.recommendations:
                if isinstance(action, dict):
                    st.markdown("- **{}** (Timeline: {})".format(
                        action.get("action", ""), action.get("timeline", "TBD")))
                else:
                    st.markdown("- {}".format(action))

        with col2:
            st.markdown("### Deal Snapshot")
            st.metric("Deal Value", format_currency(deal_data["deal_value_usd"]))
            st.metric("Win Probability", "{:.0f}%".format(deal_data["win_probability"]))
            st.metric("Enablement", "{:.0f}%".format(deal_data["enablement_score"]))
            st.metric("MEDDPICC", "{:.0f}/100".format(deal_data["meddpicc_avg"]))
            st.metric("Days Inactive", "{}".format(deal_data["days_since_last_activity"]))
            st.markdown(traffic_light_badge(
                get_status(deal_data["enablement_score"], "enablement_score"),
                "Enablement"), unsafe_allow_html=True)

st.markdown("---")

# --- DATA LINEAGE ---
st.markdown("## Data Architecture & Lineage")
lineage = datalake.get_data_lineage()

for layer, info in lineage.items():
    with st.expander("{} Layer".format(layer.upper())):
        for key, value in info.items():
            if isinstance(value, list):
                st.markdown("**{}:** {}".format(key.title(), ", ".join(value)))
            else:
                st.markdown("**{}:** {}".format(key.title(), value))
