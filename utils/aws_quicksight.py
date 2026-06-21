"""
Amazon QuickSight Integration — Embedded Analytics & CDK Templates
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class QuickSightManager:
    """QuickSight integration for embedded analytics."""

    def __init__(self, config=None):
        from utils.aws_config import AWSConfig, get_aws_client
        self.config = config or AWSConfig()
        self.client = None
        self.available = False
        if self.config.enable_quicksight_embed:
            self.client = get_aws_client("quicksight", "us-east-1")
            self.available = self.client is not None

    def generate_embed_url(self, user_arn, dashboard_id=None):
        """Generate QuickSight embed URL for registered user."""
        if not self.available:
            return None
        try:
            response = self.client.generate_embed_url_for_registered_user(
                AwsAccountId=self.config.quicksight_account_id,
                UserArn=user_arn,
                ExperienceConfiguration={
                    "Dashboard": {
                        "InitialDashboardId": dashboard_id or self.config.quicksight_dashboard_id
                    }
                }
            )
            return response["EmbedUrl"]
        except Exception as e:
            logger.error("QuickSight embed URL generation failed: %s", e)
            return None

    def configure_rls(self):
        """Row-Level Security rules by group."""
        return {
            "sales-apac-anz": ["ANZ"],
            "sales-apac-asean": ["ASEAN"],
            "sales-apac-india": ["India"],
            "sales-apac-japan": ["Japan"],
            "sales-apac-korea": ["Korea"],
            "sales-apac-china": ["Greater China"],
            "sales-apac-all": ["ANZ", "ASEAN", "India", "Japan", "Korea", "Greater China"],
        }


class QuickSightCDKTemplate:
    """CloudFormation template for full stack deployment."""

    @staticmethod
    def get_cfn_template():
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Sales Gap Analyzer - QuickSight + S3 + Glue Stack",
            "Resources": {
                "DataLakeBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": "sales-gap-analyzer-datalake",
                        "VersioningConfiguration": {"Status": "Enabled"},
                        "BucketEncryption": {
                            "ServerSideEncryptionConfiguration": [{
                                "ServerSideEncryptionByDefault": {
                                    "SSEAlgorithm": "aws:kms"
                                }
                            }]
                        }
                    }
                },
                "GlueDatabase": {
                    "Type": "AWS::Glue::Database",
                    "Properties": {
                        "CatalogId": {"Ref": "AWS::AccountId"},
                        "DatabaseInput": {"Name": "sales_gap_analyzer"}
                    }
                },
                "GlueETLJob": {
                    "Type": "AWS::Glue::Job",
                    "Properties": {
                        "Name": "sales-gap-etl-bronze-to-gold",
                        "Command": {
                            "Name": "glueetl",
                            "PythonVersion": "3",
                            "ScriptLocation": "s3://sales-gap-scripts/etl/bronze_to_gold.py"
                        },
                        "GlueVersion": "4.0",
                        "NumberOfWorkers": 5,
                        "WorkerType": "G.1X"
                    }
                },
                "AthenaWorkGroup": {
                    "Type": "AWS::Athena::WorkGroup",
                    "Properties": {
                        "Name": "sales-gap-analyzer",
                        "WorkGroupConfiguration": {
                            "ResultConfiguration": {
                                "OutputLocation": "s3://sales-gap-analyzer-datalake/athena-results/"
                            }
                        }
                    }
                },
                "QuickSightDataSource": {
                    "Type": "AWS::QuickSight::DataSource",
                    "Properties": {
                        "DataSourceId": "s3-datalake-gold",
                        "Name": "Sales Gap Analyzer - Gold Layer",
                        "Type": "ATHENA"
                    }
                }
            }
        }
