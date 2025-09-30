# tasks/aws_api_io.py

import boto3
from typing import Dict
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import logging
import json
import argparse

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
            service_name='secretsmanager',
            region_name=args.region_name
        )
        # Resource for marketoETL
        self.resource = self.boto3_session.resource('secretsmanager')
        self.logger = logging.getLogger() if logger is None else logger

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
            return None
