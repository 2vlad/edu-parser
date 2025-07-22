"""Scraper runner with error isolation - ensures one scraper failure doesn't affect others."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable
from datetime import datetime

from .logging_config import get_logger, log_scraper_result, log_performance
from .storage import Storage


logger = get_logger(__name__)


class ScraperRunner:
    """
    Runs multiple scrapers with error isolation.
    
    Each scraper runs in isolation - if one fails, others continue.
    """
    
    def __init__(self, storage: Storage = None, max_workers: int = 10):
        """
        Initialize scraper runner.
        
        Args:
            storage: Storage instance for saving results
            max_workers: Maximum concurrent scrapers
        """
        self.storage = storage or Storage()
        self.max_workers = max_workers
        self.results = []
        
        logger.info(f"ScraperRunner initialized with max_workers={max_workers}")
    
    def run_scraper_isolated(self, scraper_func: Callable, scraper_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single scraper in complete isolation.
        
        Args:
            scraper_func: The scraper function to execute
            scraper_config: Configuration for this scraper
            
        Returns:
            Result dictionary with success/error information
        """
        scraper_id = scraper_config.get('scraper_id', 'unknown')
        start_time = time.time()
        
        logger.info(f"STARTING scraper: {scraper_id}")
        
        try:
            # Execute scraper with timeout protection
            result = scraper_func(scraper_config)
            
            duration = time.time() - start_time
            
            if result.get('status') == 'success':
                count = result.get('count', 'N/A')
                logger.info(f"SUCCESS scraper {scraper_id}: {count} applicants in {duration:.2f}s")
                log_scraper_result(scraper_id, 'success', count)
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"FAILED scraper {scraper_id}: {error} in {duration:.2f}s")
                log_scraper_result(scraper_id, 'error', error=error)
            
            log_performance(f"scraper_{scraper_id}", duration, f"status={result.get('status')}")
            
            # Save to database immediately
            if self.storage:
                saved = self.storage.save_result(result)
                if not saved:
                    logger.error(f"Failed to save result for {scraper_id} to database")
            
            return result
            
        except Exception as e:
            # Complete isolation - catch ANY exception
            duration = time.time() - start_time
            error_msg = f"Critical failure: {str(e)}"
            
            logger.error(f"CRITICAL ERROR in scraper {scraper_id}: {error_msg} after {duration:.2f}s")
            log_scraper_result(scraper_id, 'error', error=error_msg)
            log_performance(f"scraper_{scraper_id}_error", duration, f"error={str(e)[:50]}")
            
            # Create error result
            error_result = {
                'scraper_id': scraper_id,
                'name': scraper_config.get('name', f'Unknown - {scraper_id}'),
                'count': None,
                'status': 'error',
                'error': error_msg
            }
            
            # Try to save error result
            try:
                if self.storage:
                    self.storage.save_result(error_result)
            except Exception as save_error:
                logger.error(f"Failed to save error result for {scraper_id}: {save_error}")
            
            return error_result
    
    def run_all_scrapers(self, scraper_functions: List[tuple]) -> List[Dict[str, Any]]:
        """
        Run all scrapers concurrently with complete error isolation.
        
        Args:
            scraper_functions: List of (scraper_func, scraper_config) tuples
            
        Returns:
            List of results from all scrapers
        """
        if not scraper_functions:
            logger.warning("No scrapers provided to run")
            return []
        
        start_time = time.time()
        logger.info(f"Starting batch execution of {len(scraper_functions)} scrapers")
        
        results = []
        
        # Use ThreadPoolExecutor for true isolation
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all scrapers
            future_to_scraper = {
                executor.submit(self.run_scraper_isolated, func, config): config.get('scraper_id', 'unknown')
                for func, config in scraper_functions
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_scraper):
                scraper_id = future_to_scraper[future]
                completed += 1
                
                try:
                    result = future.result(timeout=300)  # 5 minute max per scraper
                    results.append(result)
                    logger.info(f"Completed {completed}/{len(scraper_functions)}: {scraper_id}")
                    
                except Exception as e:
                    # Even future.result() is isolated
                    logger.error(f"Future execution failed for {scraper_id}: {e}")
                    error_result = {
                        'scraper_id': scraper_id,
                        'name': f'Future error - {scraper_id}',
                        'count': None,
                        'status': 'error',
                        'error': f'Future execution error: {str(e)}'
                    }
                    results.append(error_result)
        
        # Summary statistics
        total_duration = time.time() - start_time
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = len(results) - successful
        
        logger.info("=" * 50)
        logger.info("BATCH EXECUTION COMPLETE")
        logger.info(f"Total time: {total_duration:.2f}s")
        logger.info(f"Successful: {successful}/{len(results)}")
        logger.info(f"Failed: {failed}/{len(results)}")
        logger.info(f"Success rate: {(successful/len(results)*100):.1f}%")
        logger.info("=" * 50)
        
        log_performance("batch_scraping", total_duration, 
                       f"scrapers={len(results)}, success={successful}, failed={failed}")
        
        self.results = results
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics from last run."""
        if not self.results:
            return {"error": "No results available"}
        
        successful = [r for r in self.results if r.get('status') == 'success']
        failed = [r for r in self.results if r.get('status') == 'error']
        
        total_applicants = sum(r.get('count', 0) for r in successful if r.get('count'))
        
        return {
            'total_scrapers': len(self.results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.results) * 100,
            'total_applicants': total_applicants,
            'errors': [{'scraper_id': r['scraper_id'], 'error': r.get('error')} for r in failed]
        }