#!/usr/bin/env python3
"""
Google Sheets integration for syncing applicant count data.

This module provides functionality to sync scraping results to Google Sheets
for easy viewing and analysis.
"""

import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from .logging_config import get_logger
from .storage import Storage

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class GoogleSheetsSync:
    """
    Google Sheets synchronization client for applicant count data.
    
    Handles authentication, spreadsheet creation, and data syncing.
    """
    
    def __init__(self):
        """
        Initialize Google Sheets client.
        """
        self.credentials = None
        self.service = None
        self.spreadsheet_id = os.environ.get('GOOGLE_SPREADSHEET_ID')
        
        # Initialize Google Sheets service
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """
        Initialize Google Sheets API service with authentication.
        """
        try:
            # Try to import required Google libraries
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            # Get credentials from environment variable
            credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if not credentials_json:
                logger.error("GOOGLE_CREDENTIALS_JSON environment variable not set")
                return
            
            # Parse credentials
            try:
                credentials_data = json.loads(credentials_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                return
            
            # Create credentials object
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            self.credentials = Credentials.from_service_account_info(
                credentials_data, scopes=scopes
            )
            
            # Build service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Google Sheets service initialized successfully")
            
        except ImportError as e:
            logger.error(f"Google API libraries not installed: {e}")
            logger.error("Run: pip install google-api-python-client google-auth")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
    
    def is_available(self) -> bool:
        """
        Check if Google Sheets integration is available and configured.
        
        Returns:
            bool: True if service is ready to use.
        """
        return (self.service is not None and 
                self.spreadsheet_id is not None)
    
    def get_or_create_sheet(self, sheet_name: str) -> Optional[str]:
        """
        Get existing sheet or create new one with the given name.
        
        Args:
            sheet_name: Name of the sheet to get or create.
            
        Returns:
            Sheet ID if successful, None otherwise.
        """
        if not self.is_available():
            logger.error("Google Sheets service not available")
            return None
        
        try:
            # Get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            # Check if sheet already exists
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    logger.info(f"Found existing sheet '{sheet_name}' with ID {sheet_id}")
                    return str(sheet_id)
            
            # Create new sheet
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 20
                        }
                    }
                }
            }
            
            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
            logger.info(f"Created new sheet '{sheet_name}' with ID {sheet_id}")
            return str(sheet_id)
            
        except Exception as e:
            logger.error(f"Failed to get or create sheet '{sheet_name}': {e}")
            return None
    
    def sync_applicant_data(self, target_date: Optional[str] = None) -> bool:
        """
        Sync applicant count data to Google Sheets for a specific date.
        
        Args:
            target_date: Date to sync in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            bool: True if sync was successful.
        """
        if not self.is_available():
            logger.warning("Google Sheets not configured - skipping sync")
            return False
        
        try:
            # Use today if no date specified
            if target_date is None:
                target_date = date.today().isoformat()
            
            # Get data from database
            storage = Storage()
            result = storage.client.table('applicant_counts')\
                .select('*')\
                .eq('date', target_date)\
                .eq('status', 'success')\
                .order('name')\
                .execute()
            
            if not result.data:
                logger.warning(f"No data found for date {target_date}")
                return False
            
            # Format date for sheet name
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            sheet_name = f"Data_{date_obj.strftime('%Y_%m_%d')}"
            
            # Get or create sheet
            sheet_id = self.get_or_create_sheet(sheet_name)
            if not sheet_id:
                return False
            
            # Prepare data for sheets
            data_rows = []
            
            # Header row
            header = ['вуз', 'программа', 'количество заявлений', 'дата обновления', 'scraper_id']
            data_rows.append(header)
            
            # Data rows
            for record in result.data:
                # Determine university
                scraper_id = record['scraper_id']
                if scraper_id.startswith('hse_'):
                    university = 'НИУ ВШЭ'
                elif scraper_id.startswith('mipt_'):
                    university = 'МФТИ'
                elif scraper_id.startswith('mephi_'):
                    university = 'МИФИ'
                else:
                    university = 'Unknown'
                
                row = [
                    university,
                    record.get('name', record['scraper_id']),
                    record.get('count', 0),
                    target_date,
                    record['scraper_id']
                ]
                data_rows.append(row)
            
            # Clear existing data and write new data
            range_name = f"{sheet_name}!A:E"
            
            # Clear sheet
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            # Write data
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': data_rows}
            ).execute()
            
            # Format header row
            self._format_header_row(sheet_id)
            
            # Mark records as synced in database
            record_ids = [record['id'] for record in result.data]
            storage.mark_synced_to_sheets(record_ids)
            
            logger.info(f"Successfully synced {len(result.data)} records to Google Sheets for {target_date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync data to Google Sheets: {e}")
            return False
    
    def _format_header_row(self, sheet_id: str) -> None:
        """
        Format the header row with bold text and background color.
        
        Args:
            sheet_id: ID of the sheet to format.
        """
        try:
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': int(sheet_id),
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 5
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                },
                                'textFormat': {
                                    'bold': True
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            logger.warning(f"Failed to format header row: {e}")
    
    def sync_historical_data(self, days: int = 7) -> bool:
        """
        Sync historical data for the last N days.
        
        Args:
            days: Number of days to sync (default: 7).
            
        Returns:
            bool: True if all syncs were successful.
        """
        if not self.is_available():
            logger.warning("Google Sheets not configured - skipping historical sync")
            return False
        
        success_count = 0
        
        for i in range(days):
            target_date = (date.today() - timedelta(days=i)).isoformat()
            if self.sync_applicant_data(target_date):
                success_count += 1
        
        logger.info(f"Historical sync completed: {success_count}/{days} dates synced successfully")
        return success_count == days


# Convenience function for easy import
def sync_to_sheets(target_date: Optional[str] = None) -> bool:
    """
    Convenience function to sync data to Google Sheets.
    
    Args:
        target_date: Date to sync in YYYY-MM-DD format. Defaults to today.
        
    Returns:
        bool: True if sync was successful.
    """
    sheets_sync = GoogleSheetsSync()
    return sheets_sync.sync_applicant_data(target_date)


if __name__ == "__main__":
    # Test the sync functionality
    print("Testing Google Sheets sync...")
    
    sheets_sync = GoogleSheetsSync()
    
    if sheets_sync.is_available():
        print("✅ Google Sheets service is available")
        
        # Test sync for today
        success = sheets_sync.sync_applicant_data()
        if success:
            print("✅ Sync completed successfully")
        else:
            print("❌ Sync failed")
    else:
        print("❌ Google Sheets service not available")
        print("Please set GOOGLE_CREDENTIALS_JSON and GOOGLE_SPREADSHEET_ID environment variables")