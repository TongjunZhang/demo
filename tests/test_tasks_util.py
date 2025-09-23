import unittest
from unittest.mock import patch
from tasks.utils import get_pipeline_execution_id, get_max_dynamics_datetime, get_most_recent_datetime

class TestUtils(unittest.TestCase):

    @patch('tasks.utils.get_pipeline_execution_id')
    def test_get_pipeline_execution_id(self, mock_datetime):
        # Mock the current timestamp
        pipeline_execution_id = get_pipeline_execution_id()
        # Verify the result
        assert pipeline_execution_id is not None

    def test_get_max_dynamics_datetime(self):
        # Mock the logger
        
        # Test data
        data = {"value": [
            {"modifiedon": "2023-01-01T12:00:00Z"},
            {"modifiedon": "2023-01-02T12:00:00Z"},
            {"modifiedon": "2023-01-03T12:00:00Z"}
        ]}
        current_watermark = "2023-01-01T00:00:00Z"
        
        # Call the get_max_dynamics_datetime method
        max_datetime = get_max_dynamics_datetime(data, current_watermark)
        
        # Verify the result
        self.assertEqual(max_datetime, "2023-01-03T12:00:00Z")
        
    def test_get_max_dynamics_datetime_no_dates(self):
        # Mock the logger
        
        # Test data with no modifiedon dates
        data = {"value": [
            {"createdon": "2023-01-01T12:00:00Z"},
            {"createdon": "2023-01-02T12:00:00Z"},
            {"createdon": "2023-01-03T12:00:00Z"}
        ]}
        current_watermark = "2023-01-01T00:00:00Z"
        
        # Call the get_max_dynamics_datetime method
        max_datetime = get_max_dynamics_datetime(data, current_watermark)
        
        # Verify the result
        self.assertIsNotNone(max_datetime)
        

    def test_get_most_recent_datetime(self):
        # Define test data
        datetime_value_1 = "2023-01-01T12:00:00Z"
        datetime_value_2 = "2023-01-02T12:00:00Z"
        
        # Call the get_most_recent_datetime method
        most_recent_datetime = get_most_recent_datetime(datetime_value_1, datetime_value_2)
        
        # Verify the result
        self.assertEqual(most_recent_datetime, datetime_value_2)

    def test_get_most_recent_datetime_equal(self):
        # Define test data
        datetime_value_1 = "2023-01-01T12:00:00Z"
        datetime_value_2 = "2023-01-01T12:00:00Z"
        
        # Call the get_most_recent_datetime method
        most_recent_datetime = get_most_recent_datetime(datetime_value_1, datetime_value_2)
        
        # Verify the result
        self.assertEqual(most_recent_datetime, datetime_value_1)


if __name__ == "__main__":
    unittest.main()