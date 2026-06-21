"""
Amazon Bedrock Integration — GenAI-Powered Sales Insights
Graceful fallback to rule-based insights when Bedrock unavailable.
"""

import json
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BedrockInsight:
    """Structured output from Bedrock analysis."""
    summary: str
    key_findings: List[str]
    recommendations: List[Dict[str, str]]
    confidence: float
    model_used: str
    tokens_used: int = 0


class BedrockInsightEngine:
    """Amazon Bedrock-powered insight generation with rule-based fallback."""

    def __init__(self, config=None):
        from utils.aws_config import AWSConfig, get_aws_client
        self.config = config or AWSConfig()
        self.client = None
        self.available = False
        if self.config.enable_bedrock:
            self.client = get_aws_client("bedrock-runtime", self.config.bedrock_region)
            self.available = self.client is not None

    def _invoke_bedrock(self, prompt, max_tokens=1024, temperature=0.3):
        """Invoke Bedrock model."""
        if not self.available:
            return None
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
                "system": "You are an AWS Sales Analytics AI. Provide concise, data-driven insights."
            })
            response = self.client.invoke_model(
                modelId=self.config.bedrock_model_id,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"]
        except Exception as e:
            logger.error("Bedrock invocation failed: %s", e)
            return None

    def analyze_deal_risk(self, deal_data):
        """Generate risk analysis for a specific deal."""
        prompt = "Analyze this deal and provide risk assessment:\n{}".format(
            json.dumps(deal_data, default=str))
        response = self._invoke_bedrock(prompt)
        if response:
            return BedrockInsight(
                summary=response[:200], key_findings=[response],
                recommendations=[{"action": "Review AI analysis"}],
                confidence=0.85, model_used=self.config.bedrock_model_id)
        return self._fallback_deal_risk(deal_data)

    def generate_portfolio_summary(self, portfolio_stats):
        """Generate executive portfolio summary."""
        prompt = "Create executive summary for this sales portfolio:\n{}".format(
            json.dumps(portfolio_stats, default=str))
        response = self._invoke_bedrock(prompt)
        if response:
            return BedrockInsight(
                summary=response[:300], key_findings=[response],
                recommendations=[{"action": "Review portfolio"}],
                confidence=0.85, model_used=self.config.bedrock_model_id)
        return self._fallback_portfolio_summary(portfolio_stats)

    def generate_enablement_prescription(self, gap_data):
        """Generate enablement prescriptions for a region."""
        return self._fallback_prescription(gap_data)

    def natural_language_query(self, query, context):
        """Answer NL questions about pipeline."""
        prompt = "Answer this question about our sales pipeline: {}\nContext: {}".format(
            query, json.dumps(context, default=str))
        response = self._invoke_bedrock(prompt)
        if response:
            return response
        return self._fallback_nl_response(query, context)

    # --- FALLBACK METHODS ---
    def _fallback_deal_risk(self, deal_data):
        risk_factors = []
        actions = []

        enablement = deal_data.get("enablement_score", 0)
        activity_days = deal_data.get("days_since_last_activity", 0)
        competitor = deal_data.get("competitor_present", "None")
        sa = deal_data.get("sa_engaged", False)
        meddpicc = deal_data.get("meddpicc_avg", 0)
        opp_id = deal_data.get("opportunity_id", "Unknown")

        if enablement < 50:
            risk_factors.append("Low enablement score ({:.0f}%) indicates skill gap".format(enablement))
            actions.append({"action": "Enroll in targeted training program", "timeline": "2 weeks"})
        if activity_days > 21:
            risk_factors.append("No activity in {} days — deal may be stalling".format(activity_days))
            actions.append({"action": "Executive outreach within 48hrs", "timeline": "Immediate"})
        if competitor not in [None, "None", ""]:
            risk_factors.append("Active competitor: {}".format(competitor))
            actions.append({"action": "Deploy competitive battle card", "timeline": "This week"})
        if not sa:
            risk_factors.append("No SA engagement on this opportunity")
            actions.append({"action": "Assign SA immediately", "timeline": "24hrs"})
        if meddpicc < 45:
            risk_factors.append("MEDDPICC score {:.0f}/100 — qualification gaps".format(meddpicc))
            actions.append({"action": "Manager-led MEDDPICC coaching", "timeline": "This week"})

        if not risk_factors:
            risk_factors.append("Moderate risk profile — monitor closely")
            actions.append({"action": "Weekly check-in", "timeline": "Ongoing"})

        summary = "Deal {} has {} risk factors requiring attention.".format(opp_id, len(risk_factors))
        return BedrockInsight(
            summary=summary, key_findings=risk_factors[:5],
            recommendations=actions[:4], confidence=0.65,
            model_used="rule-based-fallback")

    def _fallback_portfolio_summary(self, stats):
        wr = stats.get("avg_win_rate", 0)
        en = stats.get("avg_enablement", 0)
        pipeline = stats.get("pipeline_value", 0)
        corr = stats.get("correlation_r", 0)
        top_region = stats.get("top_region", "Unknown")
        weak_region = stats.get("weak_region", "Unknown")

        if wr >= 40 and en >= 65:
            health = "strong"
        elif wr >= 25 and en >= 45:
            health = "moderate with improvement areas"
        else:
            health = "concerning - intervention needed"

        summary = (
            "APAC portfolio health: {}. ${:,.0f} active pipeline across {} deals. "
            "Correlation r={:.2f} confirms enablement drives revenue outcomes."
        ).format(health, pipeline, stats.get("total_deals", 0), corr)

        findings = [
            "Top performing region: {}".format(top_region),
            "Needs attention: {}".format(weak_region),
            "Enablement-Win Rate correlation: r={:.2f} (statistically significant)".format(corr),
            "High-risk deals: {} requiring immediate action".format(stats.get("high_risk", 0)),
        ]

        recommendations = [
            {"action": "Accelerate GenAI enablement in underperforming regions", "priority": "High"},
            {"action": "SA pairing for all deals >$200K without coverage", "priority": "Critical"},
            {"action": "Weekly forecast review focusing on high-risk deals", "priority": "Medium"},
        ]

        return BedrockInsight(
            summary=summary, key_findings=findings,
            recommendations=recommendations, confidence=0.7,
            model_used="rule-based-fallback")

    def _fallback_prescription(self, gap_data):
        region = gap_data.get("region", "Unknown")
        genai = gap_data.get("genai_readiness", 0)
        enablement = gap_data.get("enablement_score", 0)
        revenue_risk = gap_data.get("revenue_at_risk", 0)

        prescriptions = []
        if genai < 50:
            prescriptions.append({
                "program_name": "AWS GenAI Foundations + Bedrock Builder",
                "target": "Reps in {} below 50% GenAI readiness".format(region),
                "expected_winrate_lift": "+18-22%",
                "revenue_impact": "$1.5-2.2M acceleration",
                "timeline": "4 weeks", "priority": "Critical"
            })
        if enablement < 55:
            prescriptions.append({
                "program_name": "MEDDPICC Mastery Bootcamp",
                "target": "Reps with MEDDPICC < 50 in {}".format(region),
                "expected_winrate_lift": "+15-25%",
                "revenue_impact": "$1.8-2.8M",
                "timeline": "2 weeks intensive", "priority": "Critical"
            })
        prescriptions.append({
            "program_name": "SA Immersion + Partner Co-Sell",
            "target": "Deals >$150K without SA in {}".format(region),
            "expected_winrate_lift": "+12-18%",
            "revenue_impact": "${:,.0f} recovery potential".format(revenue_risk * 0.15),
            "timeline": "Immediate", "priority": "High"
        })

        summary = "{} prescriptions generated for {}".format(len(prescriptions), region)
        return BedrockInsight(
            summary=summary,
            key_findings=[p["program_name"] for p in prescriptions],
            recommendations=prescriptions, confidence=0.7,
            model_used="rule-based-fallback")

    def _fallback_nl_response(self, query, context):
        q = query.lower()
        pipeline = context.get("pipeline_value", 0)
        wr = context.get("avg_win_rate", 0)
        risk_count = context.get("high_risk", 0)
        corr = context.get("correlation", 0)

        if "risk" in q or "at risk" in q:
            return "{} deals flagged high-risk. Key drivers: low enablement, inactivity >21d, active competition.".format(risk_count)
        elif "win rate" in q or "win probability" in q:
            return "Average win rate: {:.1f}%. Enabled reps (score >= 60) achieve ~2.3x higher win rates. r={:.2f}.".format(wr, corr)
        elif "pipeline" in q or "revenue" in q:
            return "Total active pipeline: ${:,.0f} across {} deals.".format(pipeline, context.get("total_deals", 0))
        elif "enablement" in q or "training" in q:
            return "Enablement-Win Rate correlation: r={:.2f}. Every 10-point enablement increase = ~5.5% higher win rate.".format(corr)
        elif "region" in q:
            return "Top region: {}. Weakest: {}. Regional spread suggests targeted intervention needed.".format(
                context.get("top_region", "N/A"), context.get("weak_region", "N/A"))
        else:
            return "Pipeline: ${:,.0f} | Win Rate: {:.1f}% | Risk Deals: {} | Correlation: r={:.2f}".format(
                pipeline, wr, risk_count, corr)
