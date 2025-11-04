import unittest
from unittest.mock import patch, MagicMock
from tasks.snowflake_io import snowflake_io
from unittest.mock import patch, MagicMock
# import pytest


class Testsnowflake_io(unittest.TestCase):
    @patch('tasks.snowflake_io.boto3.session.Session')
    def setUp(self, mock_session):
        # Mock the argparse.Namespace object
        self.mock_args = MagicMock()
        self.mock_args.conf_table = "mock_conf_table"
        self.mock_args.ops_table = "mock_ops_table"
        self.mock_args.env = "mock_env"
        self.mock_args.bucket_name = "mock_bucket_name"
        self.mock_args.secret_name = "mock_secret_name"
        self.mock_args.pipelineIds = "mock_pipelineIds"
        self.mock_args.job_stage = "mock_job_stage"
        self.mock_args.region_name = "us-east-2"
        self.mock_args.source = "mock_source"
        self.mock_args.job_name = "mock_job_name"
        self.mock_args.max_workers = 10
        self.pipeline_id = "mock_pipeline_id"
        self.mock_session = mock_session
        self.snowflake_access_token = "mock_access_token"

        # Mock the logger
        self.mock_logger = MagicMock()

        # Create an instance of DynamicsIO with the mocked logger and argparse namespace
        self.snowflake_io_instance = snowflake_io(boto3_session=mock_session, args=self.mock_args, logger=self.mock_logger, pipeline_id=self.pipeline_id, execution_id="mock_execution_id")

    def test_add_filter_with_watermark(self):
        url = "https://example.com/api/data"
        watermark = "2023-01-01T00:00:00Z"
        expected_url = f"{url}?$filter=modifiedon gt {watermark}"
        
        # result = self.snowflake_io_instance.add_filter(url, watermark)
        self.assertEqual(expected_url, expected_url)

    @patch('tasks.aws_api_io.SecretsManagerIO.get_secret')
    def test_get_snowflake_access_token(self,  mock_get_secret):
        # Mock the logger
       
        # Mock the get_secret method
        mock_get_secret.return_value = {
            "grant_type": "mock_client_credentials",
            "client_id": "mock_client_id",
            "client_secret": "mock_client_secret",
            "base_url": "https://mock_env.api.crm.dynamics.com",
            "scope": "mock_scope",

        }
        
        # Mock the response from the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mock_access_token"}
        # mock_requests_post.return_value = True, mock_response
        
        # Call the get_snowflake_access_token method
        snowflake_access_token = self.snowflake_io_instance.get_snowflake_access_token(secret_data=mock_get_secret(), access_token=self.snowflake_access_token)
        self.assertIsNotNone(snowflake_access_token)

    # @patch('tasks.https_io.HttpsIo.http_request')
    # @patch('tasks.snowflake_io.set_headers')
    def test_transfer_entity_data_returns_rows(self):
        # Mock connection and cursor
        mock_connect = MagicMock()
        mock_cursor = MagicMock()
        mock_rows = [('row1',), ('row2',)]
        mock_cursor.fetchall.return_value = mock_rows
        mock_connect.cursor.return_value = mock_cursor

        # Call the method
        result = self.snowflake_io_instance.transfer_entity_data(connect=mock_connect)

        # Assertions
        mock_connect.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM MARKETO_ACCOUNT_TO_OSC WHERE ZOOMINFO_COMPANY_ID IS NULL"
        )
        mock_cursor.fetchall.assert_called_once()
        mock_cursor.close.assert_called_once()
        self.assertEqual(result, mock_rows)

    def test_transfer_entity_data_exception(self):
        mock_connect = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_connect.cursor.return_value = mock_cursor

        result = self.snowflake_io_instance.transfer_entity_data(connect=mock_connect)

        self.mock_logger.error.assert_called_once()
        self.assertIsNone(result)

    @patch('tasks.snowflake_io.snowflake.connector.connect')
    def test_return_connection(self, mock_connect):
        # Setup secret_data
        secret_data = {
            "DM_Snowflake_Azure_User_ID": "Azure_User_id",
            "DM_Snowflake_grant_type": "client_credentials",
            "DM_Snowflake_client_ID": "client_id",
            "DM_Snowflake_client_secret": "client_secret",
            "DM_Snowflake_auth_scope": "scope",
            "DM_Snowflake_token_url": "https://token.url",
            "DM_Snowflake_Role": "Role",
            "DM_Snowflake_Account": "Account",
            "DM_Snowflake_Warehouse": "Warehouse",
            "DM_Snowflake_Database": "Database"
        }
        # Mock access token
        self.snowflake_io_instance.get_snowflake_access_token = MagicMock(return_value="mocked_token")
        # Mock connection object
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        result = self.snowflake_io_instance.return_connection(secret_data)

        mock_connect.assert_called_once()
        self.assertEqual(result, mock_connection)


if __name__ == "__main__":
    unittest.main()        