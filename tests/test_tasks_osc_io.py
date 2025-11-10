import unittest
from unittest.mock import patch, MagicMock
<<<<<<< HEAD
from tasks.osc_account_io import osc_account_io
=======
from tasks.osc_io import osc_io
>>>>>>> main
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
<<<<<<< HEAD
        self.osc_io_instance = osc_account_io(boto3_session=mock_session, args=self.mock_args, logger=self.mock_logger, pipeline_id=self.pipeline_id, execution_id="mock_execution_id")
=======
        self.osc_io_instance = osc_io(boto3_session=mock_session, args=self.mock_args, logger=self.mock_logger, pipeline_id=self.pipeline_id, execution_id="mock_execution_id")
>>>>>>> main

    # @patch('tasks.aws_api_io.SecretsManagerIO.get_secret')
    # def test_get_osc_access_token(self,  mock_get_secret):
    #     # Mock the logger
       
    #     # Mock the get_secret method
    #     mock_get_secret.return_value = {
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
        
    #     # Mock the response from the requests.post call
    #     mock_response = MagicMock()
    #     mock_response.status_code = 200
    #     mock_response.json.return_value = {"access_token": "mock_access_token"}

    #     # Call the get_osc_access_token method
    #     osc_access_token = self.osc_io_instance.get_osc_access_token(secret_data=mock_get_secret(), access_token=self.osc_access_token)

    #     self.assertIsNotNone(osc_access_token)


        
if __name__ == "__main__":
    unittest.main()        