#!/usr/bin/env python3
"""Unit tests for core.runner module."""

import os
import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.runner import ScraperRunner
from core.storage import Storage


class TestScraperRunner(unittest.TestCase):
    """Test cases for the ScraperRunner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock storage
        self.mock_storage = Mock(spec=Storage)
        self.mock_storage.save_result.return_value = True
        
        # Create runner with mocked storage
        self.runner = ScraperRunner(storage=self.mock_storage, max_workers=2)
    
    def create_mock_scraper(self, scraper_id: str, result: dict, delay: float = 0.1):
        """Create a mock scraper function that returns a specific result."""
        def mock_scraper(config):
            time.sleep(delay)  # Simulate work
            return result
        
        config = {
            'scraper_id': scraper_id,
            'name': f'Test - {scraper_id}'
        }
        
        return mock_scraper, config
    
    def test_runner_initialization(self):
        """Test ScraperRunner initialization."""
        runner = ScraperRunner(max_workers=5)
        
        self.assertEqual(runner.max_workers, 5)
        self.assertIsInstance(runner.storage, Storage)
        self.assertEqual(runner.results, [])
    
    def test_run_scraper_isolated_success(self):
        """Test running a single scraper successfully."""
        def successful_scraper(config):
            return {
                'scraper_id': 'test_success',
                'name': 'Test Success',
                'count': 42,
                'status': 'success'
            }
        
        config = {'scraper_id': 'test_success', 'name': 'Test Success'}
        
        result = self.runner.run_scraper_isolated(successful_scraper, config)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['count'], 42)
        self.assertEqual(result['scraper_id'], 'test_success')
        
        # Check that result was saved
        self.mock_storage.save_result.assert_called_once_with(result)
    
    def test_run_scraper_isolated_failure(self):
        """Test running a scraper that returns an error."""
        def failing_scraper(config):
            return {
                'scraper_id': 'test_fail',
                'name': 'Test Fail',
                'count': None,
                'status': 'error',
                'error': 'Connection timeout'
            }
        
        config = {'scraper_id': 'test_fail', 'name': 'Test Fail'}
        
        result = self.runner.run_scraper_isolated(failing_scraper, config)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'Connection timeout')
        self.assertIsNone(result['count'])
        
        # Check that error result was saved
        self.mock_storage.save_result.assert_called_once_with(result)
    
    def test_run_scraper_isolated_exception(self):
        """Test running a scraper that raises an exception."""
        def crashing_scraper(config):
            raise ValueError("Something went wrong")
        
        config = {'scraper_id': 'test_crash', 'name': 'Test Crash'}
        
        result = self.runner.run_scraper_isolated(crashing_scraper, config)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Critical failure', result['error'])
        self.assertIn('Something went wrong', result['error'])
        self.assertIsNone(result['count'])
        
        # Check that error result was saved
        self.mock_storage.save_result.assert_called_once()
    
    def test_run_scraper_isolated_storage_failure(self):
        """Test scraper isolation when storage fails."""
        self.mock_storage.save_result.return_value = False
        
        def successful_scraper(config):
            return {
                'scraper_id': 'test_storage_fail',
                'name': 'Test Storage Fail',
                'count': 10,
                'status': 'success'
            }
        
        config = {'scraper_id': 'test_storage_fail', 'name': 'Test Storage Fail'}
        
        # Should not raise exception even if storage fails
        result = self.runner.run_scraper_isolated(successful_scraper, config)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['count'], 10)
    
    def test_run_all_scrapers_mixed_results(self):
        """Test running multiple scrapers with mixed success/failure."""
        scrapers = [
            self.create_mock_scraper('success_1', {
                'scraper_id': 'success_1',
                'name': 'Success 1',
                'count': 100,
                'status': 'success'
            }),
            self.create_mock_scraper('success_2', {
                'scraper_id': 'success_2', 
                'name': 'Success 2',
                'count': 200,
                'status': 'success'
            }),
            self.create_mock_scraper('fail_1', {
                'scraper_id': 'fail_1',
                'name': 'Fail 1',
                'count': None,
                'status': 'error',
                'error': 'Network error'
            })
        ]
        
        results = self.runner.run_all_scrapers(scrapers)
        
        self.assertEqual(len(results), 3)
        
        # Check individual results
        success_results = [r for r in results if r['status'] == 'success']
        error_results = [r for r in results if r['status'] == 'error']
        
        self.assertEqual(len(success_results), 2)
        self.assertEqual(len(error_results), 1)
        
        # Check that all results were saved
        self.assertEqual(self.mock_storage.save_result.call_count, 3)
    
    def test_run_all_scrapers_empty_list(self):
        """Test running with empty scraper list."""
        results = self.runner.run_all_scrapers([])
        
        self.assertEqual(results, [])
        self.mock_storage.save_result.assert_not_called()
    
    def test_run_all_scrapers_exception_isolation(self):
        """Test that exceptions in one scraper don't affect others."""
        def crashing_scraper(config):
            raise RuntimeError("Critical system error")
        
        def working_scraper(config):
            return {
                'scraper_id': 'working',
                'name': 'Working Scraper',
                'count': 50,
                'status': 'success'
            }
        
        scrapers = [
            (crashing_scraper, {'scraper_id': 'crash', 'name': 'Crashing'}),
            (working_scraper, {'scraper_id': 'working', 'name': 'Working'})
        ]
        
        results = self.runner.run_all_scrapers(scrapers)
        
        self.assertEqual(len(results), 2)
        
        # Working scraper should succeed despite other scraper crashing
        working_result = next(r for r in results if r['scraper_id'] == 'working')
        self.assertEqual(working_result['status'], 'success')
        self.assertEqual(working_result['count'], 50)
        
        # Crashing scraper should return error result
        crash_result = next(r for r in results if r['scraper_id'] == 'crash')
        self.assertEqual(crash_result['status'], 'error')
        self.assertIn('Critical failure', crash_result['error'])
    
    def test_get_summary_success(self):
        """Test getting summary statistics after successful run."""
        scrapers = [
            self.create_mock_scraper('s1', {
                'scraper_id': 's1', 'name': 'S1', 'count': 100, 'status': 'success'
            }),
            self.create_mock_scraper('s2', {
                'scraper_id': 's2', 'name': 'S2', 'count': 200, 'status': 'success'
            }),
            self.create_mock_scraper('s3', {
                'scraper_id': 's3', 'name': 'S3', 'count': None, 'status': 'error', 'error': 'Failed'
            })
        ]
        
        self.runner.run_all_scrapers(scrapers)
        summary = self.runner.get_summary()
        
        self.assertEqual(summary['total_scrapers'], 3)
        self.assertEqual(summary['successful'], 2)
        self.assertEqual(summary['failed'], 1)
        self.assertEqual(summary['success_rate'], 2/3 * 100)
        self.assertEqual(summary['total_applicants'], 300)
        self.assertEqual(len(summary['errors']), 1)
        self.assertEqual(summary['errors'][0]['scraper_id'], 's3')
    
    def test_get_summary_no_results(self):
        """Test getting summary when no scrapers have been run."""
        summary = self.runner.get_summary()
        
        self.assertIn('error', summary)
        self.assertEqual(summary['error'], 'No results available')
    
    @patch('core.runner.ThreadPoolExecutor')
    def test_concurrent_execution(self, mock_executor):
        """Test that scrapers run concurrently using ThreadPoolExecutor."""
        # Mock the executor and future
        mock_future = Mock(spec=Future)
        mock_future.result.return_value = {
            'scraper_id': 'test',
            'name': 'Test',
            'status': 'success',
            'count': 10
        }
        
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor_instance.submit.return_value = mock_future
        
        # Mock as_completed to return our future
        with patch('core.runner.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [mock_future]
            
            scrapers = [self.create_mock_scraper('test', {
                'scraper_id': 'test', 'name': 'Test', 'status': 'success', 'count': 10
            })]
            
            results = self.runner.run_all_scrapers(scrapers)
        
        # Verify ThreadPoolExecutor was used
        mock_executor.assert_called_once_with(max_workers=2)
        mock_executor_instance.submit.assert_called_once()
    
    def test_performance_timing(self):
        """Test that performance timing works correctly."""
        def slow_scraper(config):
            time.sleep(0.2)  # 200ms delay
            return {
                'scraper_id': 'slow',
                'name': 'Slow Scraper',
                'count': 42,
                'status': 'success'
            }
        
        config = {'scraper_id': 'slow', 'name': 'Slow Scraper'}
        
        start_time = time.time()
        result = self.runner.run_scraper_isolated(slow_scraper, config)
        duration = time.time() - start_time
        
        # Should take at least 200ms
        self.assertGreater(duration, 0.15)
        self.assertEqual(result['status'], 'success')
    
    def test_max_workers_setting(self):
        """Test that max_workers setting is respected."""
        runner = ScraperRunner(max_workers=1)
        self.assertEqual(runner.max_workers, 1)
        
        runner = ScraperRunner(max_workers=20)
        self.assertEqual(runner.max_workers, 20)


def run_runner_tests():
    """Run all runner tests and return results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestScraperRunner)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("Running ScraperRunner tests...")
    success, failures, errors = run_runner_tests()
    
    if success:
        print("✅ All ScraperRunner tests passed!")
    else:
        print(f"❌ ScraperRunner tests failed: {failures} failures, {errors} errors")
        sys.exit(1)