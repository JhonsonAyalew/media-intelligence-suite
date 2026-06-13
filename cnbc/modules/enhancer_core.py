# modules/enhancer_core.py
import pandas as pd
import re
from datetime import datetime
from collections import Counter
from typing import List, Dict, Tuple


def deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    """Remove duplicate articles based on URL"""
    seen_urls = set()
    unique_articles = []
    
    for article in articles:
        url = article.get("URL", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
    
    return unique_articles


def deduplicate_authors(authors: List[Dict]) -> List[Dict]:
    """Remove duplicate authors based on Profile URL and merge their articles"""
    authors_by_url = {}
    
    for author in authors:
        url = author.get("Profile URL", "")
        if not url:
            continue
            
        if url in authors_by_url:
            # Merge article counts if same author
            existing = authors_by_url[url]
            existing["Total Articles"] = existing.get("Total Articles", 0) + author.get("Total Articles", 0)
            
            # Keep better email if available
            if not existing.get("Email") and author.get("Email"):
                existing["Email"] = author["Email"]
            
            # Keep better bio if available
            if not existing.get("Role / Bio") and author.get("Role / Bio"):
                existing["Role / Bio"] = author["Role / Bio"]
        else:
            authors_by_url[url] = author.copy()
    
    return list(authors_by_url.values())


def extract_clean_email(email_text: str) -> str:
    """Extract and clean email from various formats"""
    if not email_text:
        return ""
    
    email_text = str(email_text).strip()
    
    # If it's already a clean email
    if '@' in email_text and '.' in email_text:
        # Check if it's in format "Email: email@example.com"
        if email_text.lower().startswith('email:'):
            email_text = email_text[6:].strip()
        
        # Clean up common issues
        email_text = email_text.replace('mailto:', '')
        email_text = email_text.split()[0]  # Take first word if there are multiple
        
        # Basic email validation
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_text):
            return email_text.lower()
    
    # If it's in "Contact Info" format, extract email
    if 'email:' in email_text.lower():
        # Try to find email after "Email:"
        email_match = re.search(r'email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', email_text.lower())
        if email_match:
            return email_match.group(1).lower()
    
    return ""


def is_valid_email(email: str) -> bool:
    """Check if email format is valid"""
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip().lower()
    
    # Skip placeholder emails
    if email in ["", "unknown", "n/a", "none", "no email", "email:"]:
        return False
    
    # Check email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False
    
    # Skip obvious fake domains
    fake_domains = ["example.com", "test.com", "domain.com", "company.com"]
    domain = email.split('@')[1] if '@' in email else ""
    if any(fake_domain in domain for fake_domain in fake_domains):
        return False
    
    return True


def is_valid_profile_url(url: str) -> bool:
    """Check if author profile URL is valid (Business Insider format)"""
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Skip placeholder URLs
    if url.lower() in ["", "unknown", "n/a", "none", "no profile"]:
        return False
    
    # Check if it's a Business Insider author URL
    return url.startswith("https://www.businessinsider.com/author/")


