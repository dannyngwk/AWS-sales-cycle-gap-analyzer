"""Metrics Calculation Helpers — Statistical functions for the dashboard."""

import pandas as pd
import numpy as np
from scipy import stats


def calculate_cohort_delta(df, threshold=60):
    """Calculate performance delta between enabled and under-enabled cohorts."""
    enabled = df[df["enablement_score"] >= threshold]
    under = df[df["enablement_score"] < threshold]

    if len(enabled) < 2 or len(under) < 2:
        return {
            "win_rate_delta": 0, "cycle_delta": 0, "deal_size_delta_pct": 0,
            "enabled_n": len(enabled), "under_n": len(under),
            "t_stat_win": 0, "p_value_win": 1.0
        }

    t_stat, p_val = stats.ttest_ind(enabled["win_probability"], under["win_probability"])

    under_deal_mean = under["deal_value_usd"].mean()
    if under_deal_mean == 0:
        deal_delta_pct = 0
    else:
        deal_delta_pct = ((enabled["deal_value_usd"].mean() / under_deal_mean) - 1) * 100

    return {
        "win_rate_delta": enabled["win_probability"].mean() - under["win_probability"].mean(),
        "cycle_delta": under["cycle_days_actual"].mean() - enabled["cycle_days_actual"].mean(),
        "deal_size_delta_pct": deal_delta_pct,
        "enabled_n": len(enabled),
        "under_n": len(under),
        "t_stat_win": t_stat,
        "p_value_win": p_val
    }


def calculate_correlation_with_ci(x, y, confidence=0.95):
    """Calculate Pearson correlation with Fisher z confidence interval."""
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x_arr) | np.isnan(y_arr))
    x_clean = x_arr[mask]
    y_clean = y_arr[mask]
    n = len(x_clean)
    if n < 5:
        return {"r": 0, "p": 1.0, "ci_low": -1, "ci_high": 1, "n": n}
    r, p = stats.pearsonr(x_clean, y_clean)
    z = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf((1 + confidence) / 2)
    ci_low = np.tanh(z - z_crit * se)
    ci_high = np.tanh(z + z_crit * se)
    return {"r": r, "p": p, "ci_low": ci_low, "ci_high": ci_high, "n": n}


def format_currency(value, prefix="$", suffix=""):
    """Format large numbers into readable currency."""
    if abs(value) >= 1_000_000:
        return "{}{:.1f}M{}".format(prefix, value / 1_000_000, suffix)
    elif abs(value) >= 1_000:
        return "{}{:.0f}K{}".format(prefix, value / 1_000, suffix)
    else:
        return "{}{:.0f}{}".format(prefix, value, suffix)


def safe_divide(numerator, denominator, default=0):
    """Safe division avoiding ZeroDivisionError."""
    if denominator == 0:
        return default
    return numerator / denominator
