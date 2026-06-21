# AWS Sales Cycle Gap Analyzer — APAC Edition

## Overview
Multi-CXO Streamlit dashboard that statistically correlates sales enablement investment with revenue outcomes across APAC regions. Built to demonstrate GenAI fluency, AWS-native architecture, and data-driven sales leadership.

**Author:** Danny Ng | AWS Sales Enablement Intelligence | v2.0 | June 2026

## Key Features
- **Multi-CXO Lens:** Toggle between CTO, CLO, and CSO perspectives
- **Traffic Light System:** Configurable thresholds for instant health assessment
- **Statistical Correlation Engine:** Pearson r with Fisher z confidence intervals
- **MEDDPICC Scorecard:** 8-dimension qualification heatmap by region
- **What-If Simulator:** Adjust enablement investment, see projected revenue lift
- **AI Insights:** Amazon Bedrock-powered analysis with rule-based fallback
- **APAC Regional View:** 6-region comparative radar and gap analysis

## AWS Services Demonstrated
| Service | Usage |
|---------|-------|
| Amazon Bedrock | GenAI insights (Claude 3.5 Sonnet) |
| Amazon QuickSight | Embedded analytics + RLS |
| Amazon S3 | Data lake (Bronze/Silver/Gold) |
| AWS Glue | ETL pipeline |
| Amazon Athena | SQL analytics |
| AWS CloudFormation | IaC deployment |
| Amazon CloudWatch | Operational metrics |

## Project Structure
```
AWS-sales-cycle-gap-analyzer/
├── .streamlit/
│   └── config.toml          # AWS dark theme
├── data/
│   ├── __init__.py
│   └── sample_data.py       # Synthetic APAC pipeline generator
├── utils/
│   ├── __init__.py
│   ├── traffic_light.py     # Traffic light + correlation badges
│   ├── metrics.py           # Statistical helpers
│   ├── aws_config.py        # Service client factory
│   ├── aws_bedrock.py       # Bedrock GenAI engine
│   ├── aws_s3_datalake.py   # S3 data lake integration
│   └── aws_quicksight.py    # QuickSight embed + CDK
├── pages/
│   ├── 1_Executive_Dashboard.py
│   ├── 2_Opportunity_Pipeline.py
│   ├── 3_Enablement_Correlation.py
│   ├── 4_APAC_Regional_View.py
│   ├── 5_Predictive_Insights.py
│   └── 6_AI_Insights.py
├── app.py                   # Main entry point
├── requirements.txt
└── README.md
```

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (no AWS credentials needed)
streamlit run app.py

# Run with AWS services enabled
export ENABLE_BEDROCK=true
export ENABLE_S3=true
export ENABLE_QS_EMBED=true
export AWS_ACCOUNT_ID=123456789012
streamlit run app.py
```

## Architecture Highlights
- **Graceful Degradation:** Dashboard runs fully without AWS credentials
- **12-Factor App Design:** Environment-based configuration
- **Statistical Rigor:** All correlations include p-values and confidence intervals
- **Cohort Analysis:** Enabled vs Under-Enabled with t-test significance
- **ML Feature Importance:** GradientBoosting for win probability drivers

## Interview Talking Points
1. **Correlation ≠ Causation** — but r=0.74 with p<0.001 across 150 deals is compelling
2. **Multi-CXO Design** — same data, different stories for different stakeholders
3. **AWS-Native** — Bedrock, QuickSight, S3, Glue, Athena, CloudFormation
4. **Production-Ready** — error handling, caching, graceful fallbacks
5. **GenAI Integration** — Bedrock with structured prompts + rule-based fallback

## License
Internal use — AWS Sales Enablement Intelligence
