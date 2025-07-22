#!/usr/bin/env python3
"""Unit tests for scrapers.mephi module."""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.mephi import (
    fetch_mephi_html,
    parse_mephi_html,
    scrape_mephi_program,
    get_scrapers,
    MEPHI_PROGRAMS
)


class TestMEPhIScraper(unittest.TestCase):
    """Test cases for the MEPhI scraper module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample HTML with trPosBen elements for testing
        self.sample_html = '''
        <!DOCTYPE html>
        <html>
        <head><title>MEPhI Application List</title></head>
        <body>
            <table>
                <tr class="trPosBen">
                    <td class="pos">1</td>
                    <td>Иванов Иван Иванович</td>
                    <td>250</td>
                </tr>
                <tr class="trPosBen">
                    <td class="pos">2</td>
                    <td>Петров Петр Петрович</td>
                    <td>240</td>
                </tr>
                <tr class="trPosBen">
                    <td class="pos">42</td>
                    <td>Сидоров Сидор Сидорович</td>
                    <td>200</td>
                </tr>
            </table>
        </body>
        </html>
        '''
        
        # HTML without trPosBen elements
        self.empty_html = '''
        <!DOCTYPE html>
        <html>
        <head><title>Empty Page</title></head>
        <body>
            <table>
                <tr class="otherClass">
                    <td>No relevant data</td>
                </tr>
            </table>
        </body>
        </html>
        '''
        
        # HTML with trPosBen but no pos elements
        self.no_pos_html = '''
        <!DOCTYPE html>
        <html>
        <body>
            <table>
                <tr class="trPosBen">
                    <td class="otherClass">No pos data</td>
                </tr>
            </table>
        </body>
        </html>
        '''
    
    @patch('scrapers.mephi.ReliableHTTPClient')
    def test_fetch_mephi_html_success(self, mock_client_class):
        """Test successful HTML fetching."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = self.sample_html
        
        # Mock the client instance
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        result = fetch_mephi_html("https://pk.mephi.ru/test.html")
        
        self.assertEqual(result, self.sample_html)
        mock_client_instance.get.assert_called_once()
        mock_client_instance.close.assert_called_once()
    
    @patch('scrapers.mephi.ReliableHTTPClient')
    def test_fetch_mephi_html_http_error(self, mock_client_class):
        """Test HTML fetching with HTTP error."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 404
        
        # Mock the client instance
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        result = fetch_mephi_html("https://pk.mephi.ru/notfound.html")
        
        self.assertIsNone(result)
        mock_client_instance.close.assert_called_once()
    
    @patch('scrapers.mephi.ReliableHTTPClient')
    def test_fetch_mephi_html_exception(self, mock_client_class):
        """Test HTML fetching with exception."""
        # Mock the client instance to raise exception
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = Exception("Connection failed")
        mock_client_class.return_value = mock_client_instance
        
        result = fetch_mephi_html("https://pk.mephi.ru/error.html")
        
        self.assertIsNone(result)
        mock_client_instance.close.assert_called_once()
    
    def test_parse_mephi_html_success(self):
        """Test successful HTML parsing."""
        result = parse_mephi_html(self.sample_html)
        
        self.assertEqual(result, 42)  # Should return the position from the last trPosBen element
    
    def test_parse_mephi_html_no_trposben(self):
        """Test HTML parsing with no trPosBen elements."""
        result = parse_mephi_html(self.empty_html)
        
        self.assertIsNone(result)
    
    def test_parse_mephi_html_no_pos_element(self):
        """Test HTML parsing with trPosBen but no pos elements."""
        result = parse_mephi_html(self.no_pos_html)
        
        self.assertIsNone(result)
    
    def test_parse_mephi_html_invalid_position(self):
        """Test HTML parsing with invalid position value."""
        invalid_html = '''
        <html>
        <body>
            <table>
                <tr class="trPosBen">
                    <td class="pos">not_a_number</td>
                </tr>
            </table>
        </body>
        </html>
        '''
        
        result = parse_mephi_html(invalid_html)
        
        self.assertIsNone(result)
    
    def test_parse_mephi_html_negative_position(self):
        """Test HTML parsing with negative position value."""
        negative_html = '''
        <html>
        <body>
            <table>
                <tr class="trPosBen">
                    <td class="pos">-5</td>
                </tr>
            </table>
        </body>
        </html>
        '''
        
        result = parse_mephi_html(negative_html)
        
        self.assertIsNone(result)
    
    def test_parse_mephi_html_high_position(self):
        """Test HTML parsing with suspiciously high position value."""
        high_html = '''
        <html>
        <body>
            <table>
                <tr class="trPosBen">
                    <td class="pos">60000</td>
                </tr>
            </table>
        </body>
        </html>
        '''
        
        result = parse_mephi_html(high_html)
        
        # Should still return the value, just log a warning
        self.assertEqual(result, 60000)
    
    def test_parse_mephi_html_malformed(self):
        """Test HTML parsing with malformed HTML."""
        malformed_html = "<html><body><table><tr class="
        
        # Should not crash but return None
        result = parse_mephi_html(malformed_html)
        self.assertIsNone(result)
    
    @patch('scrapers.mephi.fetch_mephi_html')
    @patch('scrapers.mephi.parse_mephi_html')
    def test_scrape_mephi_program_success(self, mock_parse, mock_fetch):
        """Test successful program scraping."""
        mock_fetch.return_value = self.sample_html
        mock_parse.return_value = 42
        
        result = scrape_mephi_program(
            'Машинное обучение и анализ данных', 
            'https://pk.mephi.ru/test.html'
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['count'], 42)
        self.assertEqual(result['university'], 'MEPhI')
        self.assertEqual(result['scraper_id'], 'mephi_machine_learning_data_analysis')
        self.assertIn('scrape_time', result)
    
    @patch('scrapers.mephi.fetch_mephi_html')
    def test_scrape_mephi_program_fetch_failure(self, mock_fetch):
        """Test program scraping when HTML fetch fails."""
        mock_fetch.return_value = None
        
        result = scrape_mephi_program(
            'Кибербезопасность', 
            'https://pk.mephi.ru/test.html'
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Failed to fetch HTML content', result['error'])
        self.assertIsNone(result['count'])
        self.assertEqual(result['scraper_id'], 'mephi_cybersecurity')
    
    @patch('scrapers.mephi.fetch_mephi_html')
    @patch('scrapers.mephi.parse_mephi_html')
    def test_scrape_mephi_program_parse_failure(self, mock_parse, mock_fetch):
        """Test program scraping when HTML parsing fails."""
        mock_fetch.return_value = self.sample_html
        mock_parse.return_value = None
        
        result = scrape_mephi_program(
            'Математическое моделирование', 
            'https://pk.mephi.ru/test.html'
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Failed to extract application count', result['error'])
        self.assertIsNone(result['count'])
        self.assertEqual(result['scraper_id'], 'mephi_mathematical_modeling')
    
    @patch('scrapers.mephi.fetch_mephi_html')
    def test_scrape_mephi_program_exception(self, mock_fetch):
        """Test program scraping when exception occurs."""
        mock_fetch.side_effect = Exception("Unexpected error")
        
        result = scrape_mephi_program(
            'Прикладная математика и информатика', 
            'https://pk.mephi.ru/test.html'
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Unexpected error scraping', result['error'])
        self.assertIsNone(result['count'])
        self.assertEqual(result['scraper_id'], 'mephi_applied_mathematics_informatics')
    
    def test_get_scrapers(self):
        """Test getting list of all MEPhI scrapers."""
        scrapers = get_scrapers()
        
        # Should have one scraper for each MEPhI program
        self.assertEqual(len(scrapers), len(MEPHI_PROGRAMS))
        
        # Check first scraper structure
        scraper_func, config = scrapers[0]
        
        self.assertTrue(callable(scraper_func))
        self.assertIn('scraper_id', config)
        self.assertIn('name', config)
        self.assertIn('university', config)
        self.assertEqual(config['university'], 'MEPhI')
        self.assertTrue(config['enabled'])
    
    def test_scraper_id_generation(self):
        """Test that scraper IDs are generated correctly."""
        scrapers = get_scrapers()
        
        # Test that IDs are unique and properly formatted
        scraper_ids = [config['scraper_id'] for _, config in scrapers]
        
        self.assertEqual(len(scraper_ids), len(set(scraper_ids)))  # All unique
        
        # Check specific ID format
        for scraper_id in scraper_ids:
            self.assertTrue(scraper_id.startswith('mephi_'))
            self.assertNotIn(' ', scraper_id)  # No spaces
            self.assertNotIn('и', scraper_id)  # Should be transliterated
    
    def test_program_list_completeness(self):
        """Test that all target programs are included."""
        scrapers = get_scrapers()
        scraper_programs = [config['program_name'] for _, config in scrapers]
        
        for program_name, _ in MEPHI_PROGRAMS:
            self.assertIn(program_name, scraper_programs)
    
    @patch('scrapers.mephi.scrape_mephi_program')
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
    
    def test_transliteration_edge_cases(self):
        """Test transliteration of various Russian program names."""
        test_cases = [
            ('Машинное обучение и анализ данных', 'mephi_machine_learning_data_analysis'),
            ('Информационные системы и технологии', 'mephi_information_systems_technologies'),
            ('Кибербезопасность', 'mephi_cybersecurity'),
            ('Математическое моделирование', 'mephi_mathematical_modeling'),
            ('Прикладная математика и информатика', 'mephi_applied_mathematics_informatics'),
            ('Ядерные физика и технологии', 'mephi_nuclear_physics_technologies')
        ]
        
        scrapers = get_scrapers()
        scraper_configs = {config['program_name']: config['scraper_id'] for _, config in scrapers}
        
        for program_name, expected_id in test_cases:
            if program_name in scraper_configs:
                self.assertEqual(scraper_configs[program_name], expected_id)
    
    def test_html_structure_edge_cases(self):
        """Test parsing with various HTML structure edge cases."""
        # Empty trPosBen elements
        empty_trposben = '''
        <html><body><table>
            <tr class="trPosBen"></tr>
        </table></body></html>
        '''
        result = parse_mephi_html(empty_trposben)
        self.assertIsNone(result)
        
        # Multiple pos elements in one trPosBen
        multiple_pos = '''
        <html><body><table>
            <tr class="trPosBen">
                <td class="pos">10</td>
                <td class="pos">20</td>
            </tr>
        </table></body></html>
        '''
        result = parse_mephi_html(multiple_pos)
        self.assertEqual(result, 10)  # Should take first pos element
        
        # Zero position
        zero_pos = '''
        <html><body><table>
            <tr class="trPosBen">
                <td class="pos">0</td>
            </tr>
        </table></body></html>
        '''
        result = parse_mephi_html(zero_pos)
        self.assertEqual(result, 0)  # Zero is valid
    
    def test_config_parameter_handling(self):
        """Test that config parameter is handled correctly."""
        with patch('scrapers.mephi.fetch_mephi_html') as mock_fetch, \
             patch('scrapers.mephi.parse_mephi_html') as mock_parse:
            
            mock_fetch.return_value = self.sample_html
            mock_parse.return_value = 15
            
            # Test with config parameter
            test_config = {'some_key': 'some_value'}
            result = scrape_mephi_program(
                'Test Program', 
                'https://test.url',
                config=test_config
            )
            
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['count'], 15)
            
            # Test without config parameter
            result2 = scrape_mephi_program(
                'Test Program', 
                'https://test.url'
            )
            
            self.assertEqual(result2['status'], 'success')
            self.assertEqual(result2['count'], 15)


def run_mephi_tests():
    """Run all MEPhI tests and return results."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMEPhIScraper)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == '__main__':
    print("Running MEPhI scraper tests...")
    success, failures, errors = run_mephi_tests()
    
    if success:
        print("✅ All MEPhI scraper tests passed!")
    else:
        print(f"❌ MEPhI scraper tests failed: {failures} failures, {errors} errors")
        sys.exit(1)