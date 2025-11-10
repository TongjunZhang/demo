import unittest
from unittest.mock import patch, MagicMock
from tasks.osc_account_io import HttpsIo


class TestHttpsIo(unittest.TestCase):
    @patch('tasks.https_io.requests.Session')
    @patch('tasks.https_io.logging.getLogger')
    def test_initiate_request(self, mock_get_logger, mock_requests_session):
        # Mock the logger
        mock_logger = mock_get_logger.return_value
        
        # Create an instance of HttpsIo with the mocked logger
        https_io_instance = HttpsIo(logger=mock_logger)
        
        # Set up the mock session instance
        mock_session_instance = mock_requests_session.return_value
        mock_session_instance.hooks = {"response": []}
        
        # Call the initiate_request method
        https_io_instance.initiate_request()
        
        # Verify that a new session was created
        mock_requests_session.assert_called_once()
        
        # Verify that the session was configured correctly
        mock_session_instance.mount.assert_called_once_with("https://", unittest.mock.ANY)
        self.assertIn("response", mock_session_instance.hooks)
        self.assertTrue(callable(mock_session_instance.hooks["response"][0]))
        

    @patch('tasks.https_io.requests.Session')
    @patch('tasks.https_io.logging.getLogger')
    def test_http_request(self, mock_get_logger, mock_requests_session):
        # Mock the logger
        mock_logger = mock_get_logger.return_value
        
        # Create an instance of HttpsIo with the mocked logger
        https_io_instance = HttpsIo(logger=mock_logger)
        
        # Set up the mock session instance
        mock_session_instance = mock_requests_session.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_session_instance.request.return_value = mock_response
        
        # Call the initiate_request method to set up the session
        https_io_instance.initiate_request()
        
        # Call the http_request method
        success, result = https_io_instance.http_request(
            http_url="https://example.com",
            http_head={"Content-Type": "application/json"},
            http_data={"key": "value"},
            http_method="POST"
        )
        
        # Assert the result
        self.assertTrue(success)
        self.assertEqual(result.status_code, 200)
        
        # Verify that the request method was called with the correct arguments
        mock_session_instance.request.assert_called_once_with(
            "POST",
            "https://example.com",
            headers={"Content-Type": "application/json"},
            data={"key": "value"}
        )
        

if __name__ == "__main__":
    unittest.main()