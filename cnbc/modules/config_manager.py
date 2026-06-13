# modules/config_manager.py - UPDATED FOR CNBC
import json
import os
from typing import Dict, Any


class ConfigManager:
    # DEFAULT CONFIGURATION FOR CNBC
    DEFAULT_SCRAPER_CONFIG = {
        "site_name": "CNBC",
        "base_url": "https://www.cnbc.com",
        "categories": {
            # Technology
            "technology": "https://www.cnbc.com/technology/",
            "cybersecurity": "https://www.cnbc.com/cybersecurity/",
            "ai-artificial-intelligence": "https://www.cnbc.com/ai-artificial-intelligence/",
            "enterprise": "https://www.cnbc.com/enterprise/",
            "internet": "https://www.cnbc.com/internet/",
            "media": "https://www.cnbc.com/media/",
            "mobile": "https://www.cnbc.com/mobile/",
            "social-media": "https://www.cnbc.com/social-media/",
            "cnbc-disruptors": "https://www.cnbc.com/cnbc-disruptors/",
            "tech-guide": "https://www.cnbc.com/tech-guide/",
            
            # Investing
            "investing": "https://www.cnbc.com/investing/",
            "personal-finance": "https://www.cnbc.com/personal-finance/",
            "fintech": "https://www.cnbc.com/fintech/",
            "financial-advisors": "https://www.cnbc.com/financial-advisors/",
            "options-action": "https://www.cnbc.com/options-action/",
            "etf-street": "https://www.cnbc.com/etf-street/",
            "earnings": "https://www.cnbc.com/earnings/",
            "trader-talk": "https://www.cnbc.com/trader-talk/",
            
            # Business
            "business": "https://www.cnbc.com/business/",
            "economy": "https://www.cnbc.com/economy/",
            "finance": "https://www.cnbc.com/finance/",
            "health-and-science": "https://www.cnbc.com/health-and-science/",
            "real-estate": "https://www.cnbc.com/real-estate/",
            "energy": "https://www.cnbc.com/energy/",
            "climate": "https://www.cnbc.com/climate/",
            "transportation": "https://www.cnbc.com/transportation/",
            "cnbc-investigations": "https://www.cnbc.com/cnbc-investigations/",
            "industrials": "https://www.cnbc.com/industrials/",
            "retail": "https://www.cnbc.com/retail/",
            "wealth": "https://www.cnbc.com/wealth/",
            "sports": "https://www.cnbc.com/sports/",
            "life": "https://www.cnbc.com/life/",
            
            # Markets
            "markets": "https://www.cnbc.com/markets/",
            "pre-markets": "https://www.cnbc.com/pre-markets/",
            "us-markets": "https://www.cnbc.com/us-markets/",
            "markets-europe": "https://www.cnbc.com/markets-europe/",
            "china-markets": "https://www.cnbc.com/china-markets/",
            "markets-asia-pacific": "https://www.cnbc.com/markets-asia-pacific/",
            "world-markets": "https://www.cnbc.com/world-markets/",
            "currencies": "https://www.cnbc.com/currencies/",
            "prediction-markets": "https://www.cnbc.com/prediction-markets/",
            "cryptocurrency": "https://www.cnbc.com/cryptocurrency/",
            "futures-and-commodities": "https://www.cnbc.com/futures-and-commodities/",
            "bonds": "https://www.cnbc.com/bonds/",
            "funds-and-etfs": "https://www.cnbc.com/funds-and-etfs/",
            
            # Politics
            "politics": "https://www.cnbc.com/politics/",
            "white-house": "https://www.cnbc.com/white-house/",
            "policy": "https://www.cnbc.com/policy/",
            "defense": "https://www.cnbc.com/defense/",
            "congress": "https://www.cnbc.com/congress/",
            "expanding-opportunity": "https://www.cnbc.com/expanding-opportunity/",
            "europe-politics": "https://www.cnbc.com/europe-politics/",
            "china-politics": "https://www.cnbc.com/china-politics/",
            "asia-politics": "https://www.cnbc.com/asia-politics/",
            "world-politics": "https://www.cnbc.com/world-politics/"
        },
        "max_pages_per_category": 5,
        "default_threads": 8,  # Increased for CNBC's larger site
        "request_timeout": 20,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "email_extraction_enabled": True,  # CNBC email extraction is enabled
        "batch_size": 40  # Optimized for CNBC scraping
    }
    
    DEFAULT_OUTREACH_CONFIG = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "email_address": "",
        "email_password": "",
        "google_creds_file": "data/google_credentials.json",
        "sheet_name": "cnbc-authors",  # Changed from business-insider-authors
        "email_templates": {
            "default": {
                "subject": "Collaboration Opportunity - {author_name} from CNBC",
                "body": """Dear {author_name},

I hope this message finds you well.

I've been following your excellent reporting on CNBC, especially your coverage of {topic}.
Your insights into market trends and financial analysis are particularly valuable.

I'm {your_name}, and I represent a team interested in high-quality financial and business content.
Given your expertise in this field, we believe there could be interesting collaboration opportunities that would benefit both our audiences.

Would you be open to a brief conversation about potential partnership opportunities?

Looking forward to hearing your thoughts.

Best regards,
{your_name}
{your_position}
{company_name}"""
            },
            "cnbc_specific": {
                "subject": "Regarding your recent CNBC coverage of {topic}",
                "body": """Hello {author_name},

I recently read your article on CNBC about {topic} and found your analysis to be very insightful.
As someone who closely follows financial and business news, I appreciate the depth and clarity of your reporting.

I'm {your_name} from {company_name}, and we're looking to connect with skilled financial journalists like yourself.
We believe there could be valuable collaboration opportunities that align with your expertise in this sector.

Would you be interested in discussing this further?

Best regards,
{your_name}
{your_position}
{company_name}"""
            },
            "market_analysis": {
                "subject": "Discussion about your market analysis on CNBC",
                "body": """Dear {author_name},

Your market analysis and financial reporting on CNBC consistently provide valuable insights.
I particularly appreciated your recent piece on {topic} - it offered a nuanced perspective that's often missing in financial journalism.

I'm {your_name}, working with {company_name} where we focus on {your_industry}.
We're always looking to collaborate with knowledgeable financial journalists who understand market dynamics as well as you do.

Would you be open to exploring potential collaboration opportunities?

Sincerely,
{your_name}
{your_position}
{company_name}"""
            },
            "quick_intro": {
                "subject": "Introduction from an admirer of your CNBC work",
                "body": """Hi {author_name},

I'm {your_name} from {company_name}. I regularly follow CNBC and have been impressed with your reporting on {topic}.

Your ability to break down complex financial concepts is remarkable, and it's clear you have a deep understanding of the markets.

I'd love to connect and explore if there might be opportunities for collaboration or knowledge sharing.

Best,
{your_name}
{your_position}
{company_name}"""
            }
        },
        "sender_info": {
            "your_name": "Your Name",
            "your_position": "Business Development Manager",
            "company_name": "Your Company",
            "your_industry": "financial services"  # Added for CNBC context
        },
        "ui_settings": {
            "theme": "light",
            "font_size": 10,
            "auto_save": True,
            "primary_color": "#005594",  # CNBC Blue
            "secondary_color": "#00a8e8",  # CNBC Light Blue
            "accent_color": "#1c1c1c"  # CNBC Dark
        },
        "email_customization": {
            "include_article_reference": True,
            "personalization_level": "high",  # low, medium, high
            "follow_up_days": 7,
            "max_emails_per_day": 50
        }
    }
    
    @classmethod
    def load_scraper_config(cls) -> Dict[str, Any]:
        """Load scraper configuration for CNBC"""
        config_file = "data/scraper_config.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Merge with defaults (preserve CNBC categories if not in user config)
                config = cls.DEFAULT_SCRAPER_CONFIG.copy()
                
                # Special handling for categories - merge rather than replace
                if "categories" in user_config:
                    # Update existing categories, add new ones
                    config["categories"].update(user_config["categories"])
                    # Remove categories from user config to avoid duplication
                    del user_config["categories"]
                
                # Update remaining config
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
                
                # Special handling for email_templates - merge templates
                if "email_templates" in user_config:
                    # Update existing templates, add new ones
                    config["email_templates"].update(user_config["email_templates"])
                    del user_config["email_templates"]
                
                # Update remaining config
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
        """Get scraping categories for CNBC"""
        config = cls.load_scraper_config()
        return config.get("categories", cls.DEFAULT_SCRAPER_CONFIG["categories"])
    
    @classmethod
    def get_category_url(cls, category: str) -> str:
        """Get URL for a specific category"""
        categories = cls.get_categories()
        return categories.get(category, "")
    
    @classmethod
    def get_categories_by_group(cls) -> Dict[str, list]:
        """Get categories organized by main groups (for UI display)"""
        categories = cls.get_categories()
        
        # Group categories based on URL patterns
        groups = {
            "Technology": [],
            "Investing": [],
            "Business": [],
            "Markets": [],
            "Politics": []
        }
        
        # Define URL patterns for each group
        tech_patterns = ["/technology", "/cybersecurity", "/ai", "/enterprise", "/internet", "/mobile", "/social-media"]
        investing_patterns = ["/investing", "/personal-finance", "/fintech", "/financial-advisors", "/options", "/etf", "/earnings", "/trader"]
        business_patterns = ["/business", "/economy", "/finance", "/health", "/real-estate", "/energy", "/climate", "/transportation", "/industrials", "/retail"]
        markets_patterns = ["/markets", "/us-markets", "/world-markets", "/china-markets", "/currencies", "/cryptocurrency", "/futures", "/bonds", "/etfs"]
        politics_patterns = ["/politics", "/white-house", "/policy", "/defense", "/congress", "/europe-politics", "/china-politics"]
        
        for cat_name, cat_url in categories.items():
            url_lower = cat_url.lower()
            
            if any(pattern in url_lower for pattern in tech_patterns):
                groups["Technology"].append(cat_name)
            elif any(pattern in url_lower for pattern in investing_patterns):
                groups["Investing"].append(cat_name)
            elif any(pattern in url_lower for pattern in business_patterns):
                groups["Business"].append(cat_name)
            elif any(pattern in url_lower for pattern in markets_patterns):
                groups["Markets"].append(cat_name)
            elif any(pattern in url_lower for pattern in politics_patterns):
                groups["Politics"].append(cat_name)
            else:
                # Default to Business for uncategorized
                groups["Business"].append(cat_name)
        
        return groups
    
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
    def get_all_email_templates(cls) -> Dict[str, Dict[str, str]]:
        """Get all email templates"""
        config = cls.load_outreach_config()
        return config.get("email_templates", cls.DEFAULT_OUTREACH_CONFIG["email_templates"])
    
    @classmethod
    def get_google_creds_path(cls) -> str:
        """Get Google credentials file path"""
        config = cls.load_outreach_config()
        return config.get("google_creds_file", "data/google_credentials.json")
    
    @classmethod
    def get_sheet_name(cls) -> str:
        """Get Google Sheet name"""
        config = cls.load_outreach_config()
        return config.get("sheet_name", "cnbc-authors")
    
    @classmethod
    def update_sender_info(cls, name: str, position: str, company: str, industry: str = "") -> bool:
        """Update sender information"""
        try:
            config = cls.load_outreach_config()
            
            if "sender_info" not in config:
                config["sender_info"] = {}
            
            config["sender_info"]["your_name"] = name
            config["sender_info"]["your_position"] = position
            config["sender_info"]["company_name"] = company
            if industry:
                config["sender_info"]["your_industry"] = industry
            
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
    def update_email_settings(cls, include_article_ref: bool, personalization: str, follow_up_days: int, max_per_day: int) -> bool:
        """Update email customization settings"""
        try:
            config = cls.load_outreach_config()
            
            if "email_customization" not in config:
                config["email_customization"] = {}
            
            config["email_customization"]["include_article_reference"] = include_article_ref
            config["email_customization"]["personalization_level"] = personalization
            config["email_customization"]["follow_up_days"] = follow_up_days
            config["email_customization"]["max_emails_per_day"] = max_per_day
            
            return cls.save_outreach_config(config)
        except Exception as e:
            print(f"Error updating email settings: {e}")
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
    
    @classmethod
    def get_scraper_settings(cls) -> Dict[str, Any]:
        """Get scraper-specific settings"""
        config = cls.load_scraper_config()
        return {
            "max_pages": config.get("max_pages_per_category", 5),
            "default_threads": config.get("default_threads", 8),
            "timeout": config.get("request_timeout", 20),
            "batch_size": config.get("batch_size", 40),
            "email_extraction": config.get("email_extraction_enabled", True)
        }
    
    @classmethod
    def update_scraper_settings(cls, max_pages: int, threads: int, timeout: int, batch_size: int, email_extraction: bool) -> bool:
        """Update scraper settings"""
        try:
            config = cls.load_scraper_config()
            
            config["max_pages_per_category"] = max_pages
            config["default_threads"] = threads
            config["request_timeout"] = timeout
            config["batch_size"] = batch_size
            config["email_extraction_enabled"] = email_extraction
            
            return cls.save_scraper_config(config)
        except Exception as e:
            print(f"Error updating scraper settings: {e}")
            return False
    
    @classmethod
    def get_ui_settings(cls) -> Dict[str, Any]:
        """Get UI settings"""
        config = cls.load_outreach_config()
        return config.get("ui_settings", cls.DEFAULT_OUTREACH_CONFIG["ui_settings"])


# Create default configs when module is imported
ConfigManager.create_default_configs()
