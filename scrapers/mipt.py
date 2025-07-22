#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MIPT (Moscow Institute of Physics and Technology) HTML scraper for application counts.

This module scrapes MIPT application data from HTML pages containing program 
information and extracts application counts based on data-index attributes.
"""

import time
from typing import Dict, List, Any, Optional

from core.http_client import ReliableHTTPClient
from core.logging_config import get_logger, log_scraper_result, log_performance

# Configure logger
logger = get_logger(__name__)

# MIPT program URLs and names
MIPT_PROGRAMS = [
    ('Науки о данных', 'https://priem.mipt.ru/applications_v2/bWFzdGVyL05hdWtpIG8gZGFubnlraF9Lb250cmFrdC5odG1s'),
    ('Современная комбинаторика', 'https://priem.mipt.ru/applications_v2/bWFzdGVyL1NvdnJlbWVubmF5YSBrb21iaW5hdG9yaWthX0tvbnRyYWt0Lmh0bWw='),
    ('Комбинаторика и цифровая экономика', 'https://priem.mipt.ru/applications_v2/bWFzdGVyL0tvbWJpbmF0b3Jpa2EgaSB0c2lmcm92YXlhIGVrb25vbWlrYV9Lb250cmFrdC5odG1s'),
    ('Contemporary combinatorics', 'https://priem.mipt.ru/applications_v2/bWFzdGVyL0NvbnRlbXBvcmFyeSBTb21iaW5hdG9yaWNzX0tvbnRyYWt0Lmh0bWw='),
    ('Modern Artificial Intelligence', 'https://priem.mipt.ru/applications_v2/bWFzdGVyL01vZGVybiBzdGF0ZSBvZiBBcnRpZmljaWFsIEludGVsbGlnZW5jZV9Lb250cmFrdC5odG1s'),
    ('Разработка IT-продукта', 'https://priem.mipt.ru/applications_v2/bWFzdGVyL1JhenJhYm90a2EgSVQtcHJvZHVrdGFfS29udHJha3QuaHRtbA=='),
    ('Управление IT-продуктами', 'https://priem.mipt.ru/applications_v2/bWFzdGVyL1VwcmF2bGVuaWUgSVQtcHJvZHVrdGFtaV9Lb250cmFrdC5odG1s')
]


def fetch_mipt_html(url: str) -> Optional[str]:
    """
    Fetch HTML content from MIPT URL with proper headers and timeout.
    
    Args:
        url: MIPT program URL to fetch
        
    Returns:
        HTML content as string, or None if fetch fails
    """
    start_time = time.time()
    logger.info(f"Fetching MIPT HTML from {url}")
    
    # Initialize HTTP client with proper configuration
    client = ReliableHTTPClient(
        timeout=30.0,
        connect_timeout=10.0,
        read_timeout=30.0,
        max_retries=3,
        retry_delay=1.0
    )
    
    try:
        # Add headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = client.get(url, headers=headers)
        
        if response.status_code == 200:
            fetch_time = time.time() - start_time
            logger.info(f"Successfully fetched MIPT HTML in {fetch_time:.2f}s")
            log_performance("mipt_html_fetch", fetch_time, {
                "url": url, 
                "content_length": len(response.text)
            })
            return response.text
        else:
            logger.error(f"HTTP {response.status_code} error fetching {url}")
            return None
            
    except Exception as e:
        fetch_time = time.time() - start_time
        logger.error(f"Error fetching MIPT HTML from {url}: {e} (after {fetch_time:.2f}s)")
        return None
    finally:
        try:
            client.close()
        except:
            pass


def parse_mipt_html(html_content: str) -> Optional[int]:
    """
    Parse HTML content to find data row elements and extract application count.
    
    Args:
        html_content: Raw HTML content from MIPT page
        
    Returns:
        Application count based on last row number, or None if parsing fails
    """
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try different row classes that MIPT uses
        data_elements = None
        class_used = None
        
        for row_class in ['R18', 'R11', 'R19', 'R0']:
            elements = soup.find_all('tr', class_=row_class)
            if elements:
                # Check if these are data rows (first cell should be numeric)
                first_cell = elements[0].find(['td', 'th'])
                if first_cell and first_cell.get_text().strip().isdigit():
                    data_elements = elements
                    class_used = row_class
                    break
        
        if not data_elements:
            logger.warning("No data row elements found in HTML")
            return None
        
        logger.info(f"Found {len(data_elements)} elements with class {class_used}")
        
        # Get the last element
        last_element = data_elements[-1]
        
        # Extract the first cell which contains the row number (application number)
        first_cell = last_element.find(['td', 'th'])
        
        if first_cell is None:
            logger.warning(f"Last {class_used} element has no cells")
            return None
        
        # Get the text content and convert to integer
        row_number_str = first_cell.get_text().strip()
        
        # Convert to integer and validate
        try:
            count = int(row_number_str)
            if count < 0:
                logger.warning(f"Negative row number value: {count}")
                return None
                
            logger.info(f"Extracted application count from last row (class {class_used}): {count}")
            return count
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid row number value '{row_number_str}': {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error parsing MIPT HTML: {e}")
        return None


def scrape_mipt_program(program_name: str, url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Scrape application count for a specific MIPT program.
    
    Args:
        program_name: Name of the MIPT program to scrape
        url: URL of the MIPT program page
        config: Optional configuration (for consistency with scraper interface)
        
    Returns:
        Dictionary with scraping result
    """
    start_time = time.time()
    
    # Create a clean scraper ID using transliteration for Russian text
    clean_name = (program_name
                 .replace('Науки о данных', 'data_science')
                 .replace('Современная комбинаторика', 'modern_combinatorics') 
                 .replace('Комбинаторика и цифровая экономика', 'combinatorics_digital_economy')
                 .replace('Contemporary combinatorics', 'contemporary_combinatorics')
                 .replace('Modern Artificial Intelligence', 'modern_ai')
                 .replace('Разработка IT-продукта', 'it_product_development')
                 .replace('Управление IT-продуктами', 'it_product_management')
                 .replace(' ', '_')
                 .replace('-', '_')
                 .lower())
    
    scraper_id = f"mipt_{clean_name}"
    
    logger.info(f"Starting MIPT program scraping for: {program_name}")
    
    try:
        # Fetch HTML content
        html_content = fetch_mipt_html(url)
        if html_content is None:
            return {
                'scraper_id': scraper_id,
                'program_name': program_name,
                'university': 'MIPT',
                'status': 'error',
                'error': 'Failed to fetch HTML content',
                'count': None,
                'scrape_time': time.time() - start_time
            }
        
        # Parse HTML and extract application count
        count = parse_mipt_html(html_content)
        if count is None:
            return {
                'scraper_id': scraper_id,
                'program_name': program_name,
                'university': 'MIPT',
                'status': 'error',
                'error': 'Failed to extract application count from HTML',
                'count': None,
                'scrape_time': time.time() - start_time
            }
        
        # Bounds checking for reasonable values
        if count > 10000:  # Sanity check - unlikely to have more than 10k applications
            logger.warning(f"Suspiciously high application count for {program_name}: {count}")
        
        scrape_time = time.time() - start_time
        
        result = {
            'scraper_id': scraper_id,
            'program_name': program_name,
            'university': 'MIPT',
            'status': 'success',
            'count': count,
            'scrape_time': scrape_time
        }
        
        logger.info(f"Successfully scraped {program_name}: {count} applications ({scrape_time:.2f}s)")
        log_scraper_result(scraper_id, 'SUCCESS', f"{count} applicants")
        
        return result
        
    except Exception as e:
        scrape_time = time.time() - start_time
        error_msg = f"Unexpected error scraping {program_name}: {e}"
        logger.error(f"{error_msg} after {scrape_time:.2f}s")
        
        log_scraper_result(scraper_id, 'ERROR', str(e))
        
        return {
            'scraper_id': scraper_id,
            'program_name': program_name,
            'university': 'MIPT',
            'status': 'error',
            'error': error_msg,
            'count': None,
            'scrape_time': scrape_time
        }


