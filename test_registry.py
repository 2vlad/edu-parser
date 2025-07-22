#!/usr/bin/env python3
"""Unit tests for core.registry module."""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.registry import ScraperRegistry, get_all_scrapers, get_ready_scrapers
from core.storage import Storage


class TestScraperRegistry(unittest.TestCase):
    """Test cases for the ScraperRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock storage to avoid database calls
        self.mock_storage = Mock(spec=Storage)
        self.mock_storage.get_enabled_scrapers.return_value = [
            {'scraper_id': 'test_scraper_1', 'name': 'Test Scraper 1', 'enabled': True},
            {'scraper_id': 'test_scraper_2', 'name': 'Test Scraper 2', 'enabled': True}
        ]
        
        # Create registry with mocked storage
        self.registry = ScraperRegistry(storage=self.mock_storage)
    
    def test_registry_initialization(self):
        """Test that registry initializes correctly."""
        self.assertIsInstance(self.registry.storage, Storage)
        self.assertEqual(self.registry.scrapers, {})
    
    def test_discover_scrapers_success(self):
        """Test successful scraper discovery with real scrapers."""
        # Test with the actual scrapers package
        discovered = self.registry.discover_scrapers('scrapers')
        
        # Should discover scrapers from hse, mephi, and mipt modules
        self.assertGreater(discovered, 0)
        self.assertGreater(len(self.registry.scrapers), 0)
        
        # Check that some expected scrapers are found
        scraper_ids = list(self.registry.scrapers.keys())
        
        # Should have scrapers from all three modules
        has_hse = any('hse_' in sid for sid in scraper_ids)
        has_mephi = any('mephi_' in sid for sid in scraper_ids)
        has_mipt = any('mipt_' in sid for sid in scraper_ids)
        
        self.assertTrue(has_hse, "Should have HSE scrapers")
        self.assertTrue(has_mephi, "Should have MEPhI scrapers")
        self.assertTrue(has_mipt, "Should have MIPT scrapers")
    
    @patch('core.registry.pkgutil.iter_modules')
    @patch('core.registry.importlib.import_module')
    def test_discover_scrapers_no_get_scrapers(self, mock_import_module, mock_iter_modules):
        """Test discovery when module has no get_scrapers function."""
        # Mock the package import first
        mock_package = Mock()
        mock_package.__path__ = ['/fake/path']
        
        # Mock module structure
        mock_iter_modules.return_value = [
            (None, 'test_module', False)
        ]
        
        # Mock module without get_scrapers function
        mock_module = Mock(spec=[])  # Empty spec means no attributes
        
        # Configure the import_module mock to return package first, then module
        mock_import_module.side_effect = [mock_package, mock_module]
        
        discovered = self.registry.discover_scrapers('test_package')
        
        self.assertEqual(discovered, 0)
        self.assertEqual(len(self.registry.scrapers), 0)
    
    def test_load_enabled_scrapers_with_matches(self):
        """Test loading enabled scrapers when matches exist."""
        # Add some test scrapers to registry
        self.registry.scrapers = {
            'test_scraper_1': {
                'function': lambda config: {'status': 'success'},
                'module': 'test',
                'config': {'scraper_id': 'test_scraper_1', 'name': 'Original Name 1'}
            },
            'test_scraper_2': {
                'function': lambda config: {'status': 'success'},
                'module': 'test',
                'config': {'scraper_id': 'test_scraper_2', 'name': 'Original Name 2'}
            }
        }
        
        ready_scrapers = self.registry.load_enabled_scrapers()
        
        self.assertEqual(len(ready_scrapers), 2)
        
        # Check that database config takes precedence
        func1, config1 = ready_scrapers[0]
        self.assertEqual(config1['name'], 'Test Scraper 1')  # From database
        self.assertEqual(config1['scraper_id'], 'test_scraper_1')
        self.assertTrue(callable(func1))
    
    def test_load_enabled_scrapers_no_matches(self):
        """Test loading enabled scrapers when no matches exist."""
        # Registry has no scrapers
        self.registry.scrapers = {}
        
        ready_scrapers = self.registry.load_enabled_scrapers()
        
        self.assertEqual(len(ready_scrapers), 0)
    
    def test_get_all_discovered_scrapers(self):
        """Test getting all discovered scrapers."""
        # Add test scrapers to registry
        self.registry.scrapers = {
            'test_1': {
                'function': lambda config: {'status': 'success'},
                'config': {'scraper_id': 'test_1', 'name': 'Test 1'}
            },
            'test_2': {
                'function': lambda config: {'status': 'success'},
                'config': {'scraper_id': 'test_2', 'name': 'Test 2'}
            }
        }
        
        all_scrapers = self.registry.get_all_discovered_scrapers()
        
        self.assertEqual(len(all_scrapers), 2)
        
        # Check that both scrapers are returned
        scraper_ids = [config['scraper_id'] for func, config in all_scrapers]
        self.assertIn('test_1', scraper_ids)
        self.assertIn('test_2', scraper_ids)
    
    def test_get_scraper_info(self):
        """Test getting scraper information summary."""
        # Add test scrapers
        self.registry.scrapers = {
            'test_scraper_1': {'function': lambda: None, 'config': {}},
            'unmatched_scraper': {'function': lambda: None, 'config': {}}
        }
        
        info = self.registry.get_scraper_info()
        
        self.assertEqual(info['total_discovered'], 2)
        self.assertEqual(info['total_enabled'], 2)  # From mock
        self.assertEqual(info['matched'], 1)  # Only test_scraper_1 matches
        self.assertIn('unmatched_scraper', info['unmatched_functions'])


class TestRegistryConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    @patch('core.registry.ScraperRegistry')
    def test_get_all_scrapers(self, mock_registry_class):
        """Test get_all_scrapers convenience function."""
        # Mock registry instance
        mock_registry = Mock()
        mock_registry.discover_scrapers.return_value = 3
        mock_registry.get_all_discovered_scrapers.return_value = [
            (lambda: None, {'scraper_id': 'test1'}),
            (lambda: None, {'scraper_id': 'test2'}),
            (lambda: None, {'scraper_id': 'test3'})
        ]
        mock_registry_class.return_value = mock_registry
        
        result = get_all_scrapers()
        
        mock_registry.discover_scrapers.assert_called_once()
        mock_registry.get_all_discovered_scrapers.assert_called_once()
        self.assertEqual(len(result), 3)
    
    @patch('core.registry.ScraperRegistry')
    def test_get_ready_scrapers(self, mock_registry_class):
        """Test get_ready_scrapers convenience function."""
        # Mock registry instance
        mock_registry = Mock()
        mock_registry.discover_scrapers.return_value = 2
        mock_registry.load_enabled_scrapers.return_value = [
            (lambda: None, {'scraper_id': 'enabled1'}),
            (lambda: None, {'scraper_id': 'enabled2'})
        ]
        mock_registry_class.return_value = mock_registry
        
        result = get_ready_scrapers()
        
        mock_registry.discover_scrapers.assert_called_once()
        mock_registry.load_enabled_scrapers.assert_called_once()
        self.assertEqual(len(result), 2)


def run_registry_tests():
    """Run all registry tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestScraperRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestRegistryConvenienceFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("Running Registry tests...")
    success, failures, errors = run_registry_tests()
    
    if success:
        print("✅ All Registry tests passed!")
    else:
        print(f"❌ Registry tests failed: {failures} failures, {errors} errors")
        sys.exit(1)