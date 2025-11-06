# tasks/snowflake_io.py

from tasks.https_io import HttpsIo
# from tasks.aws_api_io import SecretsManagerIO, MarketoETL
import logging
import boto3
import argparse
import snowflake.connector
# from tasks.osc_io import osc_io
import json

EXECUTION_STAGE = 0
EXECUTION_STATE = 1

class snowflake_io:
    """
    Class to interact with Snowflake, handle authentication, and process entity data.
    """
    def __init__(
        self,
        args: argparse.Namespace,
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
        self.pipeline_id_processing = self.pipeline_id.replace('Marketo_Snowflake_OSC_', '') if self.pipeline_id else None
        self.execution_id = execution_id

    def get_snowflake_access_token(
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
            response = HttpsIo(logger=self.logger).http_request(
                http_method='POST',
                http_url=secret_data.get('DM_Snowflake_token_url'),
                http_head=headers,
                http_data=payload
            )
            self.logger.info('Access token being requested / replaced')
            response_value = json.loads(response)
            my_access_token = response_value.get('access_token')
        return my_access_token

    def return_connection(self, secret_data) -> snowflake.connector.connection.SnowflakeConnection:
        """
        Establish and return a Snowflake connection using secret data.

        Args:
            secret_data (dict): Secret data containing connection parameters.

        Returns:
            SnowflakeConnection: Active Snowflake connection.
        """
        access_token = self.get_snowflake_access_token(secret_data=secret_data)

        ctx = snowflake.connector.connect(
            user=secret_data["DM_Snowflake_Azure_User_ID"],
            role=secret_data["DM_Snowflake_Role"],                  
            account=secret_data["DM_Snowflake_Account"],                          
            warehouse=secret_data["DM_Snowflake_Warehouse"],               
            database=secret_data['DM_Snowflake_Database'],                 
            schema="DATA_MANAGEMENT",                        
            autocommit=True,                                
            authenticator="OAuth",                           
            token=access_token
        )
        return ctx

    def transfer_entity_data(
        self,
        connect: snowflake.connector.connection.SnowflakeConnection = None
    ) -> list:
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
        datacursor = connect.cursor()
        rows = None
        try:
            # Query for rows where ACCOUNT_NUMBER is NULL
            datacursor.execute("SELECT * FROM MARKETO_ACCOUNT_TO_OSC WHERE ACCOUNT_NUMBER IS NULL OR ACCOUNT_NUMBER =''")
            rows = datacursor.fetchall()
            self.logger.info('got zoominfo data')
            datacursor.close()
        except Exception as e:
            self.logger.error(f"Error getting execution data from ZoomInfo table: {e}")
        return rows

    def update_osc_account(self,
        # watermark: str = None,
        connect: snowflake.connector.connection.SnowflakeConnection = None,
        accountnumber: str = None,
        zoominfo_company_id:str = None
        ):
        datacursor = connect.cursor()
        sqlstr = "UPDATE MARKETO_ACCOUNT_TO_OSC SET ACCOUNT_NUMBER = '" + f'{accountnumber}' + "' WHERE ZOOMINFO_COMPANY_ID = '" + f'{zoominfo_company_id}' + "'"
        datacursor.execute(sqlstr)
        datacursor.execute("COMMIT")
        datacursor.close()
        print(accountnumber)