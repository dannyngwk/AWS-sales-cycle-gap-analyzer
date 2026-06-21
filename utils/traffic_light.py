"""Traffic Light System — Reusable Status Components"""

import streamlit as st
from typing import Optional


def get_status(value, metric_type):
    """Determine traffic light status based on metric type and value."""
    thresholds = {
        "win_rate": {"green": 40, "amber": 25},
        "pipeline_value": {"green": 5, "amber": 2},
        "cycle_days": {"green": 75, "amber": 100},
        "enablement_score": {"green": 60, "amber": 45},
        "genai_readiness": {"green": 55, "amber": 35},
        "meddpicc_score": {"green": 65, "amber": 45},
        "cert_completion": {"green": 60, "amber": 40},
        "deal_velocity": {"green": 50, "amber": 25},
        "risk_score": {"green": 30, "amber": 60},
    }
    if hasattr(st, "session_state"):
        if "wr_threshold" in st.session_state:
            thresholds["win_rate"]["green"] = st.session_state.wr_threshold
        if "enablement_threshold" in st.session_state:
            thresholds["enablement_score"]["green"] = st.session_state.enablement_threshold
        if "cycle_threshold" in st.session_state:
            thresholds["cycle_days"]["green"] = st.session_state.cycle_threshold
        if "genai_threshold" in st.session_state:
            thresholds["genai_readiness"]["green"] = st.session_state.genai_threshold

    config = thresholds.get(metric_type, {"green": 60, "amber": 40})
    inverted = metric_type in ["cycle_days", "risk_score"]

    if inverted:
        if value <= config["green"]:
            return "green"
        elif value <= config["amber"]:
            return "amber"
        else:
            return "red"
    else:
        if value >= config["green"]:
            return "green"
        elif value >= config["amber"]:
            return "amber"
        else:
            return "red"


def traffic_light_badge(status, label=None):
    """Render an HTML traffic light badge."""
    config = {
        "green": {"bg": "rgba(0,200,81,0.15)", "border": "#00C851",
                  "color": "#69F0AE", "icon": "&#x1F7E2;", "text": label or "Healthy"},
        "amber": {"bg": "rgba(255,179,0,0.15)", "border": "#FFB300",
                  "color": "#FFD54F", "icon": "&#x1F7E1;", "text": label or "Caution"},
        "red": {"bg": "rgba(255,61,0,0.15)", "border": "#FF3D00",
                "color": "#FF8A65", "icon": "&#x1F534;", "text": label or "Attention"},
    }
    c = config.get(status, config["amber"])
    html = (
        '<span style="display:inline-flex;align-items:center;gap:4px;'
        'padding:4px 12px;border-radius:16px;font-size:0.8em;font-weight:500;'
        'background:{bg};border:1px solid {border};color:{color};">'
        '{icon} {text}</span>'
    ).format(**c)
    return html


def correlation_badge(r_value, label):
    """Render a correlation indicator badge."""
    if abs(r_value) >= 0.7:
        strength = "Strong"
        color = "#69F0AE"
        bg = "rgba(0,200,81,0.08)"
    elif abs(r_value) >= 0.4:
        strength = "Moderate"
        color = "#58A6FF"
        bg = "rgba(88,166,255,0.08)"
    else:
        strength = "Weak"
        color = "#FFD54F"
        bg = "rgba(255,213,79,0.08)"

    direction = "+" if r_value > 0 else "-"
    abs_r = abs(r_value)
    html = (
        '<span style="display:inline-flex;align-items:center;gap:6px;'
        'padding:5px 14px;border-radius:20px;font-size:0.8em;'
        'background:{bg};border:1px solid {color};color:{color};">'
        '&#x1F4C8; r={direction}{abs_r:.2f} ({strength}) &mdash; {label}</span>'
    ).format(bg=bg, color=color, direction=direction, abs_r=abs_r, strength=strength, label=label)
    return html


def meddpicc_traffic_light(score):
    """Traffic light for MEDDPICC component scores (0-100)."""
    if score >= 70:
        return traffic_light_badge("green", "{:.0f}".format(score))
    elif score >= 45:
        return traffic_light_badge("amber", "{:.0f}".format(score))
    else:
        return traffic_light_badge("red", "{:.0f}".format(score))
