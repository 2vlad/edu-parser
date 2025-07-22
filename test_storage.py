#!/usr/bin/env python3
"""Unit tests for core.storage module."""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import date

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage, StorageError


class TestStorage(unittest.TestCase):
    """Test cases for the Storage class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key-123'
        })
        self.env_patcher.start()
        
        # Mock the create_client function
        self.supabase_patcher = patch('core.storage.create_client')
        self.mock_create_client = self.supabase_patcher.start()
        
        # Mock the client instance
        self.mock_client = Mock()
        self.mock_create_client.return_value = self.mock_client
        
        # Mock successful connection test
        self.mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        self.supabase_patcher.stop()
    
    def test_init_success(self):
        """Test successful Storage initialization."""
        storage = Storage()
        
        self.mock_create_client.assert_called_once_with(
            'https://test.supabase.co', 
            'test-key-123'
        )
        self.assertEqual(storage.client, self.mock_client)
    
    def test_init_missing_url(self):
        """Test StorageError when SUPABASE_URL is missing."""
        with patch.dict(os.environ, {'SUPABASE_KEY': 'test-key'}, clear=True):
            with self.assertRaises(StorageError) as context:
                Storage()
            self.assertIn('SUPABASE_URL', str(context.exception))
    
    def test_init_missing_key(self):
        """Test StorageError when SUPABASE_KEY is missing."""
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co'}, clear=True):
            with self.assertRaises(StorageError) as context:
                Storage()
            self.assertIn('SUPABASE_KEY', str(context.exception))
    
    def test_init_connection_failure(self):
        """Test StorageError when connection test fails."""
        self.mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Connection failed")
        
        with self.assertRaises(StorageError) as context:
            Storage()
        self.assertIn('Database connection test failed', str(context.exception))
    
    def test_save_result_success(self):
        """Test successful result saving."""
        storage = Storage()
        
        # Mock successful insert
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        result = {
            'scraper_id': 'test_scraper',
            'name': 'Test University - Test Program',
            'count': 42,
            'status': 'success'
        }
        
        success = storage.save_result(result)
        
        self.assertTrue(success)
        self.mock_client.table.assert_called_with('applicant_counts')
        
        # Check that insert was called with correct data
        insert_call = self.mock_client.table.return_value.insert.call_args[0][0]
        self.assertEqual(insert_call['scraper_id'], 'test_scraper')
        self.assertEqual(insert_call['count'], 42)
        self.assertEqual(insert_call['status'], 'success')
        self.assertEqual(insert_call['date'], date.today().isoformat())
    
    def test_save_result_missing_required_field(self):
        """Test save_result with missing required field."""
        storage = Storage()
        
        result = {
            'name': 'Test University - Test Program',
            'count': 42,
            'status': 'success'
            # Missing scraper_id
        }
        
        success = storage.save_result(result)
        self.assertFalse(success)
    
    def test_save_result_invalid_status(self):
        """Test save_result with invalid status."""
        storage = Storage()
        
        result = {
            'scraper_id': 'test_scraper',
            'name': 'Test University - Test Program',
            'count': 42,
            'status': 'invalid_status'
        }
        
        success = storage.save_result(result)
        self.assertFalse(success)
    
    def test_save_result_database_error(self):
        """Test save_result with database error."""
        storage = Storage()
        
        # Mock database error
        self.mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")
        
        result = {
            'scraper_id': 'test_scraper',
            'name': 'Test University - Test Program',
            'status': 'success'
        }
        
        success = storage.save_result(result)
        self.assertFalse(success)
    
    def test_get_enabled_scrapers_success(self):
        """Test successful retrieval of enabled scrapers."""
        storage = Storage()
        
        # Mock successful query
        mock_data = [
            {'scraper_id': 'test1', 'name': 'Test 1', 'enabled': True},
            {'scraper_id': 'test2', 'name': 'Test 2', 'enabled': True}
        ]
        mock_response = Mock(data=mock_data)
        self.mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response
        
        scrapers = storage.get_enabled_scrapers()
        
        self.assertEqual(scrapers, mock_data)
        self.mock_client.table.assert_called_with('scrapers_config')
        
        # Check query chain
        table_mock = self.mock_client.table.return_value
        table_mock.select.assert_called_with('*')
        table_mock.select.return_value.eq.assert_called_with('enabled', True)
    
    def test_get_enabled_scrapers_database_error(self):
        """Test get_enabled_scrapers with database error."""
        storage = Storage()
        
        # Mock database error
        self.mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.side_effect = Exception("DB Error")
        
        scrapers = storage.get_enabled_scrapers()
        self.assertEqual(scrapers, [])
    
    def test_get_today_results_success(self):
        """Test successful retrieval of today's results."""
        storage = Storage()
        
        # Mock successful query
        mock_data = [
            {'scraper_id': 'test1', 'count': 10, 'status': 'success'},
            {'scraper_id': 'test2', 'count': 20, 'status': 'success'}
        ]
        mock_response = Mock(data=mock_data)
        self.mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response
        
        results = storage.get_today_results()
        
        self.assertEqual(results, mock_data)
        self.mock_client.table.assert_called_with('applicant_counts')
        
        # Check query parameters
        table_mock = self.mock_client.table.return_value
        table_mock.select.return_value.eq.assert_called_with('date', date.today().isoformat())
    
    def test_batch_save_results_success(self):
        """Test successful batch save of results."""
        storage = Storage()
        
        # Mock successful batch insert
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        results = [
            {'scraper_id': 'test1', 'name': 'Test 1', 'status': 'success', 'count': 10},
            {'scraper_id': 'test2', 'name': 'Test 2', 'status': 'success', 'count': 20}
        ]
        
        saved_count = storage.batch_save_results(results)
        
        self.assertEqual(saved_count, 2)
        self.mock_client.table.assert_called_with('applicant_counts')
        
        # Check that batch insert was called
        insert_call = self.mock_client.table.return_value.insert.call_args[0][0]
        self.assertEqual(len(insert_call), 2)
    
    def test_batch_save_results_empty_list(self):
        """Test batch_save_results with empty list."""
        storage = Storage()
        
        saved_count = storage.batch_save_results([])
        self.assertEqual(saved_count, 0)
    
    def test_batch_save_results_invalid_data(self):
        """Test batch_save_results with invalid data."""
        storage = Storage()
        
        results = [
            {'scraper_id': 'test1', 'name': 'Test 1', 'status': 'success'},
            {'name': 'Test 2', 'status': 'success'},  # Missing scraper_id
            {'scraper_id': 'test3', 'name': 'Test 3', 'status': 'invalid'}  # Invalid status
        ]
        
        # Mock successful insert for valid data
        mock_response = Mock()
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        saved_count = storage.batch_save_results(results)
        
        # Only 1 valid result should be processed
        self.assertEqual(saved_count, 1)
    
    def test_get_scraper_by_id_success(self):
        """Test successful retrieval of scraper by ID."""
        storage = Storage()
        
        # Mock successful query
        mock_data = [{'scraper_id': 'test1', 'name': 'Test 1', 'enabled': True}]
        mock_response = Mock(data=mock_data)
        self.mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
        
        scraper = storage.get_scraper_by_id('test1')
        
        self.assertEqual(scraper, mock_data[0])
        
        # Check query parameters
        table_mock = self.mock_client.table.return_value
        table_mock.select.return_value.eq.assert_called_with('scraper_id', 'test1')
    
    def test_get_scraper_by_id_not_found(self):
        """Test get_scraper_by_id when scraper doesn't exist."""
        storage = Storage()
        
        # Mock empty response
        mock_response = Mock(data=[])
        self.mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
        
        scraper = storage.get_scraper_by_id('nonexistent')
        self.assertIsNone(scraper)
    
    def test_mark_synced_to_sheets_success(self):
        """Test successful marking of results as synced to sheets."""
        storage = Storage()
        
        # Mock successful update
        mock_response = Mock()
        self.mock_client.table.return_value.update.return_value.in_.return_value.execute.return_value = mock_response
        
        result_ids = ['id1', 'id2', 'id3']
        updated_count = storage.mark_synced_to_sheets(result_ids)
        
        self.assertEqual(updated_count, 3)
        
        # Check update parameters
        table_mock = self.mock_client.table.return_value
        table_mock.update.assert_called_with({'synced_to_sheets': True})
        table_mock.update.return_value.in_.assert_called_with('id', result_ids)
    
    def test_mark_synced_to_sheets_empty_list(self):
        """Test mark_synced_to_sheets with empty list."""
        storage = Storage()
        
        updated_count = storage.mark_synced_to_sheets([])
        self.assertEqual(updated_count, 0)


def run_storage_tests():
    """Run all storage tests and return results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStorage)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("Running Storage module tests...")
    success, failures, errors = run_storage_tests()
    
    if success:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed: {failures} failures, {errors} errors")
        sys.exit(1)