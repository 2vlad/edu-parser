"""Scraper registry for automatic discovery and registration of scrapers."""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Callable, Tuple
import pkgutil

from .logging_config import get_logger
from .storage import Storage


logger = get_logger(__name__)


class ScraperRegistry:
    """
    Automatic scraper registry.
    
    Discovers scraper functions from modules and matches them with database configs.
    New scraper = new function + entry in scrapers_config table.
    """
    
    def __init__(self, storage: Storage = None):
        """Initialize registry with storage for config lookup."""
        self.storage = storage or Storage()
        self.scrapers = {}  # scraper_id -> (function, config)
        
        logger.info("ScraperRegistry initialized")
    
    def discover_scrapers(self, package_name: str = "scrapers") -> int:
        """
        Auto-discover scraper functions from scrapers package using get_scrapers() pattern.
        
        Args:
            package_name: Name of package to scan for scrapers
            
        Returns:
            Number of scrapers discovered
        """
        logger.info(f"Discovering scrapers in package: {package_name}")
        
        try:
            # Import the scrapers package
            scrapers_package = importlib.import_module(package_name)
            scrapers_path = scrapers_package.__path__[0]
            
            discovered = 0
            
            # Scan all modules in scrapers package
            for importer, modname, ispkg in pkgutil.iter_modules([scrapers_path]):
                if ispkg:
                    continue
                    
                full_module_name = f"{package_name}.{modname}"
                logger.debug(f"Scanning module: {full_module_name}")
                
                try:
                    module = importlib.import_module(full_module_name)
                    
                    # Look for get_scrapers() function
                    if hasattr(module, 'get_scrapers') and callable(getattr(module, 'get_scrapers')):
                        logger.debug(f"Found get_scrapers() in {full_module_name}")
                        
                        # Call get_scrapers() to get configured scrapers
                        scrapers_list = module.get_scrapers()
                        
                        # Register each scraper from the list
                        for scraper_func, config in scrapers_list:
                            scraper_id = config.get('scraper_id')
                            if scraper_id:
                                self.scrapers[scraper_id] = {
                                    'function': scraper_func,
                                    'module': modname,
                                    'config': config
                                }
                                discovered += 1
                                logger.debug(f"Discovered scraper: {scraper_id} from {modname}")
                        
                        logger.info(f"Loaded {len(scrapers_list)} scrapers from {modname}")
                    else:
                        logger.debug(f"No get_scrapers() function found in {full_module_name}")
                
                except Exception as e:
                    logger.error(f"Error importing module {full_module_name}: {e}")
            
            logger.info(f"Discovered {discovered} scraper functions")
            return discovered
            
        except Exception as e:
            logger.error(f"Error discovering scrapers: {e}")
            return 0
    
    def _is_scraper_function(self, name: str, func: Callable) -> bool:
        """Check if function looks like a scraper."""
        # Look for scraper naming patterns
        scraper_patterns = ['scrape_', 'get_', 'fetch_']
        return any(name.startswith(pattern) for pattern in scraper_patterns)
    
    def _extract_scraper_id(self, func_name: str, module_name: str) -> str:
        """Extract scraper_id from function name and module."""
        # Remove scrape_ prefix if present
        if func_name.startswith('scrape_'):
            base_name = func_name[7:]  # Remove 'scrape_'
        else:
            base_name = func_name
        
        # Construct scraper_id: university_program
        return f"{module_name}_{base_name}"
    
    def load_enabled_scrapers(self) -> List[Tuple[Callable, Dict]]:
        """
        Load scrapers that are enabled in database.
        
        Returns:
            List of (scraper_function, config_dict) tuples ready to run
        """
        logger.info("Loading enabled scrapers from database...")
        
        # Get enabled configs from database
        enabled_configs = self.storage.get_enabled_scrapers()
        
        if not enabled_configs:
            logger.warning("No enabled scrapers found in database")
            return []
        
        # Match discovered functions with enabled configs
        ready_scrapers = []
        
        for config in enabled_configs:
            scraper_id = config['scraper_id']
            
            if scraper_id in self.scrapers:
                scraper_info = self.scrapers[scraper_id]
                # Use the merged config (database config takes precedence)
                merged_config = {**scraper_info.get('config', {}), **config}
                ready_scrapers.append((scraper_info['function'], merged_config))
                logger.debug(f"Matched scraper: {scraper_id}")
            else:
                logger.warning(f"Scraper function not found for enabled config: {scraper_id}")
        
        logger.info(f"Loaded {len(ready_scrapers)} enabled scrapers")
        return ready_scrapers
    
    def get_all_discovered_scrapers(self) -> List[Tuple[Callable, Dict]]:
        """
        Get all discovered scrapers regardless of database config.
        
        Returns:
            List of (scraper_function, config_dict) tuples for all discovered scrapers
        """
        logger.info("Getting all discovered scrapers...")
        
        all_scrapers = []
        for scraper_id, scraper_info in self.scrapers.items():
            all_scrapers.append((scraper_info['function'], scraper_info['config']))
        
        logger.info(f"Returning {len(all_scrapers)} discovered scrapers")
        return all_scrapers
    
    def register_scraper(self, scraper_id: str, scraper_func: Callable, 
                        name: str, enabled: bool = True) -> bool:
        """
        Manually register a scraper function.
        
        Args:
            scraper_id: Unique identifier
            scraper_func: Scraper function
            name: Human-readable name
            enabled: Whether scraper should be enabled
            
        Returns:
            True if registration successful
        """
        try:
            # Add to local registry
            self.scrapers[scraper_id] = {
                'function': scraper_func,
                'module': 'manual',
                'function_name': scraper_func.__name__
            }
            
            # Add to database if not exists
            existing = self.storage.get_scraper_by_id(scraper_id)
            if not existing:
                # Insert into scrapers_config table
                # Note: This would require adding an insert method to Storage
                logger.info(f"Would insert new scraper config: {scraper_id}")
                
            logger.info(f"Manually registered scraper: {scraper_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register scraper {scraper_id}: {e}")
            return False
    
    def get_scraper_info(self) -> Dict:
        """Get information about all registered scrapers."""
        enabled_configs = self.storage.get_enabled_scrapers()
        enabled_ids = {config['scraper_id'] for config in enabled_configs}
        
        info = {
            'total_discovered': len(self.scrapers),
            'total_enabled': len(enabled_configs),
            'matched': 0,
            'unmatched_functions': [],
            'unmatched_configs': []
        }
        
        # Check matches
        for scraper_id in self.scrapers:
            if scraper_id in enabled_ids:
                info['matched'] += 1
            else:
                info['unmatched_functions'].append(scraper_id)
        
        for config in enabled_configs:
            scraper_id = config['scraper_id']
            if scraper_id not in self.scrapers:
                info['unmatched_configs'].append(scraper_id)
        
        return info


# Convenience functions for easy usage

def get_ready_scrapers() -> List[Tuple[Callable, Dict]]:
    """
    Get all ready-to-run scrapers in one function call.
    
    Returns:
        List of (scraper_function, config) tuples for enabled scrapers
    """
    registry = ScraperRegistry()
    registry.discover_scrapers()
    return registry.load_enabled_scrapers()


def get_all_scrapers() -> List[Tuple[Callable, Dict]]:
    """
    Get all discovered scrapers regardless of database config.
    
    Returns:
        List of (scraper_function, config) tuples for all discovered scrapers
    """
    registry = ScraperRegistry()
    registry.discover_scrapers()
    return registry.get_all_discovered_scrapers()


def get_scraper_summary() -> Dict:
    """Get summary of scraper discovery and matching."""
    registry = ScraperRegistry()
    registry.discover_scrapers()
    return registry.get_scraper_info()