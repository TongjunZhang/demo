import unittest
from unittest.mock import patch, MagicMock
from tasks.aws_snowflake_io import AwsSnowflakeIo
from unittest.mock import patch, MagicMock

class TestAwsSnowflakeIo(unittest.TestCase):
    @patch('tasks.aws_snowflake_io.boto3.session.Session')
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
        self.snowflake_io_instance = AwsSnowflakeIo(boto3_session=mock_session, args=self.mock_args, logger=self.mock_logger, pipeline_id=self.pipeline_id, execution_id="mock_execution_id")

    # @patch('tasks.aws_api_io.SecretsManagerIO.get_secret')
    # def test_get_snowflake_access_token(self, mock_get_secret):
    #     # Mock the logger
       
    #     # Mock the get_secret method
    #     mock_get_secret.return_value = {
    #         "DM_Snowflake_token_url" : "https://mock_token.url",
    #         "DM_Snowflake_auth_scope" : "mock_snowflake_auth_scope",
    #         "DM_Snowflake_client_ID" : "mock_snowflake_client_id",
    #         "DM_Snowflake_client_secret" : "mock_snowflake_client_secret",
    #         "DM_Snowflake_grant_type" : "mock_client_credentials",
    #         "DM_Snowflake_Database" : "mock_snowfake-database",
    #         "DM_Snowflake_Account" : "mock_snowflake_account",
    #         "DM_Snowflake_Azure_User_ID" : "mock_snowflake_user_id",
    #         "DM_Snowflake_Role" : "mock_snowflake_role",
    #         "DM_Snowflake_Warehouse" : "mock_snowflake_warehouse",
    #         "DM_OSC_API_Account_Create" : "https://mock_osc_account.url",
    #         "DM_OSC_API_Token_Create_Url" : "https://mock_osc_taken.url",
    #         "DM_OSC_API_Client_ID" : "mock_osc_client_id",
    #         "DM_OSC_API_Client_Secret": "mock_osc_client_secret",
    #         "DM_OSC_API_Scope": "mock_osc_scope",
    #         "DM_OSC_API_Grant_Type": "mock_osc_grant_type"
    #     }
        
    #     # Mock the response from the requests.post call
    #     mock_response = MagicMock()
    #     mock_response.status_code = 200
    #     mock_response.json.return_value = {"access_token": "mock_access_token"}
    #     # mock_requests_post.return_value = True, mock_response
        
    #     # Call the get_snowflake_access_token method
    #     snowflake_access_token = self.snowflake_io_instance.get_snowflake_access_token(secret_data=mock_get_secret(), access_token=self.snowflake_access_token)
    #     self.assertIsNotNone(snowflake_access_token)

    # @patch('tasks.https_io.HttpsIo.http_request')
    # @patch('tasks.aws_snowflake_io.set_headers')
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
            "SELECT * FROM MARKETO_ACCOUNT_TO_OSC WHERE ACCOUNT_NUMBER IS NULL OR ACCOUNT_NUMBER =''"
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

    # @patch('tasks.aws_snowflake_io.snowflake.connector.connect')
    # def test_return_connection(self, mock_connect):
    #     # Setup secret_data
    #     secret_data = {
    #         "DM_Snowflake_token_url" : "https://mock_token.url",
    #         "DM_Snowflake_auth_scope" : "mock_snowflake_auth_scope",
    #         "DM_Snowflake_client_ID": "mock_snowflake_client_id",
    #         "DM_Snowflake_client_secret" : "mock_snowflake_client_secret",
    #         "DM_Snowflake_grant_type" : "mock_client_credentials",
    #         "DM_Snowflake_Database" : "mock_snowfake-database",
    #         "DM_Snowflake_Account" : "mock_snowflake_account",
    #         "DM_Snowflake_Azure_User_ID" : "mock_snowflake_user_id",
    #         "DM_Snowflake_Role" : "mock_snowflake_role",
    #         "DM_Snowflake_Warehouse" : "mock_snowflake_warehouse",
    #         "DM_OSC_API_Account_Create" : "https://mock_osc_account.url",
    #         "DM_OSC_API_Token_Create_Url" : "https://mock_osc_taken.url",
    #         "DM_OSC_API_Client_ID" : "mock_osc_client_id",
    #         "DM_OSC_API_Client_Secret": "mock_osc_client_secret",
    #         "DM_OSC_API_Scope": "mock_osc_scope",
    #         "DM_OSC_API_Grant_Type": "mock_osc_grant_type"
    #     }
    #     # Mock access token
    #     self.snowflake_io_instance.get_snowflake_access_token = MagicMock(return_value="mocked_token")
    #     # Mock connection object
    #     mock_connection = MagicMock()
    #     mock_connect.return_value = mock_connection

    #     result = self.snowflake_io_instance.return_connection(secret_data)

    #     mock_connect.assert_called_once()
    #     self.assertEqual(result, mock_connection)


if __name__ == "__main__":
    unittest.main()        