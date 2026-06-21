"""
Synthetic Data Generator — APAC Sales Pipeline
Generates realistic opportunity, enablement, and correlation data.
All correlations are seeded to produce statistically significant results.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_opportunities(n=150, seed=42):
    """Generate n synthetic sales opportunities with APAC regional distribution."""
    np.random.seed(seed)

    regions = ["ANZ", "ASEAN", "India", "Japan", "Korea", "Greater China"]
    region_weights = [0.20, 0.25, 0.18, 0.15, 0.12, 0.10]

    stages = ["Prospect", "Qualification", "Technical Validation",
              "Business Validation", "Negotiation", "Closed Won", "Closed Lost"]
    stage_weights = [0.12, 0.18, 0.22, 0.18, 0.12, 0.10, 0.08]

    aws_services = ["Amazon Bedrock", "Amazon SageMaker", "Amazon Connect",
                    "AWS Lambda", "Amazon EKS", "Amazon RDS", "Amazon S3",
                    "AWS Security Hub", "Amazon QuickSight", "AWS Step Functions"]

    competitors = ["None", "Azure", "GCP", "Multi-cloud", "On-premise"]
    competitor_weights = [0.30, 0.25, 0.20, 0.15, 0.10]

    cert_levels = ["None", "Cloud Practitioner", "SA Associate",
                   "SA Professional", "ML Specialty", "Security Specialty"]
    cert_numeric_map = {"None": 0, "Cloud Practitioner": 20, "SA Associate": 50,
                        "SA Professional": 75, "ML Specialty": 90, "Security Specialty": 95}

    records = []
    for i in range(n):
        region = np.random.choice(regions, p=region_weights)
        stage = np.random.choice(stages, p=stage_weights)

        region_base = {"ANZ": 62, "ASEAN": 48, "India": 55,
                       "Japan": 70, "Korea": 58, "Greater China": 45}
        enablement = np.clip(np.random.normal(region_base[region], 15), 15, 98)
        genai_readiness = np.clip(enablement * 0.7 + np.random.normal(10, 12), 10, 95)
        win_prob = np.clip(enablement * 0.55 + np.random.normal(5, 10), 5, 95)

        deal_base = {"ANZ": 280000, "ASEAN": 180000, "India": 120000,
                     "Japan": 350000, "Korea": 220000, "Greater China": 250000}
        deal_value = max(25000, np.random.lognormal(np.log(deal_base[region]), 0.6))

        benchmark_days = {"ANZ": 72, "ASEAN": 85, "India": 90,
                          "Japan": 65, "Korea": 80, "Greater China": 95}
        cycle_benchmark = benchmark_days[region]
        cycle_actual = max(20, cycle_benchmark + (60 - enablement) * 0.8 + np.random.normal(0, 12))
        gap_days = cycle_actual - cycle_benchmark

        meddpicc_base = enablement * 0.6 + np.random.normal(15, 8)
        meddpicc = {
            "metrics": np.clip(meddpicc_base + np.random.normal(0, 10), 10, 100),
            "econ_buyer": np.clip(meddpicc_base + np.random.normal(-5, 12), 10, 100),
            "decision_criteria": np.clip(meddpicc_base + np.random.normal(3, 10), 10, 100),
            "decision_process": np.clip(meddpicc_base + np.random.normal(-2, 11), 10, 100),
            "paper_process": np.clip(meddpicc_base + np.random.normal(-8, 13), 10, 100),
            "pain": np.clip(meddpicc_base + np.random.normal(5, 9), 10, 100),
            "champion": np.clip(meddpicc_base + np.random.normal(-3, 14), 10, 100),
            "competition": np.clip(meddpicc_base + np.random.normal(0, 11), 10, 100),
        }
        meddpicc_avg = np.mean(list(meddpicc.values()))

        days_since_activity = max(1, int(np.random.exponential(14)))
        sa_engaged = np.random.random() < (0.4 + enablement * 0.005)
        training_hours = max(0, np.random.normal(enablement * 0.3, 5))
        days_in_stage = max(1, int(np.random.exponential(18)))
        cert = np.random.choice(cert_levels, p=[0.15, 0.25, 0.30, 0.15, 0.10, 0.05])

        risk_score = (100 - win_prob) * 0.3 + days_since_activity * 1.5 + (100 - enablement) * 0.2
        risk_flag = "High" if risk_score > 65 else "Medium" if risk_score > 40 else "Low"
        velocity = deal_value * (win_prob / 100) / max(cycle_actual / 7, 1)
        aging_status = "Stalled" if days_in_stage > 30 else "On Track" if days_in_stage < 15 else "Aging"

        records.append({
            "opportunity_id": "OPP-{}-{:04d}".format(region[:2], i + 1),
            "region": region,
            "stage": stage,
            "deal_value_usd": round(deal_value, 0),
            "win_probability": round(win_prob, 1),
            "enablement_score": round(enablement, 1),
            "genai_readiness": round(genai_readiness, 1),
            "cycle_days_actual": round(cycle_actual, 0),
            "cycle_days_benchmark": cycle_benchmark,
            "gap_days": round(gap_days, 0),
            "meddpicc_metrics": round(meddpicc["metrics"], 1),
            "meddpicc_econ_buyer": round(meddpicc["econ_buyer"], 1),
            "meddpicc_decision_criteria": round(meddpicc["decision_criteria"], 1),
            "meddpicc_decision_process": round(meddpicc["decision_process"], 1),
            "meddpicc_paper_process": round(meddpicc["paper_process"], 1),
            "meddpicc_pain": round(meddpicc["pain"], 1),
            "meddpicc_champion": round(meddpicc["champion"], 1),
            "meddpicc_competition": round(meddpicc["competition"], 1),
            "meddpicc_avg": round(meddpicc_avg, 1),
            "days_since_last_activity": days_since_activity,
            "sa_engaged": sa_engaged,
            "training_hours_30d": round(training_hours, 1),
            "days_in_current_stage": days_in_stage,
            "aws_service_primary": np.random.choice(aws_services),
            "competitor_present": np.random.choice(competitors, p=competitor_weights),
            "certification_level": cert,
            "cert_numeric": cert_numeric_map[cert],
            "risk_flag": risk_flag,
            "velocity_weekly_usd": round(velocity, 0),
            "aging_status": aging_status,
            "enablement_cohort": "Enabled" if enablement >= 60 else "Under-Enabled",
        })

    return pd.DataFrame(records)


def generate_enablement_data(n=80, seed=42):
    """Generate enablement program data with ROI metrics."""
    np.random.seed(seed)

    programs = [
        "AWS GenAI Foundations", "Bedrock Builder Workshop", "MEDDPICC Mastery",
        "SA Technical Immersion", "Cloud Economics", "Security Specialization",
        "Partner Co-Sell Academy", "Executive Presence", "Industry Verticals",
        "Competitive Intelligence"
    ]
    regions = ["ANZ", "ASEAN", "India", "Japan", "Korea", "Greater China"]

    records = []
    for i in range(n):
        program = np.random.choice(programs)
        region = np.random.choice(regions)
        participants = np.random.randint(5, 45)
        cost_per_head = np.random.uniform(800, 4500)
        total_cost = participants * cost_per_head
        completion = np.clip(np.random.normal(72, 15), 30, 100)
        win_rate_lift = np.clip(np.random.normal(18, 8), 2, 45)
        revenue_impact = total_cost * np.random.uniform(2.5, 12)
        roi = revenue_impact / total_cost

        records.append({
            "program_id": "PRG-{:03d}".format(i + 1),
            "program_name": program,
            "region": region,
            "participants": participants,
            "cost_per_participant": round(cost_per_head, 0),
            "total_cost": round(total_cost, 0),
            "completion_rate_pct": round(completion, 1),
            "win_rate_lift": round(win_rate_lift, 1),
            "revenue_impact_usd": round(revenue_impact, 0),
            "roi_multiple": round(roi, 1),
            "quarter": np.random.choice(["Q1-26", "Q2-26", "Q3-26"]),
        })

    return pd.DataFrame(records)


def generate_correlation_matrix():
    """Pre-computed correlation insights."""
    return {
        "enablement_win_rate": {"r": 0.74, "p": 0.0001, "ci_low": 0.65, "ci_high": 0.81},
        "genai_win_rate": {"r": 0.68, "p": 0.0003, "ci_low": 0.57, "ci_high": 0.76},
        "meddpicc_win_rate": {"r": 0.79, "p": 0.00001, "ci_low": 0.71, "ci_high": 0.85},
        "training_enablement": {"r": 0.71, "p": 0.0002, "ci_low": 0.61, "ci_high": 0.79},
        "enablement_cycle": {"r": -0.62, "p": 0.001, "ci_low": -0.72, "ci_high": -0.50},
    }
