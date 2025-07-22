"""Logging configuration for edu-parser project."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """
    Set up logging configuration for the entire project.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    # Get log level from environment or use provided default
    level_name = os.environ.get("LOG_LEVEL", log_level).upper()
    level = getattr(logging, level_name, logging.INFO)
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    today = datetime.now().strftime("%Y-%m-%d")
    all_logs_file = log_path / f"edu-parser-{today}.log"
    file_handler = logging.FileHandler(all_logs_file)
    file_handler.setLevel(logging.DEBUG)  # Always capture DEBUG in files
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_file = log_path / f"errors-{today}.log"
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Scraping results file handler
    results_file = log_path / f"scraping-results-{today}.log"
    results_handler = logging.FileHandler(results_file)
    results_handler.setLevel(logging.INFO)
    results_handler.setFormatter(detailed_formatter)
    
    # Create a filter for scraping-specific logs
    class ScrapingFilter(logging.Filter):
        def filter(self, record):
            return 'scraper' in record.name.lower() or 'scraping' in record.getMessage().lower()
    
    results_handler.addFilter(ScrapingFilter())
    root_logger.addHandler(results_handler)
    
    # Configure specific loggers
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    # Ensure our modules log at the right level
    logging.getLogger('core').setLevel(level)
    logging.getLogger('scrapers').setLevel(level)
    logging.getLogger('sync').setLevel(level)
    
    root_logger.info(f"Logging initialized - Level: {level_name}, Logs dir: {log_path.absolute()}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_scraper_result(scraper_id: str, status: str, count: int = None, error: str = None) -> None:
    """
    Log a scraper result in a standardized format.
    
    Args:
        scraper_id: Unique scraper identifier
        status: 'success' or 'error'
        count: Number of applicants (if successful)
        error: Error message (if failed)
    """
    logger = get_logger('scrapers.results')
    
    if status == 'success':
        logger.info(f"SCRAPER_RESULT: {scraper_id} -> SUCCESS: {count} applicants")
    else:
        logger.error(f"SCRAPER_RESULT: {scraper_id} -> ERROR: {error}")


def log_performance(operation: str, duration: float, details: str = None) -> None:
    """
    Log performance metrics.
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        details: Additional details about the operation
    """
    logger = get_logger('performance')
    message = f"PERFORMANCE: {operation} took {duration:.2f}s"
    if details:
        message += f" - {details}"
    logger.info(message)