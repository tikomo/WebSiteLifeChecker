"""
Configuration Manager for Health Monitor application.
Handles loading and validation of configuration files.
"""
import json
import os
from typing import List, Dict, Any
from urllib.parse import urlparse

from ..models.data_models import WebsiteTarget, DatabaseTarget


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class ConfigurationManager:
    """Manages configuration files for the Health Monitor application."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the Configuration Manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self.websites_file = os.path.join(config_dir, "websites.json")
        self.databases_file = os.path.join(config_dir, "databases.json")
    
    def load_website_config(self) -> List[WebsiteTarget]:
        """
        Load website configuration from JSON file.
        
        Returns:
            List of WebsiteTarget objects
            
        Raises:
            ConfigurationError: If configuration file is invalid or missing
        """
        try:
            if not os.path.exists(self.websites_file):
                raise ConfigurationError(f"Website configuration file not found: {self.websites_file}")
            
            with open(self.websites_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if not self.validate_website_config(config_data):
                raise ConfigurationError("Invalid website configuration format")
            
            websites = []
            for site_config in config_data.get("websites", []):
                website = WebsiteTarget(
                    name=site_config["name"],
                    url=site_config["url"],
                    timeout=site_config.get("timeout", 10),
                    expected_status=site_config.get("expected_status", 200)
                )
                websites.append(website)
            
            return websites
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in website configuration: {e}")
        except KeyError as e:
            raise ConfigurationError(f"Missing required field in website configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading website configuration: {e}")
    
    def load_database_config(self) -> List[DatabaseTarget]:
        """
        Load database configuration from JSON file.
        
        Returns:
            List of DatabaseTarget objects
            
        Raises:
            ConfigurationError: If configuration file is invalid or missing
        """
        try:
            if not os.path.exists(self.databases_file):
                raise ConfigurationError(f"Database configuration file not found: {self.databases_file}")
            
            with open(self.databases_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if not self.validate_database_config(config_data):
                raise ConfigurationError("Invalid database configuration format")
            
            databases = []
            for db_config in config_data.get("databases", []):
                database = DatabaseTarget(
                    name=db_config["name"],
                    host=db_config["host"],
                    port=db_config["port"],
                    database=db_config["database"],
                    username=db_config["username"],
                    password=db_config["password"],
                    sslmode=db_config.get("sslmode", "prefer")
                )
                databases.append(database)
            
            return databases
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in database configuration: {e}")
        except KeyError as e:
            raise ConfigurationError(f"Missing required field in database configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading database configuration: {e}")
    
    def validate_website_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate website configuration structure and content.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        if not isinstance(config, dict):
            return False
        
        if "websites" not in config:
            return False
        
        websites = config["websites"]
        if not isinstance(websites, list):
            return False
        
        for site in websites:
            if not isinstance(site, dict):
                return False
            
            # Check required fields
            required_fields = ["name", "url"]
            for field in required_fields:
                if field not in site or not isinstance(site[field], str) or not site[field].strip():
                    return False
            
            # Validate URL format
            if not self._is_valid_url(site["url"]):
                return False
            
            # Validate optional fields
            if "timeout" in site:
                if not isinstance(site["timeout"], int) or site["timeout"] <= 0:
                    return False
            
            if "expected_status" in site:
                if not isinstance(site["expected_status"], int) or not (100 <= site["expected_status"] <= 599):
                    return False
        
        return True
    
    def validate_database_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate database configuration structure and content.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        if not isinstance(config, dict):
            return False
        
        if "databases" not in config:
            return False
        
        databases = config["databases"]
        if not isinstance(databases, list):
            return False
        
        for db in databases:
            if not isinstance(db, dict):
                return False
            
            # Check required fields
            required_fields = ["name", "host", "port", "database", "username", "password"]
            for field in required_fields:
                if field not in db:
                    return False
                
                if field == "port":
                    if not isinstance(db[field], int) or not (1 <= db[field] <= 65535):
                        return False
                else:
                    if not isinstance(db[field], str) or not db[field].strip():
                        return False
            
            # Validate optional sslmode field
            if "sslmode" in db:
                valid_ssl_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
                if db["sslmode"] not in valid_ssl_modes:
                    return False
        
        return True
    
    def reload_config(self) -> None:
        """
        Reload configuration files.
        This method can be extended to support hot-reloading functionality.
        """
        # For now, this is a placeholder that could trigger re-loading
        # In a full implementation, this might notify other components
        pass
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False