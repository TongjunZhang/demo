# tasks/https_io.py

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import logging
import time
from urllib3.util.ssl_ import DEFAULT_CIPHERS
# Check if DEFAULT_CIPHERS exists, if not, define it
if not hasattr(urllib3.util.ssl_, "DEFAULT_CIPHERS"):
    urllib3.util.ssl_.DEFAULT_CIPHERS = "ECDHE+AESGCM:!ECDSA"  # Example cipher string
    
class HttpsIo:
    """
    Class to handle HTTP requests with retry logic and logging.
    """
    def __init__(
        self,
        retry_times: int = 10,
        logger: logging.Logger = None
    ) -> None:
        """
        Initialize HttpsIo with retry settings and logger.

        Args:
            retry_times (int, optional): Number of times to retry the API request. Defaults to 10.
            logger (logging.Logger, optional): Logger object. Defaults to None.
        """
        self.http_session: requests.Session = None
        self.retry_times = retry_times
        self.logger = logging.getLogger() if logger is None else logger

    def initiate_request(self) -> None:
        """
        Initiates the HTTP session and sets up the retry strategy.

        - Sets backoff factor to 1.
        - Retries on status codes: 409, 408, 429, 500, 502, 503, 504, 104.
        - Sets max retries to retry_times.
        - Adds a hook to raise exceptions for failed responses.
        """
        retry_strategy = Retry(
            total=self.retry_times,
            read=self.retry_times,
            connect=self.retry_times,
            backoff_factor=1,
            status_forcelist=[409, 408, 429, 500, 502, 503, 504, 104]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http_session = requests.Session()
        self.http_session.mount("https://", adapter)
        # Hook to raise exceptions for failed responses
        assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
        self.http_session.hooks["response"] = [assert_status_hook]

    def http_request(
        self,
        http_url: str,
        http_head: dict = {},
        http_data: dict = {},
        http_method: str = "GET"
    ) -> requests.Response:
        """
        Makes an HTTP request using the session.

        Args:
            http_url (str): Request URL.
            http_head (dict, optional): Headers for the API call. Defaults to {}.
            http_data (dict, optional): Request body for the API call. Defaults to {}.
            http_method (str, optional): HTTP method. Defaults to "GET".

        Returns:
            tuple: (success (bool), response (requests.Response))
        """
        start_time = time.time()
        if self.http_session is None:
            self.initiate_request()
        response = self.http_session.request(http_method, http_url, headers=http_head, data=http_data)
        end_time = time.time()
        self.logger.info(
            f'Response time for API call: status: {response.status_code}, time: {end_time-start_time:.2f} seconds'
        )
        try:
            response.raise_for_status()
            return True, response
        except requests.HTTPError:
            self.logger.error(
                f"HTTP request failed for {http_url}: {response.status_code}: {getattr(response, 'text', '')}"
            )
            return False, response
