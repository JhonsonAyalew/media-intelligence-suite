# modules/config_manager.py - UPDATED FOR THE VERGE
import json
import os
from typing import Dict, Any


class ConfigManager:
    # DEFAULT CONFIGURATION FOR THE VERGE
    DEFAULT_SCRAPER_CONFIG = {
        "site_name": "The Verge",
        "base_url": "https://www.theverge.com",
        "categories": {
            # Tech
            "tech": "https://www.theverge.com/tech",
            "amazon": "https://www.theverge.com/amazon",
            "apple": "https://www.theverge.com/apple",
            "facebook": "https://www.theverge.com/facebook",
            "google": "https://www.theverge.com/google",
            "microsoft": "https://www.theverge.com/microsoft",
            "samsung": "https://www.theverge.com/samsung",
            "business": "https://www.theverge.com/business",
            
            # Reviews
            "smart-home-review": "https://www.theverge.com/smart-home-review",
            "phone-review": "https://www.theverge.com/phone-review",
            "tablet-review": "https://www.theverge.com/tablet-review",
            "headphone-review": "https://www.theverge.com/headphone-review",
            "reviews": "https://www.theverge.com/reviews",
            
            # Science
            "space": "https://www.theverge.com/space",
            "energy": "https://www.theverge.com/energy",
            "environment": "https://www.theverge.com/environment",
            "health": "https://www.theverge.com/health",
            "science": "https://www.theverge.com/science",
            
            # Policy
            "policy": "https://www.theverge.com/policy",
            "antitrust": "https://www.theverge.com/antitrust",
            "politics": "https://www.theverge.com/politics",
            "law": "https://www.theverge.com/law",
            "cyber-security": "https://www.theverge.com/cyber-security",
            
            # Transportation
            "transportation": "https://www.theverge.com/transportation",
            "electric-cars": "https://www.theverge.com/electric-cars",
            "autonomous-cars": "https://www.theverge.com/autonomous-cars",
            "ride-sharing": "https://www.theverge.com/ride-sharing"
        },
        "max_pages_per_category": 3,
        "default_threads": 8,
        "request_timeout": 15,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "email_extraction_enabled": True,
        "batch_size": 50,
        "author_url_pattern": "https://www.theverge.com/authors/{author_slug}",
        "use_author_slug_normalization": True
    }
    
    DEFAULT_OUTREACH_CONFIG = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "email_address": "",
        "email_password": "",
        "google_creds_file": "data/google_credentials.json",
        "sheet_name": "theverge-authors",
        "email_templates": {
            "default": {
                "subject": "Regarding your recent reporting at The Verge - {author_name}",
                "body": """Dear {author_name},

I hope this message finds you well.

I've been following your excellent reporting at The Verge, particularly your coverage of {topic}.
Your insights and depth of analysis on technology topics have been both informative and thought-provoking.

I'm {your_name} from {company_name}, and I represent a team that values high-quality tech journalism and in-depth reporting.
Given your expertise and the quality of your work, I believe there could be meaningful collaboration opportunities that would benefit both our audiences.

Would you be open to a brief conversation about potential ways we might work together?

I look forward to hearing your thoughts.

Best regards,
{your_name}
{your_position}
{company_name}"""
            },
            "tech_specific": {
                "subject": "Appreciation for your The Verge article on {topic}",
                "body": """Hello {author_name},

I recently read your article at The Verge about {topic} and was impressed by the depth of your research and clarity of your writing.
As someone who follows tech journalism closely, I appreciate the thoroughness you bring to your reporting.

I'm {your_name}, working with {company_name} where we focus on {your_industry}.
We're interested in connecting with accomplished tech journalists like yourself who share our commitment to quality content.

Would you be interested in discussing potential collaboration opportunities?

Best regards,
{your_name}
{your_position}
{company_name}"""
            },
            "reviewer": {
                "subject": "Regarding your product reviews at The Verge",
                "body": """Dear {author_name},

I've been following your product reviews at The Verge and have consistently been impressed with your thorough testing methodology and honest assessments.
Your recent review of {topic} was particularly insightful and helpful.

I'm {your_name} from {company_name}. We work in the {your_industry} space and are always looking to connect with reviewers who share our commitment to honest, detailed analysis.

Would you be open to a conversation about potential collaboration opportunities?

Sincerely,
{your_name}
{your_position}
{company_name}"""
            },
            "policy_expert": {
                "subject": "Regarding your tech policy coverage at The Verge",
                "body": """Hi {author_name},

Your coverage of tech policy issues at The Verge has been exceptional. The way you break down complex topics like {topic} makes them accessible while maintaining depth and accuracy.

I'm {your_name} from {company_name}. We follow tech policy closely and your reporting has been invaluable for understanding these issues.

I'd love to connect and explore if there might be opportunities for collaboration or knowledge exchange.

Best,
{your_name}
{your_position}
{company_name}"""
            },
            "science_writer": {
                "subject": "Admiration for your science reporting at The Verge",
                "body": """Dear {author_name},

Your science reporting at The Verge, especially on {topic}, stands out for its ability to make complex scientific concepts engaging and understandable.
It's rare to find journalists who can bridge the gap between scientific complexity and public understanding so effectively.

I'm {your_name} from {company_name}. We're passionate about science communication and would love to connect with someone of your caliber.

Would you be open to discussing potential collaboration?

Best regards,
{your_name}
{your_position}
{company_name}"""
            },
            "transportation": {
                "subject": "Regarding your transportation coverage at The Verge",
                "body": """Hello {author_name},

Your coverage of transportation technology at The Verge, particularly your articles on {topic}, has been outstanding.
The future of mobility is one of the most exciting areas in tech right now, and your reporting captures that excitement while maintaining journalistic rigor.

I'm {your_name} from {company_name}, working in the {your_industry} space.
I'd love to connect and discuss potential collaboration opportunities.

Sincerely,
{your_name}
{your_position}
{company_name}"""
            }
        },
        "sender_info": {
            "your_name": "Your Name",
            "your_position": "Tech Industry Relations",
            "company_name": "Your Company",
            "your_industry": "technology and media"
        },
        "ui_settings": {
            "theme": "light",
            "font_size": 10,
            "auto_save": True,
            "primary_color": "#00D474",  # The Verge Green
            "secondary_color": "#1A1A1A",  # The Verge Dark
            "accent_color": "#FF4F00"  # The Verge Orange
        },
        "email_customization": {
            "include_article_reference": True,
            "personalization_level": "high",
            "follow_up_days": 7,
            "max_emails_per_day": 40,
            "reference_verge_specific": True
        }
    }
    
    @classmethod
    def load_scraper_config(cls) -> Dict[str, Any]:
        """Load scraper configuration for The Verge"""
        config_file = "data/scraper_config.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Merge with defaults
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
        """Get scraping categories for The Verge"""
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
        
        # Group categories based on the structure provided
        groups = {
            "Tech": [],
            "Reviews": [],
            "Science": [],
            "Policy": [],
            "Transportation": []
        }
        
        # Map categories to groups
        category_to_group = {
            # Tech
            "tech": "Tech",
            "amazon": "Tech",
            "apple": "Tech",
            "facebook": "Tech",
            "google": "Tech",
            "microsoft": "Tech",
            "samsung": "Tech",
            "business": "Tech",
            
            # Reviews
            "smart-home-review": "Reviews",
            "phone-review": "Reviews",
            "tablet-review": "Reviews",
            "headphone-review": "Reviews",
            "reviews": "Reviews",
            
            # Science
            "space": "Science",
            "energy": "Science",
            "environment": "Science",
            "health": "Science",
            "science": "Science",
            
            # Policy
            "policy": "Policy",
            "antitrust": "Policy",
            "politics": "Policy",
            "law": "Policy",
            "cyber-security": "Policy",
            
            # Transportation
            "transportation": "Transportation",
            "electric-cars": "Transportation",
            "autonomous-cars": "Transportation",
            "ride-sharing": "Transportation"
        }
        
        for cat_name, cat_url in categories.items():
            if cat_name in category_to_group:
                groups[category_to_group[cat_name]].append(cat_name)
            else:
                # Fallback: try to infer from URL path
                if "/reviews" in cat_url or "review" in cat_name:
                    groups["Reviews"].append(cat_name)
                elif "/science" in cat_url or cat_name in ["space", "energy", "environment", "health"]:
                    groups["Science"].append(cat_name)
                elif "/policy" in cat_url or cat_name in ["antitrust", "politics", "law", "cyber-security"]:
                    groups["Policy"].append(cat_name)
                elif "/transportation" in cat_url or cat_name in ["electric-cars", "autonomous-cars", "ride-sharing"]:
                    groups["Transportation"].append(cat_name)
                else:
                    groups["Tech"].append(cat_name)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
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
        return config.get("sheet_name", "theverge-authors")
    
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
            
            # Create main config.json if it doesn't exist
            main_config_file = "data/config.json"
            if not os.path.exists(main_config_file):
                with open(main_config_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "google_creds_file": "data/google_credentials.json",
                        "sheet_name": "theverge-authors",
                        "smtp_configured": False
                    }, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error creating default configs: {e}")
            return False
    
    @classmethod
    def get_scraper_settings(cls) -> Dict[str, Any]:
        """Get scraper-specific settings"""
        config = cls.load_scraper_config()
        return {
            "max_pages": config.get("max_pages_per_category", 3),
            "default_threads": config.get("default_threads", 8),
            "timeout": config.get("request_timeout", 15),
            "batch_size": config.get("batch_size", 50),
            "email_extraction": config.get("email_extraction_enabled", True),
            "use_author_slug": config.get("use_author_slug_normalization", True)
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
    
    @classmethod
    def get_author_url_pattern(cls) -> str:
        """Get author URL pattern for The Verge"""
        config = cls.load_scraper_config()
        return config.get("author_url_pattern", "https://www.theverge.com/authors/{author_slug}")
    
    @classmethod
    def should_use_author_slug_normalization(cls) -> bool:
        """Check if author slug normalization should be used"""
        config = cls.load_scraper_config()
        return config.get("use_author_slug_normalization", True)


# Create default configs when module is imported
ConfigManager.create_default_configs()