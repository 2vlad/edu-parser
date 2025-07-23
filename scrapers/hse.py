#!/usr/bin/env python3
"""HSE University Excel scraper for application counts.

This module scrapes HSE (Higher School of Economics) application data
from Excel files containing program information and application counts.
"""

import io
import time
from typing import Dict, List, Any, Optional
import pandas as pd
from fuzzywuzzy import fuzz

from core.http_client import download_excel_safe
from core.logging_config import get_logger, log_scraper_result, log_performance

# Configure logger
logger = get_logger(__name__)

# HSE Excel file URL
HSE_EXCEL_URL = "https://priem45.hse.ru/ABITREPORTS/MAGREPORTS/FullTime/39121437.xls"

# Target HSE programs to scrape
HSE_TARGET_PROGRAMS = [
    "ОНЛАЙН Аналитика больших данных",
    "ОНЛАЙН Аналитика данных и прикладная статистика",
    "ОНЛАЙН Инвестиции на финансовых рынках",
    "ОНЛАЙН Инженерия данных",
    "ОНЛАЙН Интерактивный дизайн",
    "ОНЛАЙН Искусственный интеллект",
    "ОНЛАЙН Искусственный интеллект в маркетинге и управлении продуктом",
    "ОНЛАЙН Кибербезопасность",
    "ОНЛАЙН Китайский язык в межкультурной бизнес-коммуникации",
    "ОНЛАЙН ЛигалТех",
    "ОНЛАЙН Магистр аналитики бизнеса",
    "ОНЛАЙН Магистр по наукам о данных",
    "ОНЛАЙН Маркетинг - менеджмент",
    "ОНЛАЙН Педагогический дизайн: теория и практика обучения",
    "ОНЛАЙН Прикладная социальная психология",
    "ОНЛАЙН Управление в креативных индустриях",
    "ОНЛАЙН Управление инновационным бизнесом",
    "ОНЛАЙН Управление стратегическими коммуникациями",
    "ОНЛАЙН Управление цифровым продуктом",
    "ОНЛАЙН Финансы",
    "ОНЛАЙН Цифровая инженерия для компьютерных игр",
    "ОНЛАЙН Цифровая урбанистика и аналитика города",
    "ОНЛАЙН Экономический анализ"
]

# Column name for application counts (may vary)
APPLICATION_COUNT_COLUMNS = [
    "Количество поданных заявлений в магистратуру\nМосква на 22.07.2025\nОсновной этап",  # Current format July 2025
    "Количество заявлений (места с оплатой стоимости обучения)",
    "Количество заявлений",
    "Заявлений",
    "Кол-во заявлений"
]


def download_hse_excel() -> Optional[pd.DataFrame]:
    """
    Download HSE Excel file and return as pandas DataFrame.
    
    Returns:
        DataFrame with HSE program data, or None if download fails
    """
    start_time = time.time()
    logger.info(f"Starting HSE Excel download from {HSE_EXCEL_URL}")
    
    try:
        # Download Excel content using our reliable HTTP client
        excel_content = download_excel_safe(HSE_EXCEL_URL)
        
        if not excel_content:
            logger.error("Failed to download HSE Excel file - no content received")
            return None
        
        # Parse Excel content into DataFrame
        df = pd.read_excel(io.BytesIO(excel_content), engine='xlrd')
        
        download_time = time.time() - start_time
        logger.info(f"Successfully downloaded HSE Excel file in {download_time:.2f}s - {len(df)} rows")
        log_performance("hse_excel_download", download_time, {"rows": len(df), "size_bytes": len(excel_content)})
        
        return df
        
    except Exception as e:
        download_time = time.time() - start_time
        error_msg = f"Failed to download/parse HSE Excel file: {e}"
        logger.error(f"{error_msg} after {download_time:.2f}s")
        return None


def find_application_count_column(df: pd.DataFrame) -> Optional[str]:
    """
    Find the correct column name for application counts.
    
    Args:
        df: DataFrame with HSE data
        
    Returns:
        Column name for application counts, or None if not found
    """
    available_columns = df.columns.tolist()
    logger.debug(f"Available Excel columns: {available_columns}")
    
    # Try exact matches first
    for col_name in APPLICATION_COUNT_COLUMNS:
        if col_name in available_columns:
            logger.info(f"Found application count column: '{col_name}'")
            return col_name
    
    # Try fuzzy matching
    for col_name in APPLICATION_COUNT_COLUMNS:
        for available_col in available_columns:
            similarity = fuzz.ratio(col_name.lower(), available_col.lower())
            if similarity > 80:  # 80% similarity threshold
                logger.info(f"Found application count column via fuzzy match: '{available_col}' (similarity: {similarity}%)")
                return available_col
    
    logger.warning(f"Could not find application count column. Available columns: {available_columns}")
    return None