def get_scrapers() -> List[tuple]:
    """
    Get list of MIPT scraper functions for all target programs.
    
    Returns:
        List of tuples (scraper_function, config_dict) for each MIPT program
    """
    scrapers = []
    
    for program_name, url in MIPT_PROGRAMS:
        # Create a clean scraper ID using transliteration for Russian text
        clean_name = (program_name
                     .replace('Науки о данных', 'data_science')
                     .replace('Современная комбинаторика', 'modern_combinatorics') 
                     .replace('Комбинаторика и цифровая экономика', 'combinatorics_digital_economy')
                     .replace('Contemporary combinatorics', 'contemporary_combinatorics')
                     .replace('Modern Artificial Intelligence', 'modern_ai')
                     .replace('Разработка IT-продукта', 'it_product_development')
                     .replace('Управление IT-продуктами', 'it_product_management')
                     .replace(' ', '_')
                     .replace('-', '_')
                     .lower())
        
        scraper_id = f"mipt_{clean_name}"
        
        def make_scraper(prog_name, prog_url):
            """Create scraper function for specific program (closure)."""
            def scraper(config):
                return scrape_mipt_program(prog_name, prog_url, config)
            return scraper
        
        config = {
            'scraper_id': scraper_id,
            'name': f'МФТИ - {program_name}',
            'university': 'MIPT',
            'program_name': program_name,
            'url': url,
            'enabled': True
        }
        
        scrapers.append((make_scraper(program_name, url), config))
    
    logger.info(f"Created {len(scrapers)} MIPT scrapers for target programs")
    return scrapers


# For testing individual programs
if __name__ == "__main__":
    # Test with one program
    test_program = "Науки о данных"
    test_url = "https://priem.mipt.ru/applications_v2/bWFzdGVyL05hdWtpIG8gZGFubnlraF9Lb250cmFrdC5odG1s"
    
    print(f"Testing MIPT scraper with program: {test_program}")
    print(f"URL: {test_url}")
    
    result = scrape_mipt_program(test_program, test_url)
    print(f"Result: {result}")