import unittest
from unittest.mock import patch, MagicMock
from tasks.osc_io import osc_io
# import pytest



class testosc_io(unittest.TestCase):
    @patch('tasks.osc_io.boto3.session.Session')
    # @patch('tasks.osc_io.logging.getLogger')
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
        self.osc_access_token = "mock_access_token"

        # Mock the logger
        self.mock_logger = MagicMock()

        # Create an instance of osc_io with the mocked logger and argparse namespace
        self.osc_io_instance = osc_io(boto3_session=mock_session, args=self.mock_args, logger=self.mock_logger, pipeline_id=self.pipeline_id, execution_id="mock_execution_id")

    @patch('tasks.aws_api_io.SecretsManagerIO.get_secret')
    def test_get_osc_access_token(self,  mock_get_secret):
        # Mock the logger
       
        # Mock the get_secret method
        mock_get_secret.return_value = {
            "snowflake_token_url" : "https://mock_token.url",
            "snowflake_auth_scope" : "mock_snowflake_auth_scope",
            "snowflake_client_id": "mock_snowflake_client_id",
            "snowflake_client_secret" : "mock_snowflake_client_secret",
            "snowflake_grant_type" : "mock_client_credentials",
            "snowflake_database" : "mock_snowfake-database",
            "snowflake_account" : "mock_snowflake_account",
            "snowflake_user_id" : "mock_snowflake_user_id",
            "snowflake_role" : "mock_snowflake_role",
            "snowflake_warehouse" : "mock_snowflake_warehouse",
            "osc_account" : "https://mock_osc_account.url",
            "osc_token_url" : "https://mock_osc_taken.url",
            "osc_client_id" : "mock_osc_client_id",
            "osc_client_secret": "mock_osc_client_secret",
            "osc_scope": "mock_osc_scope",
            "osc_grant_type": "mock_osc_grant_type"
        }
        
        # Mock the response from the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mock_access_token"}

        # Call the get_osc_access_token method
        osc_access_token = self.osc_io_instance.get_osc_access_token(secret_data=mock_get_secret(), access_token=self.osc_access_token)

        self.assertIsNotNone(osc_access_token)


        
if __name__ == "__main__":
    unittest.main()        