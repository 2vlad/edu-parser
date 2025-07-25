#!/usr/bin/env python3
"""
Dynamic Google Sheets with date columns management.

Manages a single master sheet where each day a new column is added with date
and applicant counts are updated in the corresponding rows.
"""

import os
import json
import time
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
            
            # Check if column already exists
            existing_column_index = self.find_date_column(target_date)
            if existing_column_index is not None:
                logger.info(f"Date column '{target_date}' already exists at index {existing_column_index}")
                return existing_column_index
            
            # Parse date to determine correct insertion position
            # Format: "DD месяц" -> need to convert to comparable date
            months_map = {
                'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
                'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
            }
            
            # Extract day and month from target date
            parts = target_date.strip().split()
            if len(parts) != 2:
                logger.error(f"Invalid date format: {target_date}")
                return None
                
            try:
                day = int(parts[0])
                month_name = parts[1].lower()[:3]  # Take first 3 chars
                month = months_map.get(month_name, 0)
                
                if month == 0:
                    logger.error(f"Unknown month: {parts[1]}")
                    return None
                    
                # Assume current year for comparison
                from datetime import datetime
                current_year = datetime.now().year
                target_date_obj = datetime(current_year, month, day)
                
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing date '{target_date}': {e}")
                return None
            
            # Find correct insertion position based on chronological order
            header_row = data[0] if data else []
            static_columns = 3  # вуз (A), программа (B), URL (C)
            insert_column_index = static_columns
            
            # Check existing date columns to find correct position
            for i in range(static_columns, len(header_row)):
                col_header = header_row[i].strip()
                if not col_header:  # Skip empty columns
                    continue
                    
                # Try to parse existing column date
                col_parts = col_header.split()
                if len(col_parts) == 2:
                    try:
                        col_day = int(col_parts[0])
                        col_month_name = col_parts[1].lower()[:3]
                        col_month = months_map.get(col_month_name, 0)
                        
                        if col_month != 0:
                            col_date_obj = datetime(current_year, col_month, col_day)
                            
                            # If target date is newer (more recent), insert before this column
                            if target_date_obj > col_date_obj:
                                insert_column_index = i
                                break
                    except (ValueError, KeyError):
                        continue
            
            # If we went through all columns and didn't find a place, 
            # insert at the beginning of date columns (most recent date goes first)
            if insert_column_index == static_columns:
                # For reverse chronological order, newest dates go right after static columns
                insert_column_index = static_columns  # Insert at column D (index 3)
            
            # Insert a new column at the calculated position
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
            
            # Execute the column insertion with retry
            def insert_column():
                return self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()
            
            self._retry_with_backoff(
                insert_column,
                f"Insert column for {target_date}",
                max_retries=5
            )
            
            # Convert column index to letter (A, B, C, ...)
            column_letter = chr(ord('A') + insert_column_index)
            
            # Add header for the new date column with retry
            range_name = f"{self.master_sheet_name}!{column_letter}1"
            
            def add_header():
                return self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [[target_date]]}
                ).execute()
            
            self._retry_with_backoff(
                add_header,
                f"Add header for {target_date}",
                max_retries=3
            )
            
            # Format the header
            try:
                self._format_date_header(insert_column_index)
            except Exception as e:
                logger.warning(f"Failed to format header, continuing: {e}")
            
            # Verify the column was created correctly
            logger.info(f"Verifying column creation for {target_date}...")
            time.sleep(1)  # Brief pause for Google Sheets to process
            
            if self._verify_column_exists(target_date, insert_column_index):
                logger.info(f"✅ Added date column '{target_date}' at index {insert_column_index} (reverse chronological order)")
                return insert_column_index
            else:
                logger.error(f"❌ Column verification failed for {target_date}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to add date column: {e}")
            return None
    
    def cleanup_and_reorganize_columns(self) -> bool:
        """
        Clean up test columns and reorganize date columns in proper reverse chronological order.
        
        Returns:
            bool: True if cleanup was successful
        """
        if not self.is_available():
            return False
            
        try:
            # Get current sheet data
            data = self.get_sheet_data()
            if not data or len(data) == 0:
                logger.error("No data found in sheet")
                return False
                
            header_row = data[0]
            static_columns = 3  # вуз, программа, URL
            
            # Parse all date columns
            months_map = {
                'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
                'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
            }
            
            date_columns = []
            for i in range(static_columns, len(header_row)):
                col_header = header_row[i].strip()
                if not col_header:
                    continue
                    
                parts = col_header.split()
                if len(parts) == 2:
                    try:
                        day = int(parts[0])
                        month_name = parts[1].lower()[:3]
                        month = months_map.get(month_name, 0)
                        
                        if month != 0:
                            from datetime import datetime
                            current_year = datetime.now().year
                            date_obj = datetime(current_year, month, day)
                            date_columns.append({
                                'index': i,
                                'header': col_header,
                                'date': date_obj,
                                'data': [row[i] if i < len(row) else '' for row in data[1:]]
                            })
                    except (ValueError, KeyError):
                        continue
            
            if not date_columns:
                logger.info("No date columns found to reorganize")
                return True
                
            # Sort date columns in reverse chronological order (newest first)
            date_columns.sort(key=lambda x: x['date'], reverse=True)
            
            # Delete all existing date columns (starting from the rightmost)
            delete_requests = []
            for col in sorted(date_columns, key=lambda x: x['index'], reverse=True):
                delete_requests.append({
                    'deleteDimension': {
                        'range': {
                            'sheetId': 0,
                            'dimension': 'COLUMNS',
                            'startIndex': col['index'],
                            'endIndex': col['index'] + 1
                        }
                    }
                })
            
            if delete_requests:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': delete_requests}
                ).execute()
                
            # Re-add columns in correct order
            for idx, col in enumerate(date_columns):
                column_index = static_columns + idx
                
                # Insert column
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [{
                        'insertDimension': {
                            'range': {
                                'sheetId': 0,
                                'dimension': 'COLUMNS',
                                'startIndex': column_index,
                                'endIndex': column_index + 1
                            }
                        }
                    }]}
                ).execute()
                
                # Add header
                column_letter = chr(ord('A') + column_index)
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.master_sheet_name}!{column_letter}1",
                    valueInputOption='RAW',
                    body={'values': [[col['header']]]}
                ).execute()
                
                # Add data if exists
                if col['data']:
                    data_range = f"{self.master_sheet_name}!{column_letter}2:{column_letter}{len(col['data']) + 1}"
                    values = [[val] for val in col['data']]
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=data_range,
                        valueInputOption='RAW',
                        body={'values': values}
                    ).execute()
                
                # Format header
                self._format_date_header(column_index)
                
            logger.info(f"Successfully reorganized {len(date_columns)} date columns in reverse chronological order")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup and reorganize columns: {e}")
            return False
    
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
    
    def add_missing_programs(self, target_date: Optional[str] = None) -> int:
        """
        Add missing programs to the sheet based on database data.
        
        Args:
            target_date: Date in YYYY-MM-DD format to check for programs. Defaults to today.
            
        Returns:
            int: Number of programs added.
        """
        if not self.is_available():
            return 0
        
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
                return 0
            
            # Get current programs mapping
            programs_mapping = self.get_programs_mapping()
            
            # Find missing programs
            missing_programs = []
            
            for record in result.data:
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
                
                # Clean program name
                if program_name.startswith('HSE - '):
                    program_name = program_name[6:]
                elif program_name.startswith('МФТИ - '):
                    program_name = program_name[7:]
                elif program_name.startswith('НИЯУ МИФИ - '):
                    program_name = program_name[12:]
                
                program_key = f"{university} - {program_name}"
                
                if program_key not in programs_mapping:
                    missing_programs.append({
                        'university': university,
                        'program': program_name,
                        'url': record.get('url', '')
                    })
            
            if not missing_programs:
                logger.info("No missing programs found")
                return 0
            
            # Get current sheet data to find next row
            data = self.get_sheet_data()
            next_row = len(data) + 1 if data else 2  # Start from row 2 (after header)
            
            # Prepare data for batch append
            values_to_append = []
            for program in missing_programs:
                values_to_append.append([
                    program['university'],
                    program['program'],
                    program['url']
                ])
            
            # Append new programs to the sheet
            range_name = f"{self.master_sheet_name}!A{next_row}:C"
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': values_to_append}
            ).execute()
            
            logger.info(f"Added {len(missing_programs)} missing programs to sheet")
            return len(missing_programs)
            
        except Exception as e:
            logger.error(f"Failed to add missing programs: {e}")
            return 0

    def _retry_with_backoff(self, operation_func, operation_name: str, max_retries: int = 3) -> Any:
        """
        Execute an operation with exponential backoff retry.
        
        Args:
            operation_func: Function to execute
            operation_name: Name of the operation for logging
            max_retries: Maximum number of retry attempts
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                result = operation_func()
                if attempt > 0:
                    logger.info(f"✅ {operation_name} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                wait_time = (2 ** attempt) + 1  # 1, 3, 5 seconds
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ {operation_name} failed on attempt {attempt + 1}: {e}")
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ {operation_name} failed after {max_retries} attempts: {e}")
                    raise
    
    def _verify_column_exists(self, target_date: str, expected_index: int) -> bool:
        """
        Verify that a date column was actually created at the expected position.
        
        Args:
            target_date: Date string to verify (e.g., '25 июл')
            expected_index: Expected column index
            
        Returns:
            True if column exists at expected position, False otherwise
        """
        try:
            data = self.get_sheet_data()
            if not data or len(data) < 1:
                return False
            
            header_row = data[0]
            if expected_index >= len(header_row):
                return False
                
            actual_header = header_row[expected_index].strip()
            return actual_header == target_date
        except Exception as e:
            logger.warning(f"Failed to verify column existence: {e}")
            return False
    
    def _verify_data_written(self, column_index: int, expected_records: int) -> bool:
        """
        Verify that data was actually written to the specified column.
        
        Args:
            column_index: Column index to verify
            expected_records: Expected number of non-empty records
            
        Returns:
            True if data verification passes, False otherwise
        """
        try:
            data = self.get_sheet_data()
            if not data or len(data) < 2:
                return False
            
            # Count non-empty cells in the column (skip header)
            non_empty_count = 0
            for row in data[1:]:  # Skip header row
                if column_index < len(row) and str(row[column_index]).strip():
                    non_empty_count += 1
            
            # Allow some tolerance (90% of expected records)
            min_expected = max(1, int(expected_records * 0.9))
            success = non_empty_count >= min_expected
            
            if success:
                logger.info(f"✅ Data verification passed: {non_empty_count}/{expected_records} records written")
            else:
                logger.warning(f"⚠️ Data verification failed: only {non_empty_count}/{expected_records} records written")
                
            return success
        except Exception as e:
            logger.warning(f"Failed to verify data: {e}")
            return False

    def clear_column_data(self, column_index: int) -> bool:
        """
        Clear all data in a specific column except the header.
        
        Args:
            column_index: Index of the column to clear
            
        Returns:
            bool: True if successful
        """
        try:
            # Get current sheet data to determine number of rows
            data = self.get_sheet_data()
            if not data or len(data) <= 1:
                return True
                
            num_rows = len(data)
            column_letter = chr(ord('A') + column_index)
            
            # Clear data from row 2 to the last row
            clear_range = f"{self.master_sheet_name}!{column_letter}2:{column_letter}{num_rows}"
            
            # Clear the range
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=clear_range
            ).execute()
            
            logger.info(f"Cleared data in column {column_letter} (index {column_index})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear column data: {e}")
            return False

    def update_daily_data(self, target_date: Optional[str] = None) -> bool:
        """
        Update the sheet with daily data for a specific date.
        Only updates the column for the specified date, leaving other dates untouched.
        
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
            
            # First, add any missing programs (only if we're updating today's data)
            today = date.today().isoformat()
            if target_date == today:
                added_programs = self.add_missing_programs(target_date)
                if added_programs > 0:
                    logger.info(f"Added {added_programs} missing programs before data update")
            
            # Check if date column exists, if not create it
            column_index = self.find_date_column(formatted_date)
            if column_index is None:
                column_index = self.add_date_column(formatted_date)
                if column_index is None:
                    logger.error("Failed to create date column")
                    return False
            
            # IMPORTANT: Clear only the specific column we're updating
            # This preserves manual data in other date columns
            logger.info(f"Clearing existing data in column for {formatted_date}")
            if not self.clear_column_data(column_index):
                logger.warning("Failed to clear column data, continuing anyway")
            
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
            
            # Get updated programs mapping (after adding missing programs)
            programs_mapping = self.get_programs_mapping()
            
            # Prepare updates ONLY for the specific column
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
                    logger.warning(f"Program still not found in sheet after adding missing programs: {program_key}")
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
            
            # Apply all updates in batch with retry logic and verification
            if updates:
                def perform_batch_update():
                    return self.service.spreadsheets().values().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body={
                            'valueInputOption': 'RAW',
                            'data': updates
                        }
                    ).execute()
                
                # Perform batch update with retry
                self._retry_with_backoff(
                    perform_batch_update,
                    f"Batch update for {formatted_date}",
                    max_retries=5
                )
                
                # Verify the data was actually written
                logger.info(f"Verifying data write for {formatted_date}...")
                verification_attempts = 0
                max_verification_attempts = 3
                
                while verification_attempts < max_verification_attempts:
                    # Wait a moment for Google Sheets to process the update
                    time.sleep(2)
                    
                    if self._verify_data_written(column_index, updated_count):
                        logger.info(f"✅ Successfully updated {updated_count} programs for {formatted_date} (column {column_index})")
                        return True
                    
                    verification_attempts += 1
                    if verification_attempts < max_verification_attempts:
                        logger.warning(f"Data verification failed, attempt {verification_attempts}/{max_verification_attempts}")
                        logger.info("Retrying batch update...")
                        
                        # Retry the batch update
                        self._retry_with_backoff(
                            perform_batch_update,
                            f"Retry batch update for {formatted_date}",
                            max_retries=3
                        )
                
                # If we get here, verification failed multiple times
                logger.error(f"❌ Data verification failed after {max_verification_attempts} attempts for {formatted_date}")
                logger.error("Data may not have been written correctly to Google Sheets")
                return False
                
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