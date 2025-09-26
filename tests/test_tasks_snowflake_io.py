import unittest
from unittest.mock import patch, MagicMock
from tasks.snowflake_io import snowflake_io
import pytest


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
        self.mock_args.region_name = "us-west-2"
        self.mock_args.source = "mock_source"
        self.mock_args.job_name = "mock_job_name"
        self.mock_args.max_workers = 10
        self.pipeline_id = "mock_pipeline_id"
        self.mock_session = mock_session
        self.access_token = "mock_access_token"

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

    @patch('tasks.snowflake_io.SecretsManagerIO.get_secret')
    def test_set_headers(self, mock_get_secret):
        # Mock the logger
        mock_get_secret.return_value = {
            "grant_type": "client_credentials",
            "client_id": "mock_client_id",
            "client_secret": "mock_client_secret",
            "base_url": "https://mock_env.api.crm.dynamics.com"     #todo:change
        }
        
        # Call the set_headers method
        headers = self.snowflake_io_instance.set_headers("mock_access_token")
        self.assertIsNotNone(headers)


    @patch('tasks.https_io.HttpsIo.http_request')
    @patch('tasks.snowflake_io.SecretsManagerIO.get_secret')
    def test_get_access_token(self,  mock_get_secret, mock_requests_post):
        # Mock the logger
       
        # Mock the get_secret method
        mock_get_secret.return_value = {
            "grant_type": "client_credentials",
            "client_id": "mock_client_id",
            "client_secret": "mock_client_secret",
            "base_url": "https://mock_env.api.crm.dynamics.com"
        }
        
        # Mock the response from the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mock_access_token"}
        mock_requests_post.return_value = True, mock_response
        
        # Call the get_access_token method
        access_token = self.snowflake_io_instance.get_access_token(secret_data=mock_get_secret(), access_token=self.access_token)

        self.assertIsNotNone(access_token)

    @patch('tasks.snowflake_io.HttpsIo.http_request')
    @patch('tasks.snowflake_io.set_headers')
    @patch('tasks.snowflake_io.SecretsManagerIO.get_secret')
    def test_transfer_entity_data(self, mock_get_secret, mock_set_headers, mock_http_request):
        
        # Mock the get_secret method
        mock_get_secret.return_value = {
            "grant_type": "client_credentials",
            "client_id": "mock_client_id",
            "client_secret": "mock_client_secret",
            "base_url": "https://mock_env.api.crm.dynamics.com"
        }
        
        # Mock the set_headers method
        mock_set_headers.return_value = {
            'Authorization': 'Bearer mock_access_token',
            'Content-Type': 'application/json'
        }
        
        # Mock the response from the http_request call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "value": [{"id": "1", "name": "Entity1"}, {"id": "2", "name": "Entity2"}],
            "@odata.nextLink": None
        }
        mock_http_request.return_value = (True, mock_response)
        # Call the get_entity_data method
        watermark = "2023-01-01T00:00:00Z"
        secret_data = mock_get_secret.return_value
        source = "snowflake_io"
        
        execution_max_watermark, s3_key = self.snowflake_io_instance.transfer_entity_data(watermark, secret_data, self.access_token, source)
        # Verify the result
        self.assertIsNotNone(execution_max_watermark)
        self.assertIsNotNone(s3_key)
        

        
if __name__ == "__main__":
    unittest.main()        