def find_program_in_dataframe(df: pd.DataFrame, program_name: str, count_column: str) -> Optional[Dict[str, Any]]:
    """
    Find a specific program in the DataFrame and extract its data.
    
    Args:
        df: DataFrame with HSE data
        program_name: Name of program to find
        count_column: Column name containing application counts
        
    Returns:
        Dictionary with program data, or None if not found
    """
    # Based on debug analysis: program names are in column 0, counts in column 6
    program_col_idx = 0
    count_col_idx = 6
    
    # Ensure we have enough columns
    if len(df.columns) <= max(program_col_idx, count_col_idx):
        logger.warning(f"DataFrame doesn't have enough columns. Has {len(df.columns)}, need at least {max(program_col_idx, count_col_idx) + 1}")
        return None
    
    program_column = df.columns[program_col_idx]
    actual_count_column = df.columns[count_col_idx]
    
    logger.info(f"Looking for program '{program_name}' in column '{program_column}' with counts in column '{actual_count_column}'")
    
    # Look for exact matches first in the program column
    for index, row in df.iterrows():
        cell_value = str(row[program_column]).strip()
        
        if pd.isna(row[program_column]) or cell_value == 'nan':
            continue
            
        # Exact match
        if program_name.lower() == cell_value.lower():
            count = row[actual_count_column]
            logger.info(f"Found exact match for '{program_name}' with {count} applications")
            return {
                'program_name': program_name,
                'found_text': cell_value,
                'count': count,
                'match_type': 'exact',
                'row_index': index
            }
    
    # Try fuzzy matching in the program column
    best_match = None
    best_similarity = 0
    
    for index, row in df.iterrows():
        cell_value = str(row[program_column]).strip()
        
        if pd.isna(row[program_column]) or cell_value == 'nan' or len(cell_value) <= 10:
            continue
            
        similarity = fuzz.ratio(program_name.lower(), cell_value.lower())
        
        if similarity > best_similarity and similarity > 70:  # 70% threshold
            count = row[actual_count_column]
            best_match = {
                'program_name': program_name,
                'found_text': cell_value,
                'count': count,
                'match_type': 'fuzzy',
                'similarity': similarity,
                'row_index': index
            }
            best_similarity = similarity
    
    if best_match:
        logger.info(f"Found fuzzy match for '{program_name}': '{best_match['found_text']}' "
                   f"(similarity: {best_match['similarity']}%) with {best_match['count']} applications")
        return best_match
    
    logger.warning(f"Could not find program '{program_name}' in HSE Excel data")
    return None


def scrape_hse_program(program_name: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Scrape application count for a specific HSE program.
    
    Args:
        program_name: Name of the HSE program to scrape
        config: Optional configuration (for consistency with scraper interface)
        
    Returns:
        Dictionary with scraping result
    """
    start_time = time.time()
    scraper_id = f"hse_{program_name.lower().replace(' ', '_').replace('онлайн_', '')}"
    
    logger.info(f"Starting HSE program scraping for: {program_name}")
    
    try:
        # Download Excel file
        df = download_hse_excel()
        if df is None:
            return {
                'scraper_id': scraper_id,
                'name': f'HSE - {program_name}',
                'program_name': program_name,
                'university': 'HSE',
                'status': 'error',
                'error': 'Failed to download Excel file',
                'count': None,
                'scrape_time': time.time() - start_time
            }
        
        # Find application count column
        count_column = find_application_count_column(df)
        if not count_column:
            return {
                'scraper_id': scraper_id,
                'name': f'HSE - {program_name}',
                'program_name': program_name,
                'university': 'HSE',
                'status': 'error',
                'error': 'Could not find application count column',
                'count': None,
                'scrape_time': time.time() - start_time
            }
        
        # Find program data
        program_data = find_program_in_dataframe(df, program_name, count_column)
        if not program_data:
            return {
                'scraper_id': scraper_id,
                'name': f'HSE - {program_name}',
                'program_name': program_name,
                'university': 'HSE',
                'status': 'error',
                'error': f'Program not found in Excel data',
                'count': None,
                'scrape_time': time.time() - start_time
            }
        
        # Validate and clean count data
        count = program_data['count']
        try:
            if pd.isna(count) or count is None or count == '':
                clean_count = 0
            else:
                clean_count = int(float(str(count)))
        except (ValueError, TypeError):
            logger.warning(f"Invalid count value for {program_name}: {count}")
            clean_count = 0
        
        scrape_time = time.time() - start_time
        
        result = {
            'scraper_id': scraper_id,
            'name': f'HSE - {program_name}',
            'program_name': program_name,
            'university': 'HSE',
            'status': 'success',
            'count': clean_count,
            'match_type': program_data.get('match_type', 'unknown'),
            'found_text': program_data.get('found_text', ''),
            'scrape_time': scrape_time
        }
        
        logger.info(f"Successfully scraped {program_name}: {clean_count} applications ({scrape_time:.2f}s)")
        log_scraper_result(scraper_id, 'SUCCESS', f"{clean_count} applicants")
        
        return result
        
    except Exception as e:
        scrape_time = time.time() - start_time
        error_msg = f"Unexpected error scraping {program_name}: {e}"
        logger.error(f"{error_msg} after {scrape_time:.2f}s")
        
        log_scraper_result(scraper_id, 'ERROR', str(e))
        
        return {
            'scraper_id': scraper_id,
            'name': f'HSE - {program_name}',
            'program_name': program_name,
            'university': 'HSE',
            'status': 'error',
            'error': error_msg,
            'count': None,
            'scrape_time': scrape_time
        }


def get_scrapers() -> List[tuple]:
    """
    Get list of HSE scraper functions for all target programs.
    
    Returns:
        List of tuples (scraper_function, config_dict) for each HSE program
    """
    scrapers = []
    
    for program_name in HSE_TARGET_PROGRAMS:
        scraper_id = f"hse_{program_name.lower().replace(' ', '_').replace('онлайн_', '')}"
        
        def make_scraper(prog_name):
            """Create scraper function for specific program (closure)."""
            def scraper(config):
                return scrape_hse_program(prog_name, config)
            return scraper
        
        config = {
            'scraper_id': scraper_id,
            'name': f'HSE - {program_name}',
            'university': 'HSE',
            'program_name': program_name,
            'enabled': True
        }
        
        scrapers.append((make_scraper(program_name), config))
    
    logger.info(f"Created {len(scrapers)} HSE scrapers for target programs")
    return scrapers


# For testing individual programs
if __name__ == "__main__":
    # Test with one program
    test_program = "ОНЛАЙН Аналитика больших данных"
    print(f"Testing HSE scraper with program: {test_program}")
    
    result = scrape_hse_program(test_program)
    print(f"Result: {result}")