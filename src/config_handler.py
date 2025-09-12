import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import logging

class ConfigHandler:
    """
    Handles all configuration loading and management
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        load_dotenv()
        
        # Adjust path for relative config directory
        if not os.path.isabs(config_dir):
            # If running from src/, go up one level to find config/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(base_dir, config_dir)
        
        # Load configuration files
        self.settings = self._load_json(f"{config_dir}/settings.json")
        self.check_dates_config = self._load_json(f"{config_dir}/check_dates.json")
        
        # Environment variables
        self.phone_number = os.getenv("PHONE_NUMBER")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Optional email settings
        self.email_smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.email_smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        # Browser settings with environment overrides
        self.headless = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"
        self.browser_timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))
        
        # Logging level
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Validate required settings
        self._validate_config()
    
    def _load_json(self, file_path: str) -> Dict:
        """Load JSON configuration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {file_path}")
            return {}
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in configuration file: {file_path}")
            return {}
    
    def _validate_config(self):
        """Validate that required configuration is present"""
        required_fields = {
            "phone_number": self.phone_number,
            "telegram_bot_token": self.telegram_bot_token,
            "telegram_chat_id": self.telegram_chat_id
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
    
    @property
    def academies(self) -> Dict[str, Dict[str, Any]]:
        """Get academy configuration"""
        return {
            "kotak": {
                "name": "Kotak Pullela Gopichand Badminton Academy",
                "url": "https://booking.gopichandacademy.com/venue-details/1",
                "id": 1
            },
            "pullela": {
                "name": "Pullela Gopichand Badminton Academy", 
                "url": "https://booking.gopichandacademy.com/venue-details/2",
                "id": 2
            },
            "sai": {
                "name": "SAI Gopichand Pullela Gopichand Badminton Academy",
                "url": "https://booking.gopichandacademy.com/venue-details/3", 
                "id": 3
            }
        }
    
    @property
    def dates_to_check(self) -> List[str]:
        """Get list of dates to check"""
        return self.check_dates_config.get("dates_to_check", [])
    
    @property
    def time_preferences(self) -> Dict[str, Any]:
        """Get time preferences"""
        return self.check_dates_config.get("time_preferences", {})
    
    @property
    def court_preferences(self) -> Dict[str, Any]:
        """Get court preferences"""
        return self.check_dates_config.get("court_preferences", {})
    
    @property
    def notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        return self.check_dates_config.get("notification_settings", {})
    
    @property
    def browser_settings(self) -> Dict[str, Any]:
        """Get browser settings with environment overrides"""
        browser_config = self.settings.get("browser_settings", {})
        browser_config["headless"] = self.headless
        browser_config["timeout"] = self.browser_timeout
        return browser_config
    
    @property
    def retry_settings(self) -> Dict[str, Any]:
        """Get retry settings"""
        return self.settings.get("retry_settings", {})
    
    @property
    def rate_limiting(self) -> Dict[str, Any]:
        """Get rate limiting settings"""
        return self.settings.get("rate_limiting", {})
    
    @property
    def urls(self) -> Dict[str, str]:
        """Get URL configuration"""
        return self.settings.get("urls", {})
    
    def get_academies_to_check(self) -> List[str]:
        """Get list of academies to check"""
        configured_academies = self.check_dates_config.get("academies_to_check", ["all"])
        
        if "all" in configured_academies:
            return list(self.academies.keys())
        
        return [academy for academy in configured_academies if academy in self.academies]
    
    def update_dates_to_check(self, new_dates: List[str]):
        """Update dates to check in configuration"""
        self.check_dates_config["dates_to_check"] = new_dates
        self._save_check_dates_config()
    
    def _save_check_dates_config(self):
        """Save check dates configuration to file"""
        try:
            with open(f"{self.config_dir}/check_dates.json", 'w', encoding='utf-8') as f:
                json.dump(self.check_dates_config, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving check dates configuration: {str(e)}")

# Configuration instance for easy import
config = None

def get_config() -> ConfigHandler:
    """Get global configuration instance"""
    global config
    if config is None:
        config = ConfigHandler()
    return config
