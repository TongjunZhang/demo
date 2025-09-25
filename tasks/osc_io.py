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

    def get_access_token(
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
        my_access_token = access_token
        if not my_access_token:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Accept": "application/json"
            }
            payload = {
                'grant_type': 'client_credentials',
                'client_id': 'db80b2c6-bfdc-49af-9627-f63b73b85ada',
                'client_secret': 'PBTRXCa6lnE_-G6M5S-e8H5T0ek5.A3E-D',
                'scope': 'https://vault.azure.net/.default'
            }
            # Make POST request to obtain access token
            _, response = HttpsIo(logger=self.logger).http_request(
                http_method='POST',
                http_url='https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/token',
                http_head=headers,
                http_data=payload
            )
            self.logger.info('Access token being requested / replaced')
            my_access_token = response.json().get('access_token', "")
        return my_access_token

    def set_headers(self, access_token: str) -> dict:
        """
        Set headers for OSC API requests.

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

    def create_OSC_Account(self, payload_data: str, access_token: str) -> dict:
        """
        Create an account in OSC using the provided payload and access token.

        Args:
            payload_data (str): JSON payload for account creation.
            access_token (str): Bearer token for authentication.

        Returns:
            dict: JSON response from OSC API.
        """
        url = "https://crowncastle-dev.crm.dynamics.com/api/data/v9.1/accounts"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {access_token}",
            'Prefer': 'return=representation'
        }
        # Make POST request to create account
        response = requests.request("POST", url, headers=headers, data=payload_data, verify=False)
        return response.json()
