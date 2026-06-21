"""
AWS Sales Cycle Gap Analyzer — APAC Edition
=============================================
Multi-CXO Streamlit dashboard correlating enablement investment with revenue.
Author: Danny Ng | AWS Sales Enablement Intelligence | v2.0 | June 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
from data.sample_data import generate_opportunities, generate_enablement_data, generate_correlation_matrix
from utils.traffic_light import traffic_light_badge, get_status, correlation_badge
from utils.aws_config import AWSConfig

st.set_page_config(
    page_title="AWS Sales Cycle Gap Analyzer",
    page_icon="\U0001F3AF",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLES ---
st.markdown("""
<style>
    .stApp { background-color: #0D1117; }
    .stSidebar { background-color: #161B22; }
    .metric-card {
        background: linear-gradient(135deg, #161B22 0%, #1B2838 100%);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #FF9900;
        box-shadow: 0 4px 20px rgba(255, 153, 0, 0.1);
    }
    .metric-card h3 { color: #FF9900; margin: 0; font-size: 1.8em; }
    .metric-card p { color: #8B949E; margin: 4px 0 0; font-size: 0.85em; }
    .cohort-card { border-radius: 10px; padding: 16px; text-align: center; }
    .cohort-enabled { background: rgba(0, 200, 81, 0.08); border: 1px solid #00C851; }
    .cohort-under { background: rgba(255, 61, 0, 0.08); border: 1px solid #FF3D00; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INIT ---
if "cxo_lens" not in st.session_state:
    st.session_state.cxo_lens = "CSO (Sales)"
if "selected_regions" not in st.session_state:
    st.session_state.selected_regions = ["ANZ", "ASEAN", "India", "Japan", "Korea", "Greater China"]
if "enablement_threshold" not in st.session_state:
    st.session_state.enablement_threshold = 60

# --- DATA LOADING ---
@st.cache_data
def load_all_data():
    return generate_opportunities(n=150), generate_enablement_data(n=80), generate_correlation_matrix()

df_opps, df_enablement, correlations = load_all_data()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## \U0001F3AF AWS Sales Gap Analyzer")
    st.markdown("---")

    st.markdown("### CXO Lens")
    cxo_options = ["CTO (Technical)", "CLO (Learning)", "CSO (Sales)"]
    cxo_lens = st.radio("View As:", cxo_options, index=2, key="cxo_radio")
    st.session_state.cxo_lens = cxo_lens

    st.markdown("---")
    st.markdown("### APAC Regions")
    all_regions = ["ANZ", "ASEAN", "India", "Japan", "Korea", "Greater China"]
    selected_regions = st.multiselect(
        "Filter Regions:", all_regions, default=all_regions, key="region_filter"
    )
    st.session_state.selected_regions = selected_regions

    st.markdown("---")
    with st.expander("Traffic Light Thresholds"):
        st.session_state.enablement_threshold = st.slider(
            "Enablement (Green >=)", 40, 90, 60)
        st.slider("Win Rate (Green >=)", 20, 60, 40, key="wr_threshold")
        st.slider("Cycle Days (Green <=)", 30, 120, 75, key="cycle_threshold")
        st.slider("GenAI Ready (Green >=)", 30, 80, 55, key="genai_threshold")

    st.markdown("---")
    st.markdown("### AWS Services")
    aws_config = AWSConfig()
    bedrock_status = "Live" if aws_config.enable_bedrock else "Local Mode"
    s3_status = "Connected" if aws_config.enable_s3_persistence else "In-Memory"
    qs_status = "Embedded" if aws_config.enable_quicksight_embed else "Standalone"
    st.markdown("Bedrock: {}".format(bedrock_status))
    st.markdown("S3: {}".format(s3_status))
    st.markdown("QuickSight: {}".format(qs_status))

# --- APPLY FILTERS ---
df = df_opps[df_opps["region"].isin(selected_regions)]
active = df[~df["stage"].isin(["Closed Won", "Closed Lost"])]

# === MAIN CONTENT ===
st.markdown("# AWS Sales Cycle Gap Analyzer — APAC")

pipeline_total = active["deal_value_usd"].sum()
header_text = "**Lens:** {} | **Regions:** {} | **Active Deals:** {} | **Pipeline:** ${:,.0f}".format(
    cxo_lens, len(selected_regions), len(active), pipeline_total)
st.markdown(header_text)

# Correlation badge
if len(df) > 5:
    r_val, p_val = stats.pearsonr(df["enablement_score"], df["win_probability"])
    st.markdown(correlation_badge(r_val, "Enablement Score to Win Rate (Portfolio)"), unsafe_allow_html=True)
st.markdown("---")

# --- COHORT COMPARISON ---
st.markdown("## Cohort Performance: Enabled vs Under-Enabled")
threshold = st.session_state.enablement_threshold
enabled = df[df["enablement_score"] >= threshold]
under = df[df["enablement_score"] < threshold]

c1, c2, c3 = st.columns([2, 2, 1])

with c1:
    en_wr = enabled["win_probability"].mean() if len(enabled) > 0 else 0
    en_count = len(enabled)
    en_pipeline = enabled["deal_value_usd"].sum() if len(enabled) > 0 else 0
    html_enabled = (
        '<div class="cohort-card cohort-enabled">'
        '<h4 style="color:#00C851;margin:0;">Enabled (>={threshold})</h4>'
        '<h2 style="color:#69F0AE;margin:8px 0;">{wr:.1f}% Win Rate</h2>'
        '<p style="color:#8B949E;">{count} deals | ${pipeline:,.0f}</p>'
        '</div>'
    ).format(threshold=threshold, wr=en_wr, count=en_count, pipeline=en_pipeline)
    st.markdown(html_enabled, unsafe_allow_html=True)

with c2:
    un_wr = under["win_probability"].mean() if len(under) > 0 else 0
    un_count = len(under)
    un_pipeline = under["deal_value_usd"].sum() if len(under) > 0 else 0
    html_under = (
        '<div class="cohort-card cohort-under">'
        '<h4 style="color:#FF3D00;margin:0;">Under-Enabled (<{threshold})</h4>'
        '<h2 style="color:#FF8A65;margin:8px 0;">{wr:.1f}% Win Rate</h2>'
        '<p style="color:#8B949E;">{count} deals | ${pipeline:,.0f}</p>'
        '</div>'
    ).format(threshold=threshold, wr=un_wr, count=un_count, pipeline=un_pipeline)
    st.markdown(html_under, unsafe_allow_html=True)

with c3:
    delta_wr = en_wr - un_wr
    if len(enabled) > 1 and len(under) > 1:
        en_cycle = enabled["cycle_days_actual"].mean()
        un_cycle = under["cycle_days_actual"].mean()
        delta_cy = un_cycle - en_cycle
        _, p_value = stats.ttest_ind(enabled["win_probability"], under["win_probability"])
        sig_text = "Significant" if p_value < 0.05 else "Not significant"
        sig_color = "#69F0AE" if p_value < 0.05 else "#FF8A65"
    else:
        delta_cy = 0
        p_value = 1.0
        sig_text = "Insufficient data"
        sig_color = "#8B949E"

    html_delta = (
        '<div style="text-align:center;padding:16px;">'
        '<h4 style="color:#58A6FF;">Delta</h4>'
        '<p style="color:#69F0AE;font-size:1.3em;font-weight:700;">+{dwr:.1f}% win rate</p>'
        '<p style="color:#FFD54F;">-{dcy:.0f} days cycle</p>'
        '<p style="color:{sig_color};font-size:0.8em;">p={pval:.4f} {sig}</p>'
        '</div>'
    ).format(dwr=delta_wr, dcy=delta_cy, sig_color=sig_color, pval=p_value, sig=sig_text)
    st.markdown(html_delta, unsafe_allow_html=True)

st.markdown("---")

# --- QUICK METRICS ---
st.markdown("## Key Metrics")
m1, m2, m3, m4, m5, m6 = st.columns(6)

pipeline_m = active["deal_value_usd"].sum() / 1e6
win_rate_m = df["win_probability"].mean()
cycle_gap_m = df["gap_days"].mean()
enablement_m = df["enablement_score"].mean()
genai_m = df["genai_readiness"].mean()
meddpicc_m = df["meddpicc_avg"].mean()

metrics_list = [
    (m1, "Pipeline", pipeline_m, "pipeline_value", "${:.1f}M".format(pipeline_m)),
    (m2, "Win Rate", win_rate_m, "win_rate", "{:.1f}%".format(win_rate_m)),
    (m3, "Cycle Gap", cycle_gap_m, "cycle_days", "{:+.0f}d".format(cycle_gap_m)),
    (m4, "Enablement", enablement_m, "enablement_score", "{:.0f}%".format(enablement_m)),
    (m5, "GenAI", genai_m, "genai_readiness", "{:.0f}%".format(genai_m)),
    (m6, "MEDDPICC", meddpicc_m, "meddpicc_score", "{:.0f}/100".format(meddpicc_m)),
]

for col, name, val, mtype, display in metrics_list:
    with col:
        status = get_status(val, mtype)
        card_html = '<div class="metric-card"><p>{}</p><h3>{}</h3></div>'.format(name, display)
        st.markdown(card_html, unsafe_allow_html=True)
        st.markdown(traffic_light_badge(status), unsafe_allow_html=True)

st.markdown("---")

# --- CXO SPOTLIGHT ---
if "CTO" in cxo_lens:
    st.markdown("## CTO Spotlight: Technical Readiness")
    st.markdown(correlation_badge(0.68, "GenAI Readiness to Technical Win Rate"), unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.metric("GenAI Readiness", "{:.0f}%".format(genai_m))
    sa_rate = df["sa_engaged"].mean() * 100
    s2.metric("SA Engagement", "{:.0f}%".format(sa_rate))
    bedrock_pipe = df[df["aws_service_primary"] == "Amazon Bedrock"]["deal_value_usd"].sum()
    s3.metric("Bedrock Pipeline", "${:.1f}M".format(bedrock_pipe / 1e6))

elif "CLO" in cxo_lens:
    st.markdown("## CLO Spotlight: Learning Impact")
    st.markdown(correlation_badge(0.74, "Enablement to Revenue Lift"), unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.metric("Programs Active", "{}".format(len(df_enablement)))
    rev_attr = df_enablement["revenue_impact_usd"].sum()
    s2.metric("Revenue Attributed", "${:.1f}M".format(rev_attr / 1e6))
    avg_comp = df_enablement["completion_rate_pct"].mean()
    s3.metric("Avg Completion", "{:.0f}%".format(avg_comp))

else:
    st.markdown("## CSO Spotlight: Revenue Velocity")
    st.markdown(correlation_badge(0.79, "MEDDPICC to Close Rate"), unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    velocity = active["velocity_weekly_usd"].sum()
    s1.metric("Velocity", "${:.0f}K/wk".format(velocity / 1000))
    high_risk = df[df["risk_flag"] == "High"]
    risk_val = high_risk["deal_value_usd"].sum()
    s2.metric("At Risk", "{} deals".format(len(high_risk)), "${:.1f}M".format(risk_val / 1e6))
    coverage = pipeline_total / 8_000_000
    s3.metric("Coverage", "{:.1f}x".format(coverage), "vs $8M target")

st.markdown("---")
st.markdown("*Navigate sidebar pages for deep dives*")
