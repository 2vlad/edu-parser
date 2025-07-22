"""HTTP client with timeouts and retry logic for reliable scraping."""

import httpx
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from .logging_config import get_logger, log_performance


logger = get_logger(__name__)


class ReliableHTTPClient:
    """
    HTTP client with built-in timeouts, retries, and error handling.
    
    Ensures all network requests have proper timeouts and reliability.
    """
    
    def __init__(self, 
                 timeout: float = 30.0,
                 connect_timeout: float = 10.0, 
                 read_timeout: float = 30.0,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize reliable HTTP client.
        
        Args:
            timeout: Total request timeout in seconds
            connect_timeout: Connection timeout in seconds
            read_timeout: Read timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.timeout = httpx.Timeout(
            timeout=timeout,
            connect=connect_timeout,
            read=read_timeout
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Create client with timeouts
        self.client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            verify=True  # SSL verification
        )
        
        logger.info(f"ReliableHTTPClient initialized - timeout={timeout}s, retries={max_retries}")
    
    def get(self, url: str, **kwargs) -> httpx.Response:
        """
        Reliable GET request with timeouts and retries.
        
        Args:
            url: URL to fetch
            **kwargs: Additional httpx arguments
            
        Returns:
            httpx.Response object
            
        Raises:
            Exception: If all retries failed
        """
        return self._request_with_retries("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> httpx.Response:
        """Reliable POST request with timeouts and retries."""
        return self._request_with_retries("POST", url, **kwargs)
    
    def _request_with_retries(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Execute HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional httpx arguments
            
        Returns:
            httpx.Response object
            
        Raises:
            Exception: If all retries failed
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(f"Retry {attempt}/{self.max_retries} for {domain} after {delay:.1f}s delay")
                    time.sleep(delay)
                
                logger.debug(f"Requesting {method} {domain} (attempt {attempt + 1})")
                
                response = self.client.request(method, url, **kwargs)
                
                # Log successful request
                duration = time.time() - start_time
                log_performance(f"http_{method.lower()}", duration, f"domain={domain}, status={response.status_code}")
                
                # Check for HTTP errors
                response.raise_for_status()
                
                if attempt > 0:
                    logger.info(f"Request succeeded on retry {attempt} for {domain}")
                
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1} for {domain}: {e}")
                
            except httpx.ConnectError as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1} for {domain}: {e}")
                
            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    logger.error(f"Client error {e.response.status_code} for {domain} - not retrying")
                    raise e
                
                last_exception = e
                logger.warning(f"HTTP error {e.response.status_code} on attempt {attempt + 1} for {domain}")
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected error on attempt {attempt + 1} for {domain}: {e}")
        
        # All retries failed
        duration = time.time() - start_time
        logger.error(f"All {self.max_retries + 1} attempts failed for {domain} after {duration:.1f}s")
        log_performance(f"http_{method.lower()}_failed", duration, f"domain={domain}")
        
        raise last_exception or Exception(f"All {self.max_retries + 1} attempts failed for {url}")
    
    def download_excel(self, url: str, **kwargs) -> bytes:
        """
        Download Excel file with reliability.
        
        Args:
            url: URL to Excel file
            **kwargs: Additional httpx arguments
            
        Returns:
            Excel file content as bytes
        """
        logger.info(f"Downloading Excel file from {urlparse(url).netloc}")
        
        response = self.get(url, **kwargs)
        
        # Verify content type
        content_type = response.headers.get('content-type', '').lower()
        expected_types = [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/octet-stream'
        ]
        
        if not any(expected in content_type for expected in expected_types):
            logger.warning(f"Unexpected content type for Excel file: {content_type}")
        
        content_length = len(response.content)
        logger.info(f"Downloaded Excel file: {content_length} bytes")
        
        return response.content
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
        logger.debug("HTTP client closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Default client instance for convenience
default_client = ReliableHTTPClient()


# Convenience functions
def get_with_timeout(url: str, timeout: float = 30.0, **kwargs) -> httpx.Response:
    """Convenience function for GET with timeout."""
    with ReliableHTTPClient(timeout=timeout) as client:
        return client.get(url, **kwargs)


def download_excel_safe(url: str, timeout: float = 60.0) -> bytes:
    """Convenience function for downloading Excel files safely."""
    with ReliableHTTPClient(timeout=timeout, max_retries=2) as client:
        return client.download_excel(url)