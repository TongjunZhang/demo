import boto3
import logging
import argparse
from tasks.aws_api_io import MarketoETL, SecretsManagerIO
import unittest
# from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import json
# from tasks.snowflake_io import snowflake_io
from unittest.mock import patch, MagicMock


class TestMarketoETL(unittest.TestCase):
    def setUp(self):
        # Setup mock arguments
        self.args = argparse.Namespace()
        self.args.region_name = 'us-east-2'
        
        # Setup mock session
        self.mock_session = MagicMock(spec=boto3.Session)
        self.mock_resource = MagicMock()
        self.mock_table = MagicMock()
        self.mock_payload = MagicMock()
        self.mock_session.resource.return_value = self.mock_resource
        self.mock_resource.Table.return_value = self.mock_table
        self.mock_logger = MagicMock()
        # Create MarketoETL instance with mocked session
        self.MarketoETL_io = MarketoETL(args=self.args, boto3_session=self.mock_session)
        # self.secret_data = SecretsManagerIO.get_secret(self.args.secret_name)

    # @patch('tasks.snowflake_io.transfer_entity_data')
    #@patch('tasks.aws_api_io.SecretsManagerIO.get_secret')
    def test_put_item(self):
        """Test putting an item into DynamoDB table"""
        # Setup test data
        # table_name = "test_table"
        test_item = ["1327712089","www.axeelite.com", "9c871e84-3b65-ea11-a815-000d3a591fb8","cb6a9a3f-c65c-ea11-a811-000d3a579c41","Axe Elite","301 Market St","Canonsburg","15317"]

        # Test
        # result = self.MarketoETL_io.put_item(mock_transfer_entity_data)

        payload = json.dumps({
            "ownerid@odata.bind": "/systemusers(93b90868-8652-ea11-a81a-000d3a579b7d)",
            "name": test_item[4],
            "cci_businesssector": "123",
            "address1_city": test_item[6],
            "address1_line1": test_item[5],
            "address1_postalcode": test_item[7],
            "address1_stateorprovince": test_item[3],
            "statecode": 0,
            "telephone1": "1231231232",
            "websiteurl": test_item[1],
            "address1_composite": "123 Canonsburg 15317"
        })
        # Verify table was set with correct name
        # self.mock_resource.Table.assert_called_once_with(table_name)
        self.MarketoETL_io.logger = self.mock_logger

        result=self.MarketoETL_io.put_item(test_item)

        # Verify put_item was called with correct item
        # Verify
        self.assertEqual(result, payload)

    def test_put_item_logs_info(self):
        """Test that put_item logs the operation"""
        # Setup test data
        table_name = "test_table"
        test_item = ["1327712089","www.axeelite.com", "9c871e84-3b65-ea11-a815-000d3a591fb8","cb6a9a3f-c65c-ea11-a811-000d3a579c41","Axe Elite","301 Market St","Canonsburg","15317"]

    
        # Replace the logger with our mock
        self.MarketoETL_io.logger = self.mock_logger
    
        # Call the method
        self.MarketoETL_io.put_item(test_item)
    
        # Verify logging calls
        # self.mock_logger.info.assert_any_call(f"Setting dynamodb table {table_name}")
        self.mock_logger.info.assert_any_call(
            'put item from Snowflake: %s' % (test_item[0])
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

    # def test_get_secret_client_error(self):
    #       """Test handling of ClientError when getting secret"""
    #       # Setup
    #       secret_name = "test-secret"
    #       error_message = "Secret not found"
    #       self.mock_client.get_secret_value.side_effect = ClientError(
    #           error_response={'Error': {'Message': error_message}},
    #           operation_name='GetSecretValue'
    #       )

    #       # Execute
    #       result = self.secrets_manager.get_secret(secret_name)

    #       # Verify
    #       assert result is None
    #       self.mock_client.get_secret_value.assert_called_once_with(SecretId=secret_name)
    #       self.mock_logger.info.assert_called_once_with(f"Getting secret {secret_name}")
    #       self.mock_logger.error.assert_called_once()

if __name__ == "__main__":
    unittest.main()