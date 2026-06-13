# modules/config_manager.py - CNET CONFIGURATION

import json
import os
from datetime import datetime

class ConfigManager:
    """Configuration manager for CNET scraper"""
    
    # Default CNET configuration
    DEFAULT_CONFIG = {
        "site_name": "CNET",
        "base_url": "https://www.cnet.com",
        "categories": {
            "ai-atlas": "https://www.cnet.com/ai-atlas/",
            "tech": "https://www.cnet.com/tech/",
            "home": "https://www.cnet.com/home/",
            "entertainment": "https://www.cnet.com/culture/entertainment/",
            "health": "https://www.cnet.com/health/"
        },
        "max_pages_per_category": 5,
        "default_threads": 10,
        "request_timeout": 15,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "email_extraction_enabled": True,
        "batch_size": 50,
        "use_author_slug_normalization": False,  # CNET uses different URL structure
        "pagination_pattern": "https://www.cnet.com/news/{page}/",
        "article_selectors": {
            "article_link": "a.c-storiesNeonLatest_story",
            "author_name": '[data-cy="authorName"]',
            "author_profile": 'a[rel="author"]',
            "social_links": ".c-socialSharebar_container a"
        },
        "output_format": {
            "author_fields": [
                "Author Name",
                "Profile URL",
                "Twitter",
                "Facebook",
                "Email",
                "Article Count",
                "Publication Name"
            ],
            "article_fields": [
                "link",
                "category",
                "scraped_at"
            ]
        }
    }
    
    @classmethod
    def load_config(cls, config_path="data/site_config.json"):
        """Load configuration from file or return default"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = cls.DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
            else:
                # Save default config if it doesn't exist
                cls.save_config(cls.DEFAULT_CONFIG, config_path)
                return cls.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def save_config(cls, config, config_path="data/site_config.json"):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    @classmethod
    def get_categories(cls):
        """Get all category URLs"""
        config = cls.load_config()
        return config.get("categories", {})
    
    @classmethod
    def get_category_url(cls, category_name):
        """Get URL for a specific category"""
        categories = cls.get_categories()
        return categories.get(category_name)
    
    @classmethod
    def get_site_name(cls):
        """Get site name"""
        config = cls.load_config()
        return config.get("site_name", "CNET")
    
    @classmethod
    def get_base_url(cls):
        """Get base URL"""
        config = cls.load_config()
        return config.get("base_url", "https://www.cnet.com")
    
    @classmethod
    def get_max_pages(cls):
        """Get max pages per category"""
        config = cls.load_config()
        return config.get("max_pages_per_category", 5)
    
    @classmethod
    def get_default_threads(cls):
        """Get default thread count"""
        config = cls.load_config()
        return config.get("default_threads", 10)
    
    @classmethod
    def get_request_timeout(cls):
        """Get request timeout"""
        config = cls.load_config()
        return config.get("request_timeout", 15)
    
    @classmethod
    def get_user_agent(cls):
        """Get user agent"""
        config = cls.load_config()
        return config.get("user_agent", cls.DEFAULT_CONFIG["user_agent"])
    
    @classmethod
    def is_email_extraction_enabled(cls):
        """Check if email extraction is enabled"""
        config = cls.load_config()
        return config.get("email_extraction_enabled", True)
    
    @classmethod
    def get_batch_size(cls):
        """Get batch size for processing"""
        config = cls.load_config()
        return config.get("batch_size", 50)
    
    @classmethod
    def get_article_selectors(cls):
        """Get article selectors"""
        config = cls.load_config()
        return config.get("article_selectors", cls.DEFAULT_CONFIG["article_selectors"])
    
    @classmethod
    def get_output_fields(cls):
        """Get output fields configuration"""
        config = cls.load_config()
        return config.get("output_format", cls.DEFAULT_CONFIG["output_format"])
    
    @classmethod
    def get_pagination_pattern(cls):
        """Get pagination URL pattern"""
        config = cls.load_config()
        return config.get("pagination_pattern", "https://www.cnet.com/news/{page}/")
    
    @classmethod
    def load_scraper_config(cls):
        """Load scraper configuration (compatibility with existing code)"""
        return cls.load_config()
    
    @classmethod
    def create_default_cnet_config(cls, save=True):
        """Create and optionally save default CNET configuration"""
        config = {
            "site_name": "CNET",
            "base_url": "https://www.cnet.com",
            "categories": {
                "ai-atlas": "https://www.cnet.com/ai-atlas/",
                "tech": "https://www.cnet.com/tech/",
                "home": "https://www.cnet.com/home/",
                "entertainment": "https://www.cnet.com/culture/entertainment/",
                "health": "https://www.cnet.com/health/"
            },
            "max_pages_per_category": 5,
            "default_threads": 10,
            "request_timeout": 15,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "email_extraction_enabled": True,
            "batch_size": 50,
            "use_author_slug_normalization": False,
            "pagination_pattern": "https://www.cnet.com/news/{page}/",
            "article_selectors": {
                "article_link": "a.c-storiesNeonLatest_story",
                "author_name": '[data-cy="authorName"]',
                "author_profile": 'a[rel="author"]',
                "social_links": ".c-socialSharebar_container a"
            },
            "output_format": {
                "author_fields": [
                    "Author Name",
                    "Profile URL",
                    "Twitter",
                    "Facebook",
                    "Email",
                    "Article Count",
                    "Publication Name"
                ],
                "article_fields": [
                    "link",
                    "category",
                    "scraped_at"
                ]
            },
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        if save:
            cls.save_config(config)
        
        return config


# For backward compatibility with existing code
def load_scraper_config():
    """Backward compatibility function"""
    return ConfigManager.load_scraper_config()


def get_categories():
    """Backward compatibility function"""
    return ConfigManager.get_categories()


# If run directly, create default config
if __name__ == "__main__":
    config = ConfigManager.create_default_cnet_config(save=True)
    print(f"✅ Default CNET configuration created at data/site_config.json")
    print(f"Site: {config['site_name']}")
    print(f"Categories: {list(config['categories'].keys())}")
