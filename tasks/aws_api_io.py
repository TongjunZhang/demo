# tasks/aws_api_io.py

import boto3
from typing import Dict
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging
import json
import argparse
from datetime import datetime

# Class to interact with Marketo ETL and DynamoDB
class MarketoETL:
    def __init__(
        self,
        args: argparse.Namespace,
        boto3_session: boto3.session.Session = None,
        logger: logging.Logger = None
    ):
        """
        Initialize MarketoETL with AWS session, logger, and arguments.

        Args:
            args (argparse.Namespace): Command-line arguments.
            boto3_session (boto3.session.Session, optional): AWS session.
            logger (logging.Logger, optional): Logger instance.
        """
        self.boto3_session = (
            boto3.session.Session(region_name=args.region_name)
            if boto3_session is None else boto3_session
        )
        self.client = self.boto3_session.client(
            service_name='secretsmanager'
        )
        self.args_u=args
        # Resource for marketoETL
        # self.resource = self.boto3_session.resource('secretsmanager')
        self.logger = logging.getLogger() if logger is None else logger
    def get_latest_watermark(
        self, 
        pipeline_id: str
    ) -> str:
        """
        Get the latest watermark for the pipeline
        Args:
            pipeline_id: str: the pipeline id
            table_name: str: the table name
        Returns:
            str: the latest watermark
        """
        default_watermark = "1969-01-01T00:00:00Z"
        watermark = str(datetime.now()) + "_" + pipeline_id
        self.logger.info('searching by partition key for pipeline_id: %s' % pipeline_id)
  
        return watermark
    def put_item(self, row:list = None) -> str:
        """
        Create a payload from a ZoomInfo row.

        Args:
            row: List containing company data.

        Returns:
            str: JSON payload for the item.
        """
        address1_city = row[6]
        address1_line1 = row[5]
        address1_postalcode = row[7]
        cci_address1stateid_value = row[3]
        name = row[4]
        websiteurl = row[1]

        payload = json.dumps({
            "ownerid@odata.bind": "/systemusers(93b90868-8652-ea11-a81a-000d3a579b7d)",
            "name": name,
            "cci_businesssector": "123",
            "address1_city": address1_city,
            "address1_line1": address1_line1,
            "address1_postalcode": address1_postalcode,
            "address1_stateorprovince": cci_address1stateid_value,
            "statecode": 0,
            "telephone1": "1231231232",
            "websiteurl": websiteurl,
            "address1_composite": "123 Canonsburg 15317"
        })

        self.logger.info('put item from Snowflake: %s' % (row[0]))

        return payload


# Class to interact with AWS Secrets Manager
class SecretsManagerIO:
    """
    Handles fetching secrets from AWS Secrets Manager.
    """
    def __init__(
        self,
        args: argparse.Namespace,
        boto3_session: boto3.session.Session = None,
        logger: logging.Logger = None
    ) -> None:
        self.boto3_session = (
            boto3.session.Session(region_name=args.region_name)
            if boto3_session is None else boto3_session
        )
        self.client = self.boto3_session.client('secretsmanager')
        self.logger = logging.getLogger() if logger is None else logger
        self.args_u=args

    def get_secret(self, secret_name: str = None) -> Dict:
        """
        Retrieve a secret from AWS Secrets Manager.

        Args:
            secret_name (str): The name of the secret.

        Returns:
            Dict: The secret value as a dictionary.
        """
        self.logger.info("Getting secret %s" % secret_name)
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response['SecretString'])
            self.logger.info("Secret fetched successfully")
            return secret
        except ClientError as e:
            self.logger.error(f"Failed to fetch secret for {secret_name}: {e}")
            if self.args_u.env == 'dev':
                secret = {
                    "DM_Snowflake_token_url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/v2.0/token",
                    "DM_Snowflake_auth_scope" : "https://crowncastle.com/bde23c60-815b-4bcb-86ff-95b5d57bf3fd-SnowflakeOAuthForServiceAccounts/.default",
                    "DM_Snowflake_client_ID" : "f9d84658-0724-46b8-80cc-7719d413ef88",
                    "DM_Snowflake_client_secret"  : "VT7939Jpp5lgBfpNyaLd2rYoCpGhIQsMj2xStgWyGrc=",
                    "DM_Snowflake_grant_type" : "client_credentials",
                    "DM_Snowflake_Database" : "CDWDEV",
                    "DM_Snowflake_Account" : "ccic-mainnew",
                    "DM_Snowflake_Azure_User_ID" : "0baab986-1a68-4191-953b-147d8fc0c71c",
                    "DM_Snowflake_Role" : "DATA_MANAGEMENT_RO_ROLE",
                    "DM_Snowflake_Warehouse" : "BUSINESS_REPORTING_WH",
                    "DM_OSC_API_Account_Create" : "https://crowncastle-dev.crm.dynamics.com/api/data/v9.1/accounts",
                    "DM_OSC_API_Token_Create_Url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/token",
                    "DM_OSC_API_Client_ID" : "db80b2c6-bfdc-49af-9627-f63b73b85ada",
                    "DM_OSC_API_Client_Secret" : "PBTRXCa6lnE_-G6M5S-e8H5T0ek5.A3E-D",
                    "DM_OSC_API_Scope" : "https://vault.azure.net/.default",
                    "DM_OSC_API_Grant_Type" : "client_credentials"
                }
            elif self.args_u.env == 'prd':
                    secret = {
                    "DM_Snowflake_token_url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/v2.0/token",
                    "DM_Snowflake_auth_scope" : "https://crowncastle.com/bde23c60-815b-4bcb-86ff-95b5d57bf3fd-SnowflakeOAuthForServiceAccounts/.default",
                    "DM_Snowflake_client_ID" : "625e68db-fb5d-4b5e-96e6-0a5dc0eb62da",
                    "DM_Snowflake_client_secret"  : "scoUzM34N+72s8ArjShRYARdwUcgr9ATJ8cT99IdjpA=",
                    "DM_Snowflake_grant_type" : "client_credentials",
                    "DM_Snowflake_Database" : "CDWPRD",
                    "DM_Snowflake_Account" : "ccic-mainnew",
                    "DM_Snowflake_Azure_User_ID" : "9e33ff8b-da14-46ce-bcfb-d2bc6cdf9f23",
                    "DM_Snowflake_Role" : "DATA_MANAGEMENT_RO_ROLE",
                    "DM_Snowflake_Warehouse" : "BUSINESS_REPORTING_WH",
                    "DM_OSC_API_Account_Create" : "https://crowncastle-dev.crm.dynamics.com/api/data/v9.1/accounts",
                    "DM_OSC_API_Token_Create_Url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/token",
                    "DM_OSC_API_Client_ID" : "d9f4fcfc-a3b0-49e7-8a74-c0770dd6e381",
                    "DM_OSC_API_Client_Secret" : "CqZoRq_EzmvoEvP-_oN.s8.z21~J7p7ZeC",
                    "DM_OSC_API_Scope" : "https://vault.azure.net/.default",
                    "DM_OSC_API_Grant_Type" : "client_credentials"
                }
            else:
                secret = None
            return secret
