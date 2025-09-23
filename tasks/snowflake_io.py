# tasks/snowflake_io.py

from tasks.https_io import HttpsIo
from tasks.aws_api_io import SecretsManagerIO, MarketoETL
import logging
import json
import boto3
import argparse
import snowflake.connector
from tasks.osc_io import osc_io

EXECUTION_STAGE = 0
EXECUTION_STATE = 1

class snowflake_io:
    """
    Class to interact with Snowflake, handle authentication, and process entity data.
    """
    def __init__(
        self,
        args: argparse.Namespace = None,
        logger: logging.Logger = None,
        boto3_session: boto3.session.Session = None,
        pipeline_id: str = None,
        execution_id: int = None
    ):
        """
        Initialize snowflake_io with arguments, logger, AWS session, pipeline and execution IDs.

        Args:
            args (argparse.Namespace, optional): Script arguments.
            logger (logging.Logger, optional): Logger instance.
            boto3_session (boto3.session.Session, optional): AWS session.
            pipeline_id (str, optional): Pipeline identifier.
            execution_id (int, optional): Execution identifier.
        """
        self.logger = logging.getLogger() if logger is None else logger
        self.boto3_session = boto3.session.Session(region_name=args.region_name) if boto3_session is None else boto3_session
        self.args = args
        self.pipeline_id = pipeline_id
        # Remove prefix from pipeline_id for processing
        self.pipeline_id_processing = self.pipeline_id.replace('Marketo_Snowflake_OSC_nonprod_DQ_', '') if self.pipeline_id else None
        self.execution_id = execution_id

    def set_headers(self, access_token: str) -> dict:
        """
        Set headers for Snowflake API requests.

        Args:
            access_token (str): Bearer token for authentication.

        Returns:
            dict: Headers for the request.
        """
        return {
            'Authorization': f'Bearer {access_token}',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8'
        }

    def get_access_token(
        self,
        secret_data: dict,
        access_token: str = None
    ) -> str:
        """
        Get the access token from the secret data or request a new one.

        Args:
            secret_data (dict): Secret data containing credentials.
            access_token (str, optional): Existing access token.

        Returns:
            str: Access token string.
        """
        my_access_token = access_token
        if not my_access_token:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            payload = {
                'grant_type': secret_data["DM_Snowflake_grant_type"],
                'client_id': secret_data["DM_Snowflake_client_ID"],
                'client_secret': secret_data["DM_Snowflake_client_secret"],
                'scope': secret_data["DM_Snowflake_auth_scope"]
            }
            # Make POST request to obtain access token
            _, response = HttpsIo(logger=self.logger).http_request(
                http_method='POST',
                http_url=secret_data.get('DM_Snowflake_token_url'),
                http_head=headers,
                http_data=payload
            )
            self.logger.info('Access token being requested / replaced')
            my_access_token = response.json().get('access_token', "")
        return my_access_token

    def return_connection(self, secret_data) -> snowflake.connector.connection.SnowflakeConnection:
        """
        Establish and return a Snowflake connection using secret data.

        Args:
            secret_data (dict): Secret data containing connection parameters.

        Returns:
            SnowflakeConnection: Active Snowflake connection.
        """
        ctx = snowflake.connector.connect(
            user='0baab986-1a68-4191-953b-147d8fc0c71c',     # Replace with secret_data["DM_Snowflake_User_ID"]
            role="DATA_MANAGEMENT_RO_ROLE",                  # Replace with secret_data['DM_Snowflake_role']
            account="ccic-mainnew",                          # Replace with secret_data['DM_Snowflake_account']
            warehouse="BUSINESS_REPORTING_WH",               # Replace with secret_data['DM_Snowflake_warehouse']
            database="CDWDEV",                               # Replace with secret_data['DM_Snowflake_database']
            schema="DATA_MANAGEMENT",                        # Replace with secret_data['DM_Snowflake_schema']
            autocommit=True,                                 # Replace with secret_data['DM_Snowflake_autocommit']
            authenticator="OAuth",                           # Replace with secret_data['DM_Snowflake_authenticator']
            token=self.get_access_token(self.get_secret(self.args.secret_name))
        )
        return ctx

    def transfer_entity_data(
        self,
        watermark: str = None,
        secret_data: dict = None,
        access_token: str = None,
        source: str = 'snowflake'
    ):
        """
        Fetch entity data from Snowflake and process it for OSC.

        Args:
            watermark (str, optional): Watermark to filter data. Defaults to None.
            secret_data (dict, optional): Secret data for connection. Defaults to None.
            access_token (str, optional): Access token for authentication. Defaults to None.
            source (str, optional): Source of data. Defaults to 'snowflake'.

        Returns:
            None
        """
        connect = self.return_connection(secret_data)
        datacursor = connect.cursor()
        rows = None
        try:
            # Query for rows where ZOOMINFO_COMPANY_ID is NULL
            datacursor.execute("SELECT * FROM MARKETO_ACCOUNT_TO_OSC WHERE ZOOMINFO_COMPANY_ID IS NULL")
            rows = datacursor.fetchall()
            oscaccesstoken = None
            for row in rows:
                # Create payload and send to OSC
                inpayload = MarketoETL.put_item(row)
                rt = osc_io.create_OSC_Account(inpayload, oscaccesstoken)
                accountnumber = rt.get('accountnumber')
                # Update Snowflake table with new account number
                sqlstr = (
                    "UPDATE MARKETO_ACCOUNT_TO_OSC SET ACCOUNT_NUMBER = '" +
                    f'{accountnumber}' +
                    "' WHERE ZOOMINFO_COMPANY_ID = '" +
                    f'{row[0]}' +
                    "'"
                )
                datacursor.execute(sqlstr)
                datacursor.execute("COMMIT")
                print(accountnumber)
                self.logger.info("logging info: Account number:" + f'{accountnumber}')
        except Exception as e:
            self.logger.error(f"Error getting execution data from ZoomInfo table: {e}")
            return
