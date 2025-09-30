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

    def get_items(self,
                  table_name: str,
                  key: Dict,
                  fields: str = None,
                  scan_column_forward: str = None
                  ):
        """
        Get the item from the table

        Args:
            table_name: name of the table
            key: key to get the item
            fields: fields to get
            scan_column_forward: column to sort the records on

        Returns:
            item object
        """
        table = self.set_table(table_name)
        scan_kwargs = {}
        ## building the search key conditions.
        key_condition = Key(list(key.keys())[0]).eq(list(key.values())[0])
        for k, v in list(key.items())[1:]:
            key_condition &= Attr(k).eq(v)

        scan_kwargs['FilterExpression'] = key_condition
        if fields:
            scan_kwargs['ProjectionExpression'] = fields

        self.logger.info("Getting items from table %s with filter of %s" % (table_name, key))
        complete_results = []
        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            records = table.scan(**scan_kwargs)
            complete_results.extend(records['Items'])
            start_key = records.get('LastEvaluatedKey', None)
            done = start_key is None

        self.logger.info(
            "Got items from table %s with filter of %s, record count: %s" % (table_name, key, len(complete_results)))
        if scan_column_forward and complete_results:
            complete_results.sort(key=lambda x: x[scan_column_forward], reverse=True)
        return complete_results

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
        return payload

    def set_table(self, table_name: str):
        """
        Set the dynamodb table

        Args:
            table_name (str): Dyanmodb table name

        Returns:
            _type_: Dynamodb table object
        """
        self.logger.info(f"Setting osc account {table_name}")
        return self.resource.Table(table_name)

    def get_latest_watermark(
        self,
        pipeline_id: str,
        table_name: str = None
    ) -> str:
        """
        Get the latest watermark for the pipeline.

        Args:
            pipeline_id (str): The pipeline ID.
            osc_account (str, optional): OSC account info.

        Returns:
            str: The latest watermark.
        """
        default_watermark = "2025-01-01T00:00:00Z"
        try:
            table = self.set_table(table_name)
            self.logger.info('searching by partition key for pipeline_id: %s' % pipeline_id)
            items = table.query(KeyConditionExpression=Key('pipelineId').eq(pipeline_id),
                                ScanIndexForward=False)
            self.logger.info('pipeline_id: %s - count: %s' % (pipeline_id, items.get('Count', 0)))
            items = items.get('Items', [])
            if items and "dynamicObjects" in items[0]:
                watermark = items[0].get('dynamicObjects', {}).get('cdc_rpl_last_update_date', None)
                if not watermark:
                    self.logger.info('No watermark found in Dynamodb, setting watermark for pipeline %s to default %s' % (pipeline_id, default_watermark))
                    watermark= default_watermark
            else:
                self.logger.info('No results from Dynamodb found, setting watermark for pipeline %s to default %s' % (pipeline_id, default_watermark))
                watermark = default_watermark
        except Exception as e:
            self.logger.error('error in getting watermark for pipeline %s: %s, using default %s' % (pipeline_id, e, default_watermark))
            watermark = default_watermark
        self.logger.info('watermark for pipeline %s is %s' % (pipeline_id, watermark))
        return watermark

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
