#!/usr/bin/env python3
"""
Dynamic Google Sheets with date columns management.

Manages a single master sheet where each day a new column is added with date
and applicant counts are updated in the corresponding rows.
"""

import os
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

from .logging_config import get_logger
from .storage import Storage

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


class DynamicSheetsManager:
    """
    Manages a dynamic Google Sheet with date columns.
    
    Structure:
    | вуз | программа | URL | 21 июль | 22 июль | 23 июль | ...
    """
    
    def __init__(self):
        """Initialize the dynamic sheets manager."""
        self.credentials = None
        self.service = None
        self.spreadsheet_id = os.environ.get('GOOGLE_SPREADSHEET_ID')
        self.master_sheet_name = "Лист1"  # Default main sheet name
        
        # Initialize Google Sheets service
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize Google Sheets API service with authentication."""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if not credentials_json:
                logger.error("GOOGLE_CREDENTIALS_JSON environment variable not set")
                return
            
            try:
                credentials_data = json.loads(credentials_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                return
            
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            self.credentials = Credentials.from_service_account_info(
                credentials_data, scopes=scopes
            )
            
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Dynamic Sheets service initialized successfully")
            
        except ImportError as e:
            logger.error(f"Google API libraries not installed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Dynamic Sheets service: {e}")
    
    def is_available(self) -> bool:
        """Check if Dynamic Sheets is available and configured."""
        return (self.service is not None and 
                self.spreadsheet_id is not None)
    
    def get_sheet_data(self) -> Optional[List[List[str]]]:
        """Get current sheet data to analyze structure."""
        if not self.is_available():
            return None
        
        try:
            range_name = f"{self.master_sheet_name}!A:Z"  # Get first 26 columns
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
            
        except Exception as e:
            logger.error(f"Failed to get sheet data: {e}")
            return None
    
    def find_date_column(self, target_date: str) -> Optional[int]:
        """
        Find column index for a specific date.
        
        Args:
            target_date: Date in format 'DD месяц' (e.g., '23 июль')
            
        Returns:
            Column index (0-based) or None if not found
        """
        data = self.get_sheet_data()
        if not data or len(data) < 1:
            return None
        
        header_row = data[0]
        
        for i, cell in enumerate(header_row):
            if cell.strip() == target_date:
                return i
        
        return None
    
    def add_date_column(self, target_date: str) -> Optional[int]:
        """
        Add a new date column to the sheet in reverse chronological order.
        New columns are inserted right after static columns (before existing date columns).
        
        Args:
            target_date: Date in format 'DD месяц' (e.g., '23 июль')
            
        Returns:
            Column index where the date was added, or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            data = self.get_sheet_data()
            if not data:
                logger.error("No data found in sheet")
                return None
            
            # Static columns: вуз (A), программа (B), URL (C)
            # New date columns should be inserted at position D (index 3)
            # This pushes existing date columns to the right
            static_columns = 3
            insert_column_index = static_columns
            
            # First, insert a new column at the desired position
            requests = [
                {
                    'insertDimension': {
                        'range': {
                            'sheetId': 0,  # Assuming first sheet
                            'dimension': 'COLUMNS',
                            'startIndex': insert_column_index,
                            'endIndex': insert_column_index + 1
                        },
                        'inheritFromBefore': False
                    }
                }
            ]
            
            # Execute the column insertion
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            # Convert column index to letter (A, B, C, ...)
            column_letter = chr(ord('A') + insert_column_index)
            
            # Add header for the new date column
            range_name = f"{self.master_sheet_name}!{column_letter}1"
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [[target_date]]}
            ).execute()
            
            # Format the header
            self._format_date_header(insert_column_index)
            
            logger.info(f"Added date column '{target_date}' at index {insert_column_index} (reverse chronological order)")
            return insert_column_index
            
        except Exception as e:
            logger.error(f"Failed to add date column: {e}")
            return None
    
    def _format_date_header(self, column_index: int) -> None:
        """Format the date header cell."""
        try:
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,  # Assuming first sheet
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': column_index,
                            'endColumnIndex': column_index + 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.8,
                                    'green': 0.9,
                                    'blue': 1.0
                                },
                                'textFormat': {
                                    'bold': True
                                },
                                'horizontalAlignment': 'CENTER'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            logger.warning(f"Failed to format date header: {e}")
    
    def get_programs_mapping(self) -> Dict[str, int]:
        """
        Get mapping of program names to row indices.
        
        Returns:
            Dict mapping program names to row indices (1-based)
        """
        data = self.get_sheet_data()
        if not data or len(data) < 2:
            return {}
        
        mapping = {}
        
        for i, row in enumerate(data[1:], start=2):  # Skip header, start from row 2
            if len(row) >= 2:  # Need at least вуз and программа
                university = row[0].strip() if len(row) > 0 else ""
                program = row[1].strip() if len(row) > 1 else ""
                
                if university and program:
                    # Create key that matches our data format
                    key = f"{university} - {program}"
                    mapping[key] = i
        
        return mapping
    
    def update_daily_data(self, target_date: Optional[str] = None) -> bool:
        """
        Update the sheet with daily data for a specific date.
        
        Args:
            target_date: Date in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            bool: True if update was successful.
        """
        if not self.is_available():
            logger.warning("Dynamic Sheets not configured - skipping update")
            return False
        
        try:
            # Use today if no date specified
            if target_date is None:
                target_date = date.today().isoformat()
            
            # Format date for column header (DD месяц)
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
                     'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
            formatted_date = f"{date_obj.day} {months[date_obj.month - 1]}"
            
            logger.info(f"Updating dynamic sheet for {formatted_date} ({target_date})")
            
            # Check if date column exists, if not create it
            column_index = self.find_date_column(formatted_date)
            if column_index is None:
                column_index = self.add_date_column(formatted_date)
                if column_index is None:
                    logger.error("Failed to create date column")
                    return False
            
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
            
            # Get programs mapping from sheet
            programs_mapping = self.get_programs_mapping()
            
            # Prepare updates
            updates = []
            updated_count = 0
            
            for record in result.data:
                # Determine university and create key
                scraper_id = record['scraper_id']
                if scraper_id.startswith('hse_'):
                    university = 'НИУ ВШЭ'
                elif scraper_id.startswith('mipt_'):
                    university = 'МФТИ'
                elif scraper_id.startswith('mephi_'):
                    university = 'МИФИ'
                else:
                    university = 'Unknown'
                
                program_name = record.get('name', record['scraper_id'])
                
                # Clean program name - remove university prefix if present
                if program_name.startswith('HSE - '):
                    program_name = program_name[6:]  # Remove "HSE - "
                elif program_name.startswith('МФТИ - '):
                    program_name = program_name[7:]  # Remove "МФТИ - "
                elif program_name.startswith('НИЯУ МИФИ - '):
                    program_name = program_name[12:]  # Remove "НИЯУ МИФИ - "
                
                program_key = f"{university} - {program_name}"
                
                # Find row for this program
                row_index = programs_mapping.get(program_key)
                if row_index is None:
                    logger.warning(f"Program not found in sheet: {program_key}")
                    continue
                
                # Convert column index to letter
                column_letter = chr(ord('A') + column_index)
                range_name = f"{self.master_sheet_name}!{column_letter}{row_index}"
                
                # Add update
                updates.append({
                    'range': range_name,
                    'values': [[record.get('count', 0)]]
                })
                updated_count += 1
            
            # Apply all updates in batch
            if updates:
                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={
                        'valueInputOption': 'RAW',
                        'data': updates
                    }
                ).execute()
                
                logger.info(f"Successfully updated {updated_count} programs for {formatted_date}")
                return True
            else:
                logger.warning("No programs to update")
                return False
            
        except Exception as e:
            logger.error(f"Failed to update daily data: {e}")
            return False


# Convenience function
def update_dynamic_sheets(target_date: Optional[str] = None) -> bool:
    """
    Convenience function to update dynamic sheets.
    
    Args:
        target_date: Date to update in YYYY-MM-DD format. Defaults to today.
        
    Returns:
        bool: True if update was successful.
    """
    manager = DynamicSheetsManager()
    return manager.update_daily_data(target_date)


if __name__ == "__main__":
    # Test the dynamic sheets functionality
    print("Testing Dynamic Sheets management...")
    
    manager = DynamicSheetsManager()
    
    if manager.is_available():
        print("✅ Dynamic Sheets service is available")
        
        # Test update for today
        success = manager.update_daily_data()
        if success:
            print("✅ Daily data update completed successfully")
        else:
            print("❌ Daily data update failed")
    else:
        print("❌ Dynamic Sheets service not available")
        print("Please set GOOGLE_CREDENTIALS_JSON and GOOGLE_SPREADSHEET_ID environment variables")