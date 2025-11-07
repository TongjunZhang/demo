# tasks/osc_io.py

from tasks.https_io import HttpsIo
import requests
import logging
import argparse
import boto3

class osc_io:
    """
    Class to interact with OSC (Oracle Service Cloud) and handle API requests,
    authentication, and payload management.
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
        Initialize osc_io with arguments, logger, AWS session, pipeline and execution IDs.

        Args:
            args (argparse.Namespace, optional): Script arguments.
            logger (logging.Logger, optional): Logger instance.
            boto3_session (boto3.session.Session, optional): AWS session.
            pipeline_id (str, optional): Pipeline identifier.
            execution_id (int, optional): Execution identifier.
        """
        self.logger = logging.getLogger() if logger is None else logger
        self.boto3_session = boto3.session.Session(
            region_name=args.region_name) if boto3_session is None else boto3_session
        self.args = args
        self.pipeline_id = pipeline_id
        # Remove prefix from pipeline_id for processing
        self.pipeline_id_processing = self.pipeline_id.replace('Marketo_Snowflake_OSC_nonprod_DQ_', '') if self.pipeline_id else None
        self.execution_id = execution_id

    def get_osc_access_token(
            self,
            secret_data: dict,
            access_token: str = None
    ) -> str:
        """
        Obtain an access token from secret data or request a new one.

        Args:
            secret_data (dict): Secret data containing credentials.
            access_token (str, optional): Existing access token.

        Returns:
            str: Access token string.
        """
        my_access_token = None
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Accept": "application/json"
        }
        payload = {
            'grant_type': secret_data["DM_OSC_API_Grant_Type"],
            'client_id': secret_data["DM_OSC_API_Client_ID"],
            'client_secret': secret_data["DM_OSC_API_Client_Secret"],
            'scope': secret_data["DM_OSC_API_Scope"]
        }
            # Make POST request to obtain access token
        _, response = HttpsIo(logger=self.logger).http_request(
            http_method='POST',
            http_url=secret_data["DM_OSC_API_Token_Create_Url"],
            http_head=headers,
            http_data=payload
        )
        self.logger.info('Access token being requested / replaced')
        response_value = response.json()
        my_access_token = response_value.get('access_token')
        return my_access_token

    def create_OSC_Account(self, payload_data: str, access_token: str, secret_data: dict) -> dict:
        """
        Create an account in OSC using the provided payload and access token.

        Args:
            payload_data (str): JSON payload for account creation.
            access_token (str): Bearer token for authentication.

        Returns:
            dict: JSON response from OSC API.
        """
        url = secret_data["DM_OSC_API_Account_Create"]
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {access_token}",
            'Prefer': 'return=representation'
        }
        # Make POST request to create account
        _, response = HttpsIo(logger=self.logger).http_request(
            http_method='POST',
            http_url=secret_data["DM_OSC_API_Account_Create"],
            http_head=headers,
            http_data=payload_data
        )
        return response.json()
