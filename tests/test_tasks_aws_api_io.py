from unittest.mock import MagicMock
import boto3
import logging
import argparse
from tasks.aws_api_io import MarketoETL, SecretsManagerIO
import unittest
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import json


class TestMarketoETL(unittest.TestCase):
    def setUp(self):
        # Setup mock arguments
        self.args = argparse.Namespace()
        self.args.region_name = 'us-east-1'
        
        # Setup mock session
        self.mock_session = MagicMock(spec=boto3.Session)
        self.mock_resource = MagicMock()
        self.mock_table = MagicMock()
        self.mock_session.resource.return_value = self.mock_resource
        self.mock_resource.Table.return_value = self.mock_table
        self.mock_logger = MagicMock()        
        # Create MarketoETL instance with mocked session
        self.dynamo_io = MarketoETL(args=self.args, boto3_session=self.mock_session)

    def test_put_item(self):
        """Test putting an item into DynamoDB table"""
        # Setup test data
        table_name = "test_table"
        test_item = {"id": "123", "data": "test_data"}
        
        # Configure the mock table's put_item method
        self.mock_table.put_item.return_value = {}
        
        # Call the method
        self.dynamo_io.put_item(table_name, test_item)
        
        # Verify table was set with correct name
        self.mock_resource.Table.assert_called_once_with(table_name)
        
        # Verify put_item was called with correct item
        self.mock_table.put_item.assert_called_once_with(Item=test_item)

    def test_put_item_logs_info(self):
        """Test that put_item logs the operation"""
        # Setup test data
        table_name = "test_table"
        test_item = {"id": "123", "data": "test_data"}
        
        # Replace the logger with our mock
        self.dynamo_io.logger = self.mock_logger
        
        # Call the method
        self.dynamo_io.put_item(table_name, test_item)
        
        # Verify logging calls
        self.mock_logger.info.assert_any_call(f"Setting dynamodb table {table_name}")
        self.mock_logger.info.assert_any_call(
            'put item in dynamodb table: %s Item: %s' % (table_name, test_item)
        )

    def test_get_latest_watermark(self):
        """Test successful watermark retrieval"""
        # Setup test data
        pipeline_id = "test_pipeline"
        table_name = "test_table"
        expected_watermark = "2023-01-01T00:00:00Z"
        
        # Mock query response
        mock_response = {
            'Items': [{
                'pipelineId': pipeline_id,
                'dynamicObjects': {
                    'cdc_rpl_last_update_date': expected_watermark
                }
            }],
            'Count': 1
        }
        self.mock_table.query.return_value = mock_response
        
        # Test
        result = self.dynamo_io.get_latest_watermark(pipeline_id, table_name)
        
        # Verify
        self.assertEqual(result, expected_watermark)
        self.mock_table.query.assert_called_once_with(
            KeyConditionExpression=Key('pipelineId').eq(pipeline_id),
            ScanIndexForward=False
        )


class TestSecretsManagerIO:
    def setup_method(self):
        """Setup test fixtures before each test method"""
        self.args = argparse.Namespace(region_name='us-east-1')
        self.mock_session = MagicMock(spec=boto3.Session)
        self.mock_client = MagicMock()
        self.mock_session.client.return_value = self.mock_client
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.secrets_manager = SecretsManagerIO(
            args=self.args,
            boto3_session=self.mock_session,
            logger=self.mock_logger
        )

    def test_get_secret_success(self):
        """Test successful retrieval of a secret"""
        # Setup
        secret_name = "test-secret"
        expected_secret = {"username": "testuser", "password": "testpass"}
        self.mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(expected_secret)
        }

        # Execute
        result = self.secrets_manager.get_secret(secret_name)

        # Verify
        assert result == expected_secret
        self.mock_client.get_secret_value.assert_called_once_with(SecretId=secret_name)
        self.mock_logger.info.assert_any_call(f"Getting secret {secret_name}")
        self.mock_logger.info.assert_any_call("Secret fetched successfully")

    def test_get_secret_client_error(self):
        """Test handling of ClientError when getting secret"""
        # Setup
        secret_name = "test-secret"
        error_message = "Secret not found"
        self.mock_client.get_secret_value.side_effect = ClientError(
            error_response={'Error': {'Message': error_message}},
            operation_name='GetSecretValue'
        )

        # Execute
        result = self.secrets_manager.get_secret(secret_name)

        # Verify
        assert result is None
        self.mock_client.get_secret_value.assert_called_once_with(SecretId=secret_name)
        self.mock_logger.info.assert_called_once_with(f"Getting secret {secret_name}")
        self.mock_logger.error.assert_called_once()

