#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEPhI (National Research Nuclear University) HTML scraper for application counts.

This module scrapes MEPhI application data from HTML pages containing program 
information and extracts application counts based on trPosBen elements.
"""

import time
from typing import Dict, List, Any, Optional

from core.http_client import ReliableHTTPClient
from core.logging_config import get_logger, log_scraper_result, log_performance

# Configure logger
logger = get_logger(__name__)

# MEPhI program URLs and names
MEPHI_PROGRAMS = [
    ('Машинное обучение и анализ данных', 'https://org.mephi.ru/pupil-rating/get-rating/entity/12843/original/no'),
    ('Информационные системы и технологии', 'https://org.mephi.ru/pupil-rating/get-rating/entity/12768/original/no'),
    ('Кибербезопасность', 'https://org.mephi.ru/pupil-rating/get-rating/entity/12847/original/no'),
    ('Математическое моделирование', 'https://org.mephi.ru/pupil-rating/get-rating/entity/12816/original/no'),
    ('Прикладная математика и информатика', 'https://org.mephi.ru/pupil-rating/get-rating/entity/12764/original/no'),
    ('Ядерные физика и технологии', 'https://org.mephi.ru/pupil-rating/get-rating/entity/13584/original/no')
]


def transliterate_program_name(program_name: str) -> str:
    """
    Transliterate Russian program name to English for clean scraper ID.
    
    Args:
        program_name: Russian program name
        
    Returns:
        Transliterated English name
    """
    clean_name = (program_name
                 .replace('Машинное обучение и анализ данных', 'machine_learning_data_analysis')
                 .replace('Информационные системы и технологии', 'information_systems_technologies') 
                 .replace('Кибербезопасность', 'cybersecurity')
                 .replace('Математическое моделирование', 'mathematical_modeling')
                 .replace('Прикладная математика и информатика', 'applied_mathematics_informatics')
                 .replace('Ядерные физика и технологии', 'nuclear_physics_technologies')
                 .replace(' ', '_')
                 .replace('-', '_')
                 .lower())
    return clean_name


def fetch_mephi_html(url: str) -> Optional[str]:
    """
    Fetch HTML content from MEPhI URL with proper headers and timeout.
    
    Args:
        url: MEPhI program URL to fetch
        
    Returns:
        HTML content as string, or None if fetch fails
    """
    start_time = time.time()
    logger.info(f"Fetching MEPhI HTML from {url}")
    
    # Initialize HTTP client with proper configuration
    client = ReliableHTTPClient(
        timeout=30.0,
        connect_timeout=10.0,
        read_timeout=30.0,
        max_retries=3,
        retry_delay=1.0
    )
    
    try:
        # Add headers to avoid blocking and handle authentication
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        
        response = client.get(url, headers=headers)
        
        if response.status_code == 200:
            fetch_time = time.time() - start_time
            logger.info(f"Successfully fetched MEPhI HTML in {fetch_time:.2f}s")
            log_performance("mephi_html_fetch", fetch_time, {
                "url": url, 
                "content_length": len(response.text)
            })
            return response.text
        else:
            logger.error(f"HTTP {response.status_code} error fetching {url}")
            return None
            
    except Exception as e:
        fetch_time = time.time() - start_time
        logger.error(f"Error fetching MEPhI HTML from {url}: {e} (after {fetch_time:.2f}s)")
        return None
    finally:
        try:
            client.close()
        except:
            pass


def parse_mephi_html(html_content: str) -> Optional[int]:
    """
    Parse HTML content to find trPosBen elements and extract application count.
    
    Args:
        html_content: Raw HTML content from MEPhI page
        
    Returns:
        Application count based on last position number, or None if parsing fails
    """
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all elements with class 'trPosBen'
        tr_pos_ben_elements = soup.find_all('tr', class_='trPosBen')
        
        if not tr_pos_ben_elements:
            logger.warning("No trPosBen elements found in HTML")
            return None
        
        logger.info(f"Found {len(tr_pos_ben_elements)} trPosBen elements")
        
        # Get the last element
        last_element = tr_pos_ben_elements[-1]
        
        # Find the 'pos' class element within the trPosBen element
        pos_element = last_element.find('td', class_='pos')
        
        if pos_element is None:
            logger.warning("No pos class element found in last trPosBen element")
            return None
        
        # Get the text content and convert to integer
        position_str = pos_element.get_text().strip()
        
        # Convert to integer and validate
        try:
            count = int(position_str)
            if count < 0:
                logger.warning(f"Negative position value: {count}")
                return None
                
            if count > 50000:  # Sanity check - unlikely to have more than 50k applications
                logger.warning(f"Suspiciously high position value: {count}")
                
            logger.info(f"Extracted application count from last trPosBen element: {count}")
            return count
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid position value '{position_str}': {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error parsing MEPhI HTML: {e}")
        return None


def scrape_mephi_program(program_name: str, url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Scrape application count for a specific MEPhI program.
    
    Args:
        program_name: Name of the MEPhI program to scrape
        url: URL of the MEPhI program page
        config: Optional configuration (for consistency with scraper interface)
        
    Returns:
        Dictionary with scraping result
    """
    start_time = time.time()
    
    # Create a clean scraper ID using transliteration for Russian text
    clean_name = transliterate_program_name(program_name)
    scraper_id = f"mephi_{clean_name}"
    
    logger.info(f"Starting MEPhI program scraping for: {program_name}")
    
    try:
        # Fetch HTML content
        html_content = fetch_mephi_html(url)
        if html_content is None:
            return {
                'scraper_id': scraper_id,
                'program_name': program_name,
                'university': 'MEPhI',
                'status': 'error',
                'error': 'Failed to fetch HTML content',
                'count': None,
                'scrape_time': time.time() - start_time
            }
        
        # Parse HTML and extract application count
        count = parse_mephi_html(html_content)
        if count is None:
            return {
                'scraper_id': scraper_id,
                'program_name': program_name,
                'university': 'MEPhI',
                'status': 'error',
                'error': 'Failed to extract application count from HTML',
                'count': None,
                'scrape_time': time.time() - start_time
            }
        
        scrape_time = time.time() - start_time
        
        result = {
            'scraper_id': scraper_id,
            'program_name': program_name,
            'university': 'MEPhI',
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
            'university': 'MEPhI',
            'status': 'error',
            'error': error_msg,
            'count': None,
            'scrape_time': scrape_time
        }


