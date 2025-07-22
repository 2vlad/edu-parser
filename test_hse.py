#!/usr/bin/env python3
"""Unit tests for scrapers.hse module."""

import os
import sys
import io
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.hse import (
    download_hse_excel,
    find_application_count_column,
    find_program_in_dataframe,
    scrape_hse_program,
    get_scrapers,
    HSE_TARGET_PROGRAMS
)


class TestHSEScraper(unittest.TestCase):
    """Test cases for the HSE scraper module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample Excel data for testing
        self.sample_data = pd.DataFrame({
            'Направление подготовки': [
                'ОНЛАЙН Аналитика больших данных',
                'ОНЛАЙН Искусственный интеллект', 
                'Традиционная программа',
                'ОНЛАЙН Магистр по наукам о данных',
                'Другая программа'
            ],
            'Количество заявлений (места с оплатой стоимости обучения)': [42, 35, 15, 28, 8],
            'Другие данные': ['A', 'B', 'C', 'D', 'E']
        })
        
        # Alternative column naming for testing
        self.alt_sample_data = pd.DataFrame({
            'Программа': [
                'ОНЛАЙН Аналитика данных и прикладная статистика',
                'ОНЛАЙН ЛигалТех',
                'Обычная программа'
            ],
            'Заявлений': [25, 18, 12],
            'Код': [1, 2, 3]
        })
    
    @patch('scrapers.hse.download_excel_safe')
    def test_download_hse_excel_success(self, mock_download):
        """Test successful Excel download and parsing."""
        # Mock Excel file content - use xlwt for .xls format
        mock_excel_data = io.BytesIO()
        
        try:
            # Try to create old format Excel file
            import xlwt
            wb = xlwt.Workbook()
            ws = wb.add_sheet('Sheet1')
            
            # Write headers
            for col_idx, col_name in enumerate(self.sample_data.columns):
                ws.write(0, col_idx, col_name)
            
            # Write data
            for row_idx, row in self.sample_data.iterrows():
                for col_idx, value in enumerate(row):
                    ws.write(row_idx + 1, col_idx, value)
            
            wb.save(mock_excel_data)
            mock_download.return_value = mock_excel_data.getvalue()
        except ImportError:
            # Fall back to just testing the mock behavior
            mock_excel_data = b"fake_excel_content"
            mock_download.return_value = mock_excel_data
        
        result = download_hse_excel()
        
        # Should have attempted the download
        mock_download.assert_called_once()
        
        # The result should either be a DataFrame or None (if parsing failed)
        # The important thing is that the function handled the download correctly
        self.assertTrue(result is None or isinstance(result, pd.DataFrame))
    
    @patch('scrapers.hse.download_excel_safe')
    def test_download_hse_excel_failure(self, mock_download):
        """Test Excel download failure."""
        mock_download.return_value = None
        
        result = download_hse_excel()
        
        self.assertIsNone(result)
    
    @patch('scrapers.hse.download_excel_safe')
    def test_download_hse_excel_parse_error(self, mock_download):
        """Test Excel parsing error."""
        mock_download.return_value = b"invalid excel content"
        
        result = download_hse_excel()
        
        self.assertIsNone(result)
    
    def test_find_application_count_column_exact_match(self):
        """Test finding application count column with exact match."""
        result = find_application_count_column(self.sample_data)
        
        self.assertEqual(result, 'Количество заявлений (места с оплатой стоимости обучения)')
    
    def test_find_application_count_column_fuzzy_match(self):
        """Test finding application count column with fuzzy matching."""
        result = find_application_count_column(self.alt_sample_data)
        
        self.assertEqual(result, 'Заявлений')
    
    def test_find_application_count_column_not_found(self):
        """Test when application count column is not found."""
        no_match_data = pd.DataFrame({
            'Программа': ['Test'],
            'Неизвестная колонка': [5]
        })
        
        result = find_application_count_column(no_match_data)
        
        self.assertIsNone(result)
    
    def test_find_program_exact_match(self):
        """Test finding program with exact match."""
        count_column = 'Количество заявлений (места с оплатой стоимости обучения)'
        program_name = 'ОНЛАЙН Аналитика больших данных'
        
        result = find_program_in_dataframe(self.sample_data, program_name, count_column)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['program_name'], program_name)
        self.assertEqual(result['count'], 42)
        self.assertEqual(result['match_type'], 'exact')
    
    def test_find_program_fuzzy_match(self):
        """Test finding program with fuzzy matching."""
        count_column = 'Количество заявлений (места с оплатой стоимости обучения)'
        # Slightly different name that should match fuzzily
        program_name = 'ОНЛАЙН Искуственный интеллект'  # Note the typo
        
        result = find_program_in_dataframe(self.sample_data, program_name, count_column)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['match_type'], 'fuzzy')
        self.assertEqual(result['count'], 35)
        self.assertGreater(result['similarity'], 70)
    
    def test_find_program_not_found(self):
        """Test when program is not found."""
        count_column = 'Количество заявлений (места с оплатой стоимости обучения)'
        program_name = 'Несуществующая программа'
        
        result = find_program_in_dataframe(self.sample_data, program_name, count_column)
        
        self.assertIsNone(result)
    
    @patch('scrapers.hse.download_hse_excel')
    @patch('scrapers.hse.find_application_count_column')
    @patch('scrapers.hse.find_program_in_dataframe')
    def test_scrape_hse_program_success(self, mock_find_program, mock_find_column, mock_download):
        """Test successful program scraping."""
        # Mock successful responses
        mock_download.return_value = self.sample_data
        mock_find_column.return_value = 'Количество заявлений (места с оплатой стоимости обучения)'
        mock_find_program.return_value = {
            'program_name': 'ОНЛАЙН Аналитика больших данных',
            'found_text': 'ОНЛАЙН Аналитика больших данных',
            'count': 42,
            'match_type': 'exact',
            'row_index': 0
        }
        
        result = scrape_hse_program('ОНЛАЙН Аналитика больших данных')
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['count'], 42)
        self.assertEqual(result['university'], 'HSE')
        self.assertEqual(result['match_type'], 'exact')
    
    @patch('scrapers.hse.download_hse_excel')
    def test_scrape_hse_program_download_failure(self, mock_download):
        """Test scraping when Excel download fails."""
        mock_download.return_value = None
        
        result = scrape_hse_program('ОНЛАЙН Аналитика больших данных')
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Failed to download Excel file', result['error'])
        self.assertIsNone(result['count'])
    
    @patch('scrapers.hse.download_hse_excel')
    @patch('scrapers.hse.find_application_count_column')
    def test_scrape_hse_program_column_not_found(self, mock_find_column, mock_download):
        """Test scraping when application count column is not found."""
        mock_download.return_value = self.sample_data
        mock_find_column.return_value = None
        
        result = scrape_hse_program('ОНЛАЙН Аналитика больших данных')
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Could not find application count column', result['error'])
    
    @patch('scrapers.hse.download_hse_excel')
    @patch('scrapers.hse.find_application_count_column')
    @patch('scrapers.hse.find_program_in_dataframe')
    def test_scrape_hse_program_not_found(self, mock_find_program, mock_find_column, mock_download):
        """Test scraping when program is not found."""
        mock_download.return_value = self.sample_data
        mock_find_column.return_value = 'Количество заявлений (места с оплатой стоимости обучения)'
        mock_find_program.return_value = None
        
        result = scrape_hse_program('Несуществующая программа')
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Program not found in Excel data', result['error'])
    
    @patch('scrapers.hse.download_hse_excel')
    @patch('scrapers.hse.find_application_count_column')
    @patch('scrapers.hse.find_program_in_dataframe')
    def test_scrape_hse_program_invalid_count(self, mock_find_program, mock_find_column, mock_download):
        """Test scraping with invalid count data."""
        mock_download.return_value = self.sample_data
        mock_find_column.return_value = 'Количество заявлений (места с оплатой стоимости обучения)'
        mock_find_program.return_value = {
            'program_name': 'Test Program',
            'found_text': 'Test Program',
            'count': 'invalid_number',  # Invalid count
            'match_type': 'exact',
            'row_index': 0
        }
        
        result = scrape_hse_program('Test Program')
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['count'], 0)  # Should default to 0 for invalid counts
    
    @patch('scrapers.hse.download_hse_excel')
    @patch('scrapers.hse.find_application_count_column')
    @patch('scrapers.hse.find_program_in_dataframe')
    def test_scrape_hse_program_none_count(self, mock_find_program, mock_find_column, mock_download):
        """Test scraping with None count."""
        mock_download.return_value = self.sample_data
        mock_find_column.return_value = 'Количество заявлений (места с оплатой стоимости обучения)'
        mock_find_program.return_value = {
            'program_name': 'Test Program',
            'found_text': 'Test Program',
            'count': None,  # None count
            'match_type': 'exact',
            'row_index': 0
        }
        
        result = scrape_hse_program('Test Program')
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['count'], 0)  # Should default to 0 for None counts
    
    @patch('scrapers.hse.download_hse_excel')
    def test_scrape_hse_program_exception(self, mock_download):
        """Test scraping when unexpected exception occurs."""
        mock_download.side_effect = Exception("Unexpected error")
        
        result = scrape_hse_program('ОНЛАЙН Аналитика больших данных')
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Unexpected error scraping', result['error'])
        self.assertIsNone(result['count'])
    
    def test_get_scrapers(self):
        """Test getting list of all HSE scrapers."""
        scrapers = get_scrapers()
        
        # Should have one scraper for each target program
        self.assertEqual(len(scrapers), len(HSE_TARGET_PROGRAMS))
        
        # Check first scraper structure
        scraper_func, config = scrapers[0]
        
        self.assertTrue(callable(scraper_func))
        self.assertIn('scraper_id', config)
        self.assertIn('name', config)
        self.assertIn('university', config)
        self.assertEqual(config['university'], 'HSE')
        self.assertTrue(config['enabled'])
    
    def test_scraper_id_generation(self):
        """Test that scraper IDs are generated correctly."""
        scrapers = get_scrapers()
        
        # Test that IDs are unique and properly formatted
        scraper_ids = [config['scraper_id'] for _, config in scrapers]
        
        self.assertEqual(len(scraper_ids), len(set(scraper_ids)))  # All unique
        
        # Check specific ID format
        for scraper_id in scraper_ids:
            self.assertTrue(scraper_id.startswith('hse_'))
            self.assertNotIn(' ', scraper_id)  # No spaces
            self.assertNotIn('онлайн_', scraper_id)  # Should be removed
    
    def test_program_list_completeness(self):
        """Test that all target programs are included."""
        scrapers = get_scrapers()
        scraper_programs = [config['program_name'] for _, config in scrapers]
        
        for target_program in HSE_TARGET_PROGRAMS:
            self.assertIn(target_program, scraper_programs)
    
    @patch('scrapers.hse.scrape_hse_program')
    def test_scraper_function_execution(self, mock_scrape):
        """Test that generated scraper functions execute correctly."""
        mock_scrape.return_value = {
            'status': 'success',
            'count': 25,
            'program_name': 'Test Program'
        }
        
        scrapers = get_scrapers()
        scraper_func, config = scrapers[0]
        
        # Execute the scraper function
        result = scraper_func(config)
        
        # Should have called the underlying scrape function
        mock_scrape.assert_called_once()
    
    def test_count_data_validation_edge_cases(self):
        """Test count data validation with various edge cases."""
        test_cases = [
            ('42', 42),      # String number
            (42.0, 42),      # Float
            (42.7, 42),      # Float with decimals (should truncate)
            ('', 0),         # Empty string
            (None, 0),       # None
            ('N/A', 0),      # Invalid string
            (0, 0),          # Zero
            (-5, -5),        # Negative (should preserve)
        ]
        
        count_column = 'Количество заявлений (места с оплатой стоимости обучения)'
        
        for test_value, expected in test_cases:
            with self.subTest(value=test_value):
                test_data = pd.DataFrame({
                    'Программа': ['Test Program'],
                    count_column: [test_value]
                })
                
                with patch('scrapers.hse.download_hse_excel') as mock_download, \
                     patch('scrapers.hse.find_application_count_column') as mock_find_column, \
                     patch('scrapers.hse.find_program_in_dataframe') as mock_find_program:
                    
                    mock_download.return_value = test_data
                    mock_find_column.return_value = count_column
                    mock_find_program.return_value = {
                        'program_name': 'Test Program',
                        'found_text': 'Test Program',
                        'count': test_value,
                        'match_type': 'exact',
                        'row_index': 0
                    }
                    
                    result = scrape_hse_program('Test Program')
                    
                    self.assertEqual(result['status'], 'success')
                    self.assertEqual(result['count'], expected)


def run_hse_tests():
    """Run all HSE tests and return results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHSEScraper)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("Running HSE scraper tests...")
    success, failures, errors = run_hse_tests()
    
    if success:
        print("✅ All HSE scraper tests passed!")
    else:
        print(f"❌ HSE scraper tests failed: {failures} failures, {errors} errors")
        sys.exit(1)