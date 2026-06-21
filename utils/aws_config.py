"""
AWS Configuration & Service Client Factory
Graceful degradation — dashboard works fully without AWS credentials.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AWSConfig:
    """AWS service configuration with APAC defaults."""
    bedrock_region: str = "us-west-2"
    data_regions: Dict[str, str] = field(default_factory=lambda: {
        "ANZ": "ap-southeast-2", "ASEAN": "ap-southeast-1",
        "India": "ap-south-1", "Japan": "ap-northeast-1",
        "Korea": "ap-northeast-2", "Greater China": "cn-north-1"
    })
    s3_bucket_prefix: str = "aws-sales-gap-analyzer"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_embed_model: str = "amazon.titan-embed-text-v2:0"
    quicksight_account_id: str = ""
    quicksight_dashboard_id: str = "sales-gap-analyzer-v2"
    dynamodb_table: str = "SalesGapAnalyzer-Opportunities"
    cloudwatch_namespace: str = "SalesGapAnalyzer/Metrics"
    enable_bedrock: bool = False
    enable_quicksight_embed: bool = False
    enable_s3_persistence: bool = False
    enable_cloudwatch: bool = False

    def __post_init__(self):
        self.quicksight_account_id = os.getenv("AWS_ACCOUNT_ID", "")
        self.enable_bedrock = os.getenv("ENABLE_BEDROCK", "false").lower() == "true"
        self.enable_quicksight_embed = os.getenv("ENABLE_QS_EMBED", "false").lower() == "true"
        self.enable_s3_persistence = os.getenv("ENABLE_S3", "false").lower() == "true"
        self.enable_cloudwatch = os.getenv("ENABLE_CW", "false").lower() == "true"


def get_aws_client(service_name, region=None):
    """Factory for AWS service clients with graceful degradation."""
    try:
        import boto3
        from botocore.config import Config
        config = Config(
            region_name=region or "ap-southeast-1",
            retries={"max_attempts": 3, "mode": "adaptive"}
        )
        session = boto3.Session()
        client = session.client(service_name, config=config)
        sts = session.client("sts")
        sts.get_caller_identity()
        return client
    except Exception as e:
        logger.warning("AWS client for %s failed: %s. Running in local mode.", service_name, e)
        return None


class AWSServiceStatus:
    """Track availability of AWS services."""

    def __init__(self):
        self.services = {}

    def check_service(self, name, client):
        available = client is not None
        status = {
            "name": name,
            "available": available,
            "status": "Connected" if available else "Local Mode"
        }
        self.services[name] = status
        return status

    def summary(self):
        connected = sum(1 for s in self.services.values() if s["available"])
        total = len(self.services)
        return "{}/{} AWS services connected".format(connected, total)
