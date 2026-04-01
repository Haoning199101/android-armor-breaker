#!/usr/bin/env python3
"""
I18n Logger for Android Armor Breaker
Provides internationalized logging functionality for all skill scripts
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any

class I18nLogger:
    """Internationalized logger with support for multiple languages"""
    
    # Supported languages
    SUPPORTED_LANGUAGES = ['en-US', 'zh-CN']
    
    def __init__(self, language: str = 'en-US', verbose: bool = True, module: str = 'common'):
        """
        Initialize the I18nLogger
        
        Args:
            language: Language code (e.g., 'en-US', 'zh-CN')
            verbose: Whether to enable verbose logging
            module: Default module for message lookup
        """
        self.language = language if language in self.SUPPORTED_LANGUAGES else 'en-US'
        self.verbose = verbose
        self.default_module = module
        self.messages = self._load_messages()
        
        # Log prefixes
        self.prefixes = {
            "INFO": "📝",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }
    
    def _load_messages(self) -> Dict[str, Dict[str, str]]:
        """Load messages from language resource files"""
        messages = {}
        
        # Get the i18n directory
        script_dir = Path(__file__).parent
        i18n_dir = script_dir / 'i18n'
        
        # Load the language file
        lang_file = i18n_dir / f'{self.language}.json'
        
        if not lang_file.exists():
            # Fallback to English if language file not found
            lang_file = i18n_dir / 'en-US.json'
            if not lang_file.exists():
                # Create a minimal default messages dict
                return {'common': {}}
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load language file {lang_file}: {e}")
            messages = {'common': {}}
        
        return messages
    
    def get_message(self, key: str, module: Optional[str] = None, **kwargs) -> str:
        """
        Get a translated message
        
        Args:
            key: Message key
            module: Module name (e.g., 'root_memory_extractor')
            **kwargs: Formatting parameters
            
        Returns:
            Formatted message string
        """
        module_name = module or self.default_module
        
        # Try to get message from specified module
        if module_name in self.messages and key in self.messages[module_name]:
            template = self.messages[module_name][key]
        # Fallback to common module
        elif 'common' in self.messages and key in self.messages['common']:
            template = self.messages['common'][key]
        # Fallback to key itself
        else:
            template = key
        
        # Format the template with kwargs
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # If formatting fails, return template with error info
            return f"{template} [Format error: missing {e}]"
    
    def log(self, key: str, level: str = "INFO", module: Optional[str] = None, **kwargs):
        """
        Log a message with internationalization support
        
        Args:
            key: Message key
            level: Log level (INFO, SUCCESS, WARNING, ERROR, DEBUG)
            module: Module name for message lookup
            **kwargs: Formatting parameters for the message
        """
        # Skip DEBUG logs if not verbose
        if level == "DEBUG" and not self.verbose:
            return
        
        # Get the message
        message = self.get_message(key, module, **kwargs)
        
        # Get timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Get prefix
        prefix = self.prefixes.get(level, "📝")
        
        # Print the log
        print(f"{prefix} [{timestamp}] {message}")
    
    # Convenience methods
    def info(self, key: str, **kwargs):
        """Log an info message"""
        self.log(key, "INFO", **kwargs)
    
    def success(self, key: str, **kwargs):
        """Log a success message"""
        self.log(key, "SUCCESS", **kwargs)
    
    def warning(self, key: str, **kwargs):
        """Log a warning message"""
        self.log(key, "WARNING", **kwargs)
    
    def error(self, key: str, **kwargs):
        """Log an error message"""
        self.log(key, "ERROR", **kwargs)
    
    def debug(self, key: str, **kwargs):
        """Log a debug message"""
        self.log(key, "DEBUG", **kwargs)
    
    def set_language(self, language: str):
        """Change the language at runtime"""
        if language in self.SUPPORTED_LANGUAGES:
            self.language = language
            self.messages = self._load_messages()
        else:
            self.warning("unsupported_language", language=language, supported=", ".join(self.SUPPORTED_LANGUAGES))


# Global logger instance for easy import
_default_logger = None

def get_logger(language: str = 'en-US', verbose: bool = True, module: str = 'common') -> I18nLogger:
    """
    Get a logger instance (singleton pattern)
    
    Args:
        language: Language code
        verbose: Verbose mode
        module: Default module
        
    Returns:
        I18nLogger instance
    """
    global _default_logger
    
    # Check environment variable for language preference
    env_language = os.environ.get('ANDROID_ARMOR_BREAKER_LANG', language)
    
    if _default_logger is None:
        _default_logger = I18nLogger(language=env_language, verbose=verbose, module=module)
    elif _default_logger.language != env_language or _default_logger.verbose != verbose:
        # Update existing logger if parameters changed
        _default_logger.language = env_language if env_language in I18nLogger.SUPPORTED_LANGUAGES else 'en-US'
        _default_logger.verbose = verbose
        _default_logger.messages = _default_logger._load_messages()
    
    return _default_logger


# Test function
def test_i18n_logger():
    """Test the I18nLogger functionality"""
    print("Testing I18nLogger...")
    
    # Test English logger
    logger_en = I18nLogger(language='en-US', verbose=True)
    logger_en.info("checking_root")
    logger_en.success("device_has_root")
    logger_en.error("no_root_permission", error="su not found")
    logger_en.info("starting_app")
    
    print("\n" + "="*50 + "\n")
    
    # Test Chinese logger
    logger_zh = I18nLogger(language='zh-CN', verbose=True)
    logger_zh.info("checking_root")
    logger_zh.success("device_has_root")
    logger_zh.error("no_root_permission", error="su not found")
    logger_zh.info("starting_app")
    
    print("\n" + "="*50 + "\n")
    
    # Test module-specific messages
    logger_module = I18nLogger(language='en-US', verbose=True, module='root_memory_extractor')
    logger_module.info("extraction_start")
    logger_module.info("target_app", package="com.example.app")
    logger_module.info("extracting_memory", region_num=1, total_regions=10, start=0x1000, end=0x2000, size_mb=4.0)
    
    print("\n✅ I18nLogger test completed successfully!")


if __name__ == '__main__':
    test_i18n_logger()