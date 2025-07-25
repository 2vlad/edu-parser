"""Core storage module for interacting with Supabase database."""

import os
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv

from .logging_config import get_logger, log_performance
import time

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class StorageError(Exception):
    """Custom exception for storage-related errors."""
    pass


class Storage:
    """
    Storage class for managing database operations with Supabase.
    
    Handles saving scraping results, retrieving scraper configurations,
    and providing monitoring functionality.
    """
    
    def __init__(self):
        """
        Initialize Storage with Supabase client.
        
        Raises:
            StorageError: If environment variables are missing or connection fails.
        """
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        
        if not url:
            raise StorageError("SUPABASE_URL environment variable is required")
        
        if not key:
            raise StorageError("SUPABASE_KEY environment variable is required")
        
        try:
            self.client: Client = create_client(url, key)
            logger.info("Storage initialized successfully")
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise StorageError(f"Failed to connect to database: {e}")
    
    def _test_connection(self) -> None:
        """
        Test database connection by querying scrapers_config table.
        
        Raises:
            StorageError: If connection test fails.
        """
        try:
            # Simple query to test connection
            response = self.client.table('scrapers_config').select('scraper_id').limit(1).execute()
            logger.debug("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise StorageError(f"Database connection test failed: {e}")
    
    def save_result(self, result: Dict[str, Any]) -> bool:
        """
        Save a single scraping result to the database.
        
        Args:
            result: Dictionary containing scraping result data with keys:
                   - scraper_id (str): Unique scraper identifier
                   - name (str): Human-readable scraper name
                   - count (int, optional): Number of applicants
                   - status (str): 'success' or 'error'
                   - error (str, optional): Error message if status is 'error'
        
        Returns:
            bool: True if save was successful, False otherwise.
        """
        start_time = time.time()
        scraper_id = result.get('scraper_id', 'unknown')
        
        logger.debug(f"Starting to save result for {scraper_id}")
        
        # Validate required fields
        required_fields = ['scraper_id', 'name', 'status']
        for field in required_fields:
            if field not in result:
                logger.error(f"Validation failed - Missing required field: {field} for {scraper_id}")
                return False
        
        if result['status'] not in ['success', 'error']:
            logger.error(f"Validation failed - Invalid status: {result['status']} for {scraper_id}. Must be 'success' or 'error'")
            return False
        
        try:
            data = {
                'scraper_id': result['scraper_id'],
                'name': result['name'],
                'count': result.get('count'),
                'status': result['status'],
                'error': result.get('error'),
                'date': date.today().isoformat(),
                'synced_to_sheets': False
            }
            
            # Remove None values to let database handle defaults
            data = {k: v for k, v in data.items() if v is not None}
            
            # UPSERT logic: first delete existing records for this scraper_id + date combination
            today_str = data['date']
            logger.debug(f"Performing UPSERT for {scraper_id} on {today_str}")
            
            # Delete existing records for this scraper + date
            delete_response = self.client.table('applicant_counts')\
                .delete()\
                .eq('scraper_id', scraper_id)\
                .eq('date', today_str)\
                .execute()
            
            # Insert new record
            logger.debug(f"Inserting data for {scraper_id}: {data}")
            response = self.client.table('applicant_counts').insert(data).execute()
            
            duration = time.time() - start_time
            logger.info(f"Successfully saved result for {scraper_id} (count: {result.get('count', 'N/A')})")
            log_performance("save_result", duration, f"scraper_id={scraper_id}")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed to save result for {scraper_id}: {e}")
            log_performance("save_result_failed", duration, f"scraper_id={scraper_id}, error={str(e)[:100]}")
            return False
    
    def get_enabled_scrapers(self) -> List[Dict[str, Any]]:
        """
        Retrieve all enabled scraper configurations from the database.
        
        Returns:
            List of dictionaries containing scraper configuration data.
            Returns empty list if query fails.
        """
        try:
            response = self.client.table('scrapers_config') \
                .select('*') \
                .eq('enabled', True) \
                .order('scraper_id') \
                .execute()
            
            logger.info(f"Retrieved {len(response.data)} enabled scrapers")
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to get enabled scrapers: {e}")
            return []
    
    def get_today_results(self) -> List[Dict[str, Any]]:
        """
        Get all scraping results for today.
        
        Returns:
            List of dictionaries containing today's results.
            Returns empty list if query fails.
        """
        try:
            today = date.today().isoformat()
            response = self.client.table('applicant_counts') \
                .select('*') \
                .eq('date', today) \
                .order('created_at', desc=True) \
                .execute()
            
            logger.info(f"Retrieved {len(response.data)} results for today")
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to get today's results: {e}")
            return []
    
    def batch_save_results(self, results: List[Dict[str, Any]]) -> int:
        """
        Save multiple scraping results in a single batch operation.
        
        Args:
            results: List of result dictionaries (same format as save_result)
        
        Returns:
            int: Number of successfully saved results.
        """
        if not results:
            logger.warning("No results provided to batch_save_results")
            return 0
        
        successful_saves = 0
        batch_data = []
        today = date.today().isoformat()
        
        # Prepare batch data
        for result in results:
            # Validate required fields
            required_fields = ['scraper_id', 'name', 'status']
            if not all(field in result for field in required_fields):
                logger.error(f"Skipping invalid result: {result}")
                continue
            
            if result['status'] not in ['success', 'error']:
                logger.error(f"Skipping result with invalid status: {result}")
                continue
            
            data = {
                'scraper_id': result['scraper_id'],
                'name': result['name'],
                'count': result.get('count'),
                'status': result['status'],
                'error': result.get('error'),
                'date': today,
                'synced_to_sheets': False
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            batch_data.append(data)
        
        if not batch_data:
            logger.warning("No valid results to save in batch")
            return 0
        
        try:
            # UPSERT logic for batch: first delete all existing records for these scrapers + date
            scraper_ids = [data['scraper_id'] for data in batch_data]
            
            logger.debug(f"Performing batch UPSERT for {len(scraper_ids)} scrapers on {today}")
            
            # Delete existing records for these scrapers + date
            delete_response = self.client.table('applicant_counts')\
                .delete()\
                .in_('scraper_id', scraper_ids)\
                .eq('date', today)\
                .execute()
            
            # Insert new records
            response = self.client.table('applicant_counts').insert(batch_data).execute()
            successful_saves = len(batch_data)
            logger.info(f"Successfully saved {successful_saves} results in batch (UPSERT)")
            return successful_saves
            
        except Exception as e:
            logger.error(f"Batch save failed, falling back to individual saves: {e}")
            
            # Fallback to individual saves
            for result in results:
                if self.save_result(result):
                    successful_saves += 1
        
        return successful_saves
    
    def get_scraper_by_id(self, scraper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific scraper configuration by ID.
        
        Args:
            scraper_id: The scraper identifier
            
        Returns:
            Scraper configuration dictionary or None if not found.
        """
        try:
            response = self.client.table('scrapers_config') \
                .select('*') \
                .eq('scraper_id', scraper_id) \
                .limit(1) \
                .execute()
            
            if response.data:
                return response.data[0]
            else:
                logger.warning(f"Scraper {scraper_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get scraper {scraper_id}: {e}")
            return None
    
    def mark_synced_to_sheets(self, result_ids: List[str]) -> int:
        """
        Mark results as synced to Google Sheets.
        
        Args:
            result_ids: List of result IDs to mark as synced
            
        Returns:
            Number of successfully updated records.
        """
        if not result_ids:
            return 0
        
        try:
            # Update records in batch
            response = self.client.table('applicant_counts') \
                .update({'synced_to_sheets': True}) \
                .in_('id', result_ids) \
                .execute()
            
            updated_count = len(result_ids)  # Assume success for all
            logger.info(f"Marked {updated_count} results as synced to sheets")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to mark results as synced: {e}")
            return 0