#!/usr/bin/env python3
"""Unit tests for core.http_client module."""

import os
import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
import httpx

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.http_client import ReliableHTTPClient, get_with_timeout, download_excel_safe


class TestReliableHTTPClient(unittest.TestCase):
    """Test cases for the ReliableHTTPClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = ReliableHTTPClient(timeout=5.0, max_retries=2, retry_delay=0.1)
    
    def tearDown(self):
        """Clean up after tests."""
        self.client.close()
    
    def test_client_initialization(self):
        """Test ReliableHTTPClient initialization."""
        client = ReliableHTTPClient(
            timeout=10.0,
            connect_timeout=3.0,
            read_timeout=7.0,
            max_retries=5,
            retry_delay=2.0
        )
        
        # Check timeout object has correct values (httpx.Timeout doesn't have .timeout attribute)
        self.assertIsInstance(client.timeout, httpx.Timeout)
        self.assertEqual(client.timeout.connect, 3.0)
        self.assertEqual(client.timeout.read, 7.0)
        self.assertEqual(client.max_retries, 5)
        self.assertEqual(client.retry_delay, 2.0)
        
        client.close()
    
    def test_default_initialization(self):
        """Test default ReliableHTTPClient initialization."""
        client = ReliableHTTPClient()
        
        # Check timeout object has correct default values
        self.assertIsInstance(client.timeout, httpx.Timeout)
        self.assertEqual(client.timeout.connect, 10.0)
        self.assertEqual(client.timeout.read, 30.0)
        self.assertEqual(client.max_retries, 3)
        self.assertEqual(client.retry_delay, 1.0)
        
        client.close()
    
    @patch('core.http_client.httpx.Client')
    def test_successful_get_request(self, mock_client_class):
        """Test successful GET request."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        # Mock the client instance
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        # Create client and make request
        with ReliableHTTPClient(timeout=5.0) as client:
            response = client.get("https://example.com")
        
        self.assertEqual(response, mock_response)
        mock_client_instance.request.assert_called_once_with("GET", "https://example.com")
    
    @patch('core.http_client.httpx.Client')
    def test_timeout_with_retries(self, mock_client_class):
        """Test timeout handling with retry logic."""
        # Mock client to raise TimeoutException on first calls, then succeed
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance.request.side_effect = [
            httpx.TimeoutException("Timeout 1"),
            httpx.TimeoutException("Timeout 2"),
            mock_response  # Success on third attempt
        ]
        mock_client_class.return_value = mock_client_instance
        
        with ReliableHTTPClient(timeout=1.0, max_retries=2, retry_delay=0.01) as client:
            response = client.get("https://slow-example.com")
        
        self.assertEqual(response, mock_response)
        self.assertEqual(mock_client_instance.request.call_count, 3)
    
    @patch('core.http_client.httpx.Client')
    def test_all_retries_fail(self, mock_client_class):
        """Test when all retry attempts fail."""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = httpx.TimeoutException("Always timeout")
        mock_client_class.return_value = mock_client_instance
        
        with self.assertRaises(httpx.TimeoutException):
            with ReliableHTTPClient(timeout=1.0, max_retries=1, retry_delay=0.01) as client:
                client.get("https://always-timeout.com")
        
        # Should try initial + retries
        self.assertEqual(mock_client_instance.request.call_count, 2)
    
    @patch('core.http_client.httpx.Client')
    def test_http_status_error_no_retry_4xx(self, mock_client_class):
        """Test that 4xx errors don't trigger retries."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)
        
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = mock_error
        mock_client_class.return_value = mock_client_instance
        
        with self.assertRaises(httpx.HTTPStatusError):
            with ReliableHTTPClient(max_retries=3) as client:
                client.get("https://example.com/notfound")
        
        # Should only try once for 4xx errors
        mock_client_instance.request.assert_called_once()
    
    @patch('core.http_client.httpx.Client')
    def test_http_status_error_retry_5xx(self, mock_client_class):
        """Test that 5xx errors trigger retries."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_error = httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)
        
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = mock_error
        mock_client_class.return_value = mock_client_instance
        
        with self.assertRaises(httpx.HTTPStatusError):
            with ReliableHTTPClient(max_retries=2, retry_delay=0.01) as client:
                client.get("https://example.com/server-error")
        
        # Should retry for 5xx errors
        self.assertEqual(mock_client_instance.request.call_count, 3)  # initial + 2 retries
    
    @patch('core.http_client.httpx.Client')
    def test_connection_error_retries(self, mock_client_class):
        """Test that connection errors trigger retries."""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = httpx.ConnectError("Connection failed")
        mock_client_class.return_value = mock_client_instance
        
        with self.assertRaises(httpx.ConnectError):
            with ReliableHTTPClient(max_retries=1, retry_delay=0.01) as client:
                client.get("https://unreachable.com")
        
        self.assertEqual(mock_client_instance.request.call_count, 2)
    
    @patch('core.http_client.httpx.Client')
    def test_post_method(self, mock_client_class):
        """Test POST method works correctly."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        with ReliableHTTPClient() as client:
            response = client.post("https://example.com/api", json={"test": "data"})
        
        self.assertEqual(response, mock_response)
        mock_client_instance.request.assert_called_once_with(
            "POST", "https://example.com/api", json={"test": "data"}
        )
    
    @patch('core.http_client.httpx.Client')
    def test_download_excel_success(self, mock_client_class):
        """Test successful Excel file download."""
        mock_content = b"fake excel content"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/vnd.ms-excel"}
        mock_response.content = mock_content
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        with ReliableHTTPClient() as client:
            content = client.download_excel("https://example.com/data.xls")
        
        self.assertEqual(content, mock_content)
    
    @patch('core.http_client.httpx.Client')
    def test_download_excel_wrong_content_type(self, mock_client_class):
        """Test Excel download with unexpected content type (should warn but work)."""
        mock_content = b"fake excel content"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}  # Wrong type
        mock_response.content = mock_content
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        with ReliableHTTPClient() as client:
            content = client.download_excel("https://example.com/weird.xls")
        
        # Should still return content despite wrong content type
        self.assertEqual(content, mock_content)
    
    def test_context_manager(self):
        """Test that client works as context manager."""
        with ReliableHTTPClient() as client:
            self.assertIsInstance(client, ReliableHTTPClient)
        
        # Client should be closed after context
        # (We can't easily test this without mocking, but the syntax works)
    
    @patch('core.http_client.ReliableHTTPClient')
    def test_convenience_get_with_timeout(self, mock_client_class):
        """Test convenience function get_with_timeout."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        
        result = get_with_timeout("https://example.com", timeout=15.0)
        
        self.assertEqual(result, mock_response)
        mock_client_class.assert_called_once_with(timeout=15.0)
        mock_client_instance.get.assert_called_once_with("https://example.com")
    
    @patch('core.http_client.ReliableHTTPClient')
    def test_convenience_download_excel_safe(self, mock_client_class):
        """Test convenience function download_excel_safe."""
        mock_client_instance = Mock()
        mock_content = b"excel content"
        mock_client_instance.download_excel.return_value = mock_content
        mock_client_class.return_value.__enter__.return_value = mock_client_instance
        
        result = download_excel_safe("https://example.com/data.xlsx")
        
        self.assertEqual(result, mock_content)
        mock_client_class.assert_called_once_with(timeout=60.0, max_retries=2)
        mock_client_instance.download_excel.assert_called_once_with("https://example.com/data.xlsx")
    
    @patch('time.sleep')
    @patch('core.http_client.httpx.Client')
    def test_exponential_backoff(self, mock_client_class, mock_sleep):
        """Test exponential backoff delay between retries."""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = [
            httpx.TimeoutException("Timeout 1"),
            httpx.TimeoutException("Timeout 2"),
            httpx.TimeoutException("Timeout 3")
        ]
        mock_client_class.return_value = mock_client_instance
        
        with self.assertRaises(httpx.TimeoutException):
            with ReliableHTTPClient(max_retries=2, retry_delay=1.0) as client:
                client.get("https://example.com")
        
        # Check exponential backoff: 1.0, 2.0
        expected_calls = [unittest.mock.call(1.0), unittest.mock.call(2.0)]
        mock_sleep.assert_has_calls(expected_calls)
    
    def test_real_timeout_behavior(self):
        """Test that timeout configuration actually works (integration test)."""
        # Skip this integration test since it depends on external network
        self.skipTest("Integration test requires external network - skipping in unit tests")


def run_http_client_tests():
    """Run all HTTP client tests and return results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReliableHTTPClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("Running ReliableHTTPClient tests...")
    success, failures, errors = run_http_client_tests()
    
    if success:
        print("✅ All ReliableHTTPClient tests passed!")
    else:
        print(f"❌ ReliableHTTPClient tests failed: {failures} failures, {errors} errors")
        sys.exit(1)