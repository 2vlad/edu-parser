"""Core storage module for interacting with Supabase database."""

import os
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


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
        # Validate required fields
        required_fields = ['scraper_id', 'name', 'status']
        for field in required_fields:
            if field not in result:
                logger.error(f"Missing required field: {field}")
                return False
        
        if result['status'] not in ['success', 'error']:
            logger.error(f"Invalid status: {result['status']}. Must be 'success' or 'error'")
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
            
            response = self.client.table('applicant_counts').insert(data).execute()
            logger.info(f"Successfully saved result for {result['scraper_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save result for {result.get('scraper_id', 'unknown')}: {e}")
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
            response = self.client.table('applicant_counts').insert(batch_data).execute()
            successful_saves = len(batch_data)
            logger.info(f"Successfully saved {successful_saves} results in batch")
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