def get_scrapers() -> List[tuple]:
    """
    Get list of MEPhI scraper functions for all target programs.
    
    Returns:
        List of tuples (scraper_function, config_dict) for each MEPhI program
    """
    scrapers = []
    
    for program_name, url in MEPHI_PROGRAMS:
        # Create a clean scraper ID using transliteration for Russian text
        clean_name = transliterate_program_name(program_name)
        scraper_id = f"mephi_{clean_name}"
        
        def make_scraper(prog_name, prog_url):
            """Create scraper function for specific program (closure)."""
            def scraper(config):
                return scrape_mephi_program(prog_name, prog_url, config)
            return scraper
        
        config = {
            'scraper_id': scraper_id,
            'name': f'НИЯУ МИФИ - {program_name}',
            'university': 'MEPhI',
            'program_name': program_name,
            'url': url,
            'enabled': True
        }
        
        scrapers.append((make_scraper(program_name, url), config))
    
    logger.info(f"Created {len(scrapers)} MEPhI scrapers for target programs")
    return scrapers


# For testing individual programs
if __name__ == "__main__":
    # Test with one program
    test_program = "Машинное обучение и анализ данных"
    test_url = "https://pk.mephi.ru/abit/2024/lists_v2/4618b23e.html"
    
    print(f"Testing MEPhI scraper with program: {test_program}")
    print(f"URL: {test_url}")
    
    result = scrape_mephi_program(test_program, test_url)
    print(f"Result: {result}")