def clean_author_data(author: Dict) -> Dict:
    """Clean and enhance author data"""
    cleaned = author.copy()
    
    # Clean author name
    author_name = author.get("Author Name", "")
    if author_name:
        author_name = author_name.strip()
        # Remove numbers like "1. " from the beginning
        author_name = re.sub(r'^\d+\.\s*', '', author_name)
        cleaned["Author Name"] = author_name
    
    # Clean email - extract from Contact Info or Email field
    email = author.get("Email", "")
    contact_info = author.get("Contact Info", "")
    
    # Try to extract email from Contact Info first
    if contact_info:
        extracted_email = extract_clean_email(contact_info)
        if extracted_email:
            cleaned["Email"] = extracted_email
            cleaned["Contact Info"] = contact_info.replace(extracted_email, "").strip()
        elif email:
            # Use the Email field if Contact Info doesn't have it
            cleaned["Email"] = extract_clean_email(email)
    elif email:
        cleaned["Email"] = extract_clean_email(email)
    
    # Clean profile URL
    profile_url = author.get("Profile URL", "")
    if profile_url:
        profile_url = profile_url.strip()
        cleaned["Profile URL"] = profile_url
    
    # Clean role/bio - handle the format from scraper
    role_bio = author.get("Role / Bio", "")
    if role_bio:
        role_bio = role_bio.strip()
        
        # Remove empty "|" patterns
        role_bio = re.sub(r'\s*\|\s*$', '', role_bio)
        role_bio = role_bio.strip()
        
        # Skip if it's just empty or placeholders
        if role_bio.lower() in ["", "unknown", "n/a", "none"]:
            role_bio = ""
        
        cleaned["Role / Bio"] = role_bio
    
    # Clean Contact Info - remove email if it was extracted
    if "Contact Info" in cleaned:
        contact = cleaned["Contact Info"]
        if contact:
            # Remove email if it's in Contact Info
            email_in_contact = extract_clean_email(contact)
            if email_in_contact:
                contact = contact.replace(email_in_contact, "").strip()
                contact = re.sub(r'\s*,\s*,', ',', contact)  # Fix double commas
                contact = re.sub(r'^\s*,\s*', '', contact)  # Remove leading comma
                contact = re.sub(r'\s*,\s*$', '', contact)  # Remove trailing comma
                cleaned["Contact Info"] = contact
    
    # Clean primary topic
    primary_topic = author.get("Primary Topic", "")
    if primary_topic:
        primary_topic = primary_topic.strip()
        if primary_topic.upper() in ["UNKNOWN", "N/A", "NONE"]:
            primary_topic = ""
        cleaned["Primary Topic"] = primary_topic
    
    # Add enhancement timestamp
    cleaned["Enhanced On"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return cleaned


def extract_single_author_from_string(author_string: str) -> str:
    """Extract single author name from strings that might contain multiple authors"""
    if not author_string:
        return ""
    
    author_string = str(author_string).strip()
    
    # Remove numbers like "1. " from the beginning
    author_string = re.sub(r'^\d+\.\s*', '', author_string)
    
    # Check for "and" separator
    if ' and ' in author_string.lower():
        # Take the first author before "and"
        parts = re.split(r'\s+and\s+', author_string, flags=re.IGNORECASE)
        if parts:
            return parts[0].strip()
    
    # Check for "&" separator
    if ' & ' in author_string:
        parts = author_string.split(' & ')
        if parts:
            return parts[0].strip()
    
    # Check for slash separator
    if '/' in author_string:
        parts = author_string.split('/')
        if parts:
            return parts[0].strip()
    
    # Check for comma separator (for lists)
    if ',' in author_string:
        parts = author_string.split(',')
        if parts:
            # Take first part, but avoid taking just "and" if it's in a list
            first_part = parts[0].strip()
            if first_part.lower() != 'and':
                return first_part
    
    # Check for multiple names separated by space (more than 3 words)
    words = author_string.split()
    if len(words) > 3:
        # Assume first two words are first name and last name
        return f"{words[0]} {words[1]}"
    
    return author_string


def clean_article_authors(articles: List[Dict]) -> List[Dict]:
    """Clean author names in articles to extract single authors"""
    cleaned_articles = []
    
    for article in articles:
        cleaned_article = article.copy()
        
        # Clean the author field
        author = article.get("Author", "")
        if author:
            single_author = extract_single_author_from_string(author)
            cleaned_article["Author"] = single_author
        
        cleaned_articles.append(cleaned_article)
    
    return cleaned_articles


def calculate_article_frequency(articles_df: pd.DataFrame, author_name: str) -> Dict:
    """Calculate article frequency for an author"""
    if articles_df.empty or not author_name:
        return {"total": 0, "categories": {}}
    
    author_articles = articles_df[articles_df["Author"] == author_name]
    total = len(author_articles)
    
    # Count articles by category
    categories = {}
    if not author_articles.empty and "Category" in author_articles.columns:
        category_counts = Counter(author_articles["Category"].dropna().str.lower())
        categories = dict(category_counts.most_common(5))
    
    return {"total": total, "categories": categories}


def assign_primary_topic(articles_df: pd.DataFrame, author_name: str) -> str:
    """Assign primary topic based on most frequent article category"""
    if articles_df.empty or not author_name:
        return "General"
    
    author_articles = articles_df[articles_df["Author"] == author_name]
    
    if author_articles.empty or "Category" not in author_articles.columns:
        return "General"
    
    # Get category frequencies
    categories = author_articles["Category"].dropna().str.lower()
    if categories.empty:
        return "General"
    
    category_counter = Counter(categories)
    
    # Get most common category
    if not category_counter:
        return "General"
    
    most_common = category_counter.most_common(1)[0][0]
    
    # Map to clean topic names
    topic_map = {
        "tech": "Technology",
        "finance": "Finance",
        "markets": "Markets",
        "strategy": "Strategy",
        "ai": "AI",
        "artificial intelligence": "AI",
        "fintech": "Fintech",
        "venture capital": "Venture Capital",
        "politics": "Politics",
        "science": "Science",
        "business": "Business",
        "media": "Media",
        "entertainment": "Entertainment"
    }
    
    # Check for exact matches first
    if most_common in topic_map:
        return topic_map[most_common]
    
    # Check for partial matches
    for key, value in topic_map.items():
        if key in most_common:
            return value
    
    # Capitalize first letter if not in map
    return most_common.title()


def filter_valid_authors(authors: List[Dict], articles_df: pd.DataFrame) -> List[Dict]:
    """Filter authors to keep only those with valid profiles"""
    valid_authors = []
    
    for author in authors:
        author_name = author.get("Author Name", "")
        
        # Skip if no name
        if not author_name:
            continue
        
        # Check if author appears in articles (optional, but good to check)
        if not articles_df.empty:
            author_articles = articles_df[articles_df["Author"] == author_name]
            if len(author_articles) == 0:
                # Author not found in articles, but we might still keep if profile is valid
                pass
        
        # Check profile URL - MUST have valid Business Insider profile
        profile_url = author.get("Profile URL", "")
        if not is_valid_profile_url(profile_url):
            continue
        
        # Check email (optional - we can keep authors without email)
        email = author.get("Email", "")
        
        valid_authors.append(author)
    
    return valid_authors


def apply_enhancements(articles: List[Dict], authors: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Apply enhancements to data:
    1. Clean article authors (fix multiple authors)
    2. Remove duplicates
    3. Clean data (extract emails, remove placeholders)
    4. Remove authors without valid Business Insider profiles
    5. Add article frequency data
    6. Assign primary topics
    
    Returns: (articles, enhanced_authors, valid_authors)
    """
    
    # 1️⃣ Clean article authors (fix multiple authors in single field)
    if articles:
        articles = clean_article_authors(articles)
    
    # 2️⃣ Remove duplicate articles
    if articles:
        articles = deduplicate_articles(articles)
    
    # 3️⃣ Remove duplicate authors
    if authors:
        authors = deduplicate_authors(authors)
    
    # Convert articles to DataFrame for processing
    articles_df = pd.DataFrame(articles) if articles else pd.DataFrame()
    
    enhanced_authors = []
    
    for author in authors:
        # 4️⃣ Clean author data (extract emails, clean names, etc.)
        cleaned_author = clean_author_data(author)
        
        author_name = cleaned_author.get("Author Name", "")
        
        # 5️⃣ Calculate article frequency
        freq_data = calculate_article_frequency(articles_df, author_name)
        cleaned_author["Total Articles"] = freq_data["total"]
        
        # 6️⃣ Assign primary topic
        primary_topic = assign_primary_topic(articles_df, author_name)
        cleaned_author["Primary Topic"] = primary_topic
        
        # 7️⃣ Add categories info
        if freq_data["categories"]:
            top_categories = ", ".join(freq_data["categories"].keys())
            cleaned_author["Top Categories"] = top_categories
        
        # 8️⃣ Add data quality indicators
        cleaned_author["Has Email"] = bool(is_valid_email(cleaned_author.get("Email", "")))
        cleaned_author["Has Profile"] = bool(is_valid_profile_url(cleaned_author.get("Profile URL", "")))
        cleaned_author["Has Bio"] = bool(cleaned_author.get("Role / Bio", "").strip())
        
        enhanced_authors.append(cleaned_author)
    
    # 9️⃣ Filter for authors with valid Business Insider profiles
    valid_authors = filter_valid_authors(enhanced_authors, articles_df)
    
    # Return 3 values to match what the UI expects
    return articles, enhanced_authors, valid_authors
