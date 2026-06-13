# modules/config_manager.py - COMPLETE VERSION FOR BUSINESS INSIDER
import json
import os
from typing import Dict, Any


class ConfigManager:
    # DEFAULT CONFIGURATION FOR BUSINESS INSIDER
    DEFAULT_SCRAPER_CONFIG = {
        "site_name": "Business Insider",
        "base_url": "https://www.businessinsider.com",
        "categories": {
            # Business
            "business": "https://www.businessinsider.com/business",
            "strategy": "https://www.businessinsider.com/strategy",
            "economy": "https://www.businessinsider.com/economy",
            "finance": "https://www.businessinsider.com/finance",
            "retail": "https://www.businessinsider.com/retail",
            "advertising": "https://www.businessinsider.com/advertising",
            "careers": "https://www.businessinsider.com/careers",
            "media": "https://www.businessinsider.com/media",
            "real-estate": "https://www.businessinsider.com/real-estate",
            "smallbusiness": "https://www.businessinsider.com/smallbusiness",
            "the-better-work-project": "https://sc.businessinsider.com/the-better-work-project",
            
            # Tech
            "tech": "https://www.businessinsider.com/tech",
            "science": "https://www.businessinsider.com/science",
            "artificial-intelligence": "https://www.businessinsider.com/artificial-intelligence",
            "enterprise": "https://www.businessinsider.com/enterprise",
            "transportation": "https://www.businessinsider.com/transportation",
            "startups": "https://www.businessinsider.com/startups",
            "innovation": "https://www.businessinsider.com/innovation",
            
            # Market
            "markets": "https://markets.businessinsider.com/",
            "stocks": "https://markets.businessinsider.com/stocks",
            "indices": "https://markets.businessinsider.com/indices",
            "commodities": "https://markets.businessinsider.com/commodities",
            
            # Lifestyle
            "lifestyle": "https://www.businessinsider.com/lifestyle",
            "entertainment": "https://www.businessinsider.com/entertainment",
            "culture": "https://www.businessinsider.com/culture",
            "travel": "https://www.businessinsider.com/travel",
            "food": "https://www.businessinsider.com/food",
            "health": "https://www.businessinsider.com/health",
            "parenting": "https://www.businessinsider.com/parenting",
            
            # Politics
            "politics": "https://www.businessinsider.com/politics",
            "defense": "https://www.businessinsider.com/defense",
            "law": "https://www.businessinsider.com/law",
            "education": "https://www.businessinsider.com/education"
        },
        "max_pages_per_category": 5,
        "default_threads": 6,
        "request_timeout": 20,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    DEFAULT_OUTREACH_CONFIG = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "email_address": "",
        "email_password": "",
        "google_creds_file": "data/google_credentials.json",
        "sheet_name": "business-insider-authors",
        "email_templates": {
            "default": {
                "subject": "Collaboration Opportunity - {author_name} from Business Insider",
                "body": """Dear {author_name},

I hope this message finds you well.

I've been following your excellent work on Business Insider, especially your articles on {topic}.
Your insights are particularly impressive and resonate with our audience.

I'm {your_name}, and I represent a team interested in high-quality content in your area of expertise.
We would be honored to explore a potential collaboration opportunity that could benefit both our audiences.

Would you be open to a brief conversation about potential partnership opportunities?

Looking forward to hearing your thoughts.

Best regards,
{your_name}
{your_position}
{company_name}"""
            },
            "business_insider_specific": {
                "subject": "Regarding your recent Business Insider article on {topic}",
                "body": """Hello {author_name},

I recently read your article on Business Insider about {topic} and found it very insightful.

As someone who follows business journalism closely, I appreciate the depth of your analysis.
Your perspective on this subject is particularly valuable.

I'm {your_name} from {company_name}, and we're looking to connect with skilled journalists like yourself.
We believe there could be interesting collaboration opportunities that align with your expertise.

Would you be interested in discussing this further?

Best regards,
{your_name}
{your_position}
{company_name}"""
            }
        },
        "sender_info": {
            "your_name": "Your Name",
            "your_position": "Content Outreach Manager",
            "company_name": "Your Company"
        },
        "ui_settings": {
            "theme": "light",
            "font_size": 10,
            "auto_save": True,
            "primary_color": "#E2001A",  # Business Insider red
            "secondary_color": "#263238"  # Dark gray
        }
    }
    
    @classmethod
    def load_scraper_config(cls) -> Dict[str, Any]:
        """Load scraper configuration for Business Insider"""
        config_file = "data/scraper_config.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Merge with defaults
                config = cls.DEFAULT_SCRAPER_CONFIG.copy()
                config.update(user_config)
                return config
        except Exception as e:
            print(f"Error loading scraper config: {e}")
        
        return cls.DEFAULT_SCRAPER_CONFIG.copy()
    
    @classmethod
    def load_outreach_config(cls) -> Dict[str, Any]:
        """Load outreach configuration from file"""
        config_file = "data/outreach_config.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Merge with defaults
                config = cls.DEFAULT_OUTREACH_CONFIG.copy()
                config.update(user_config)
                return config
        except Exception as e:
            print(f"Error loading outreach config: {e}")
        
        return cls.DEFAULT_OUTREACH_CONFIG.copy()
    
    @classmethod
    def save_scraper_config(cls, config: Dict[str, Any]) -> bool:
        """Save scraper configuration to file"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            with open("data/scraper_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving scraper config: {e}")
            return False
    
    @classmethod
    def save_outreach_config(cls, config: Dict[str, Any]) -> bool:
        """Save outreach configuration to file"""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            with open("data/outreach_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving outreach config: {e}")
            return False
    
    @classmethod
    def get_categories(cls) -> Dict[str, str]:
        """Get scraping categories for Business Insider"""
        config = cls.load_scraper_config()
        return config.get("categories", cls.DEFAULT_SCRAPER_CONFIG["categories"])
    
    @classmethod
    def get_category_url(cls, category: str) -> str:
        """Get URL for a specific category"""
        categories = cls.get_categories()
        return categories.get(category, "")
    
    @classmethod
    def save_email_template(cls, template_name: str, subject: str, body: str) -> bool:
        """Save custom email template"""
        try:
            config = cls.load_outreach_config()
            
            if "email_templates" not in config:
                config["email_templates"] = {}
            
            config["email_templates"][template_name] = {
                "subject": subject,
                "body": body
            }
            
            return cls.save_outreach_config(config)
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    @classmethod
    def get_email_template(cls, template_name: str = "default") -> Dict[str, str]:
        """Get email template by name"""
        config = cls.load_outreach_config()
        templates = config.get("email_templates", {})
        
        if template_name in templates:
            return templates[template_name]
        elif "default" in templates:
            return templates["default"]
        else:
            return cls.DEFAULT_OUTREACH_CONFIG["email_templates"]["default"]
    
    @classmethod
    def get_google_creds_path(cls) -> str:
        """Get Google credentials file path"""
        config = cls.load_outreach_config()
        return config.get("google_creds_file", "data/google_credentials.json")
    
    @classmethod
    def get_sheet_name(cls) -> str:
        """Get Google Sheet name"""
        config = cls.load_outreach_config()
        return config.get("sheet_name", "business-insider-authors")
    
    @classmethod
    def update_sender_info(cls, name: str, position: str, company: str) -> bool:
        """Update sender information"""
        try:
            config = cls.load_outreach_config()
            
            if "sender_info" not in config:
                config["sender_info"] = {}
            
            config["sender_info"]["your_name"] = name
            config["sender_info"]["your_position"] = position
            config["sender_info"]["company_name"] = company
            
            return cls.save_outreach_config(config)
        except Exception as e:
            print(f"Error updating sender info: {e}")
            return False
    
    @classmethod
    def update_smtp_settings(cls, server: str, port: int, email: str, password: str) -> bool:
        """Update SMTP settings"""
        try:
            config = cls.load_outreach_config()
            
            config["smtp_server"] = server
            config["smtp_port"] = port
            config["email_address"] = email
            config["email_password"] = password
            
            return cls.save_outreach_config(config)
        except Exception as e:
            print(f"Error updating SMTP settings: {e}")
            return False
    
    @classmethod
    def create_default_configs(cls):
        """Create default configuration files if they don't exist"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Create scraper config if it doesn't exist
            scraper_config_file = "data/scraper_config.json"
            if not os.path.exists(scraper_config_file):
                with open(scraper_config_file, 'w', encoding='utf-8') as f:
                    json.dump(cls.DEFAULT_SCRAPER_CONFIG, f, indent=4, ensure_ascii=False)
            
            # Create outreach config if it doesn't exist
            outreach_config_file = "data/outreach_config.json"
            if not os.path.exists(outreach_config_file):
                with open(outreach_config_file, 'w', encoding='utf-8') as f:
                    json.dump(cls.DEFAULT_OUTREACH_CONFIG, f, indent=4, ensure_ascii=False)
            
            # Create empty Google credentials file if it doesn't exist
            google_creds_file = "data/google_credentials.json"
            if not os.path.exists(google_creds_file):
                with open(google_creds_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error creating default configs: {e}")
            return False


# Create default configs when module is imported
ConfigManager.create_default_configs()
