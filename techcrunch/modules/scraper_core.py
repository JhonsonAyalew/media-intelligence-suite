# modules/scraper_core.py - OPTIMIZED FOR SPEED (FIXED)
import threading
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random
import re
from collections import defaultdict

# Disable SSL warnings
urllib3.disable_warnings()

# Global session with optimized settings
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# Simple in-memory cache
_article_cache = {}
_author_cache = {}

def scrape_articles(category: str, url: str, max_pages: int, log_callback=None) -> list:
    """Scrape articles from Business Insider category"""
    rows = []
    page = 1
    next_url = url

    while next_url and page <= max_pages:
        if log_callback:
            log_callback(f"[{category}] Scraping page {page}", "progress")
        
        try:
            time.sleep(1)
            r = session.get(next_url, timeout=20, verify=False)
            soup = BeautifulSoup(r.text, "html.parser")

            # BUSINESS INSIDER ARTICLE SELECTOR
            for link in soup.select("a[class*='tout-title-link']"):
                href = link.get("href")
                title = link.text.strip()
                
                if not href or not title:
                    continue
                
                # Make absolute URL
                if href.startswith("/"):
                    href = f"https://www.businessinsider.com{href}"
                
                # Skip if already in list
                if any(row["URL"] == href for row in rows):
                    continue
                
                rows.append({
                    "Author": "",  # Will be filled later
                    "Article Title": title,
                    "URL": href,
                    "Category": category,
                    "Publish Date": datetime.now().strftime("%Y-%m-%d")
                })

            # BUSINESS INSIDER PAGINATION
            nxt = soup.select_one("a[data-testid='pagination-next']")
            next_url = nxt["href"] if nxt else None
            if next_url and next_url.startswith("/"):
                next_url = f"https://www.businessinsider.com{next_url}"
            
            page += 1
            
        except Exception as e:
            if log_callback:
                log_callback(f"[{category}] Error: {str(e)}", "error")
            break

    if log_callback:
        log_callback(f"[{category}] Collected {len(rows)} articles", "success")
    return rows

def extract_author_from_article_page_fast(article_url: str, log_callback=None) -> str:
    """Fast version - uses session and simple caching"""
    try:
        # Check cache first
        if article_url in _article_cache:
            return _article_cache[article_url]
        
        r = session.get(article_url, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # METHOD 1: Try to find author link
        author_link = soup.select_one("a[href*='/author/']")
        if author_link:
            author = author_link.text.strip()
            _article_cache[article_url] = author
            return author
        
        # METHOD 2: Look for byline section
        byline_selectors = [
            "div[data-testid='byline']",
            "div.byline",
            "span.byline",
            "p.byline",
            "div.author-byline",
            "span.author-byline"
        ]
        
        for selector in byline_selectors:
            byline = soup.select_one(selector)
            if byline:
                text = byline.text.strip()
                # Try to extract author name
                if 'By ' in text:
                    parts = text.split('By ')
                    if len(parts) > 1:
                        author = parts[1].split('\n')[0].split(',')[0].strip()
                        if author:
                            _article_cache[article_url] = author
                            return author
                elif 'by ' in text:
                    parts = text.split('by ')
                    if len(parts) > 1:
                        author = parts[1].split('\n')[0].split(',')[0].strip()
                        if author:
                            _article_cache[article_url] = author
                            return author
                # If no "By" found, try to extract name directly
                elif text:
                    # Look for a name pattern (First Last)
                    name_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)', text)
                    if name_match:
                        author = name_match.group(1)
                        _article_cache[article_url] = author
                        return author
        
        # METHOD 3: Look for author in meta tags
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author and meta_author.get('content'):
            author = meta_author['content'].strip()
            _article_cache[article_url] = author
            return author
        
        # METHOD 4: Look for article-author class
        author_div = soup.select_one("div.article-author, span.article-author")
        if author_div:
            author = author_div.text.strip()
            _article_cache[article_url] = author
            return author
        
        # METHOD 5: Search for author name in the article content
        article_body = soup.find('article') or soup.find('div', class_=re.compile(r'article|content|body', re.I))
        if article_body:
            text = article_body.get_text()
            # Look for common author name patterns
            patterns = [
                r'By ([A-Z][a-z]+ [A-Z][a-z]+)',
                r'by ([A-Z][a-z]+ [A-Z][a-z]+)',
                r'Written by ([A-Z][a-z]+ [A-Z][a-z]+)',
                r'Reported by ([A-Z][a-z]+ [A-Z][a-z]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    author = match.group(1)
                    _article_cache[article_url] = author
                    return author
        
        _article_cache[article_url] = ""  # Cache empty result too
        return ""  # No author found
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error extracting author from article: {str(e)[:100]}", "error")
        return ""

def extract_email(soup: BeautifulSoup) -> str:
    """Extract email from Business Insider author page"""
    # BUSINESS INSIDER EMAIL SELECTOR FROM YOUR HTML EXAMPLE
    email_link = soup.select_one("a.author-contact-icon-link.email[href^='mailto:']")
    if email_link:
        email = email_link.get("href", "").replace("mailto:", "").strip()
        # Get the tooltip if available
        if "data-original-title" in email_link.attrs:
            return email_link["data-original-title"]
        return email
    
    # Alternative: any mailto link
    mailto_links = soup.select("a[href^='mailto:']")
    for link in mailto_links:
        email = link.get("href", "").replace("mailto:", "").strip()
        if email:
            return email
    
    return ""

def scrape_author_fast(author_info: dict, log_callback=None) -> dict:
    """Fast author scraping with caching"""
    try:
        # Check cache first
        cache_key = f"{author_info['Profile URL']}_{author_info['Author Name']}"
        if cache_key in _author_cache:
            return _author_cache[cache_key]
        
        r = session.get(author_info["Profile URL"], timeout=10, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")

        # Extract name
        name = author_info.get("Author Name", "")
        if not name:
            name_tag = soup.select_one("h1")
            if name_tag:
                name = name_tag.text.strip()
        
        # Extract role/bio
        role = ""
        bio = ""
        
        # Try different selectors for role
        role_selectors = ["h2", "p.title", "span.role", "div.author-title"]
        for selector in role_selectors:
            role_tag = soup.select_one(selector)
            if role_tag:
                role = role_tag.text.strip()
                break
        
        # Try different selectors for bio
        bio_selectors = ["div.bio", "p.bio", "div.author-bio", "article p"]
        for selector in bio_selectors:
            bio_tag = soup.select_one(selector)
            if bio_tag:
                bio = bio_tag.text.strip()
                break
        
        email = extract_email(soup)
        
        # Extract social links
        twitter = soup.select_one("a[href*='twitter.com'], a[href*='x.com']")
        linkedin = soup.select_one("a[href*='linkedin.com']")
        
        contact_info = []
        if email: 
            contact_info.append(f"Email: {email}")
        if twitter: 
            contact_info.append(f"Twitter: {twitter.get('href', '')}")
        if linkedin: 
            contact_info.append(f"LinkedIn: {linkedin.get('href', '')}")
        
        result = {
            "Author Name": name,
            "Profile URL": author_info["Profile URL"],
            "Email": email,
            "Role / Bio": f"{role} | {bio}" if role or bio else "",
            "Contact Info": ", ".join(contact_info) if contact_info else "",
            "Primary Topic": author_info.get("Primary Topic", "General"),
            "Total Articles": author_info.get("Total Articles", 0)
        }
        
        # Cache the result
        _author_cache[cache_key] = result
        return result
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error scraping author {author_info.get('Author Name')}: {str(e)[:100]}", "error")
        return None

def scrape_authors_from_articles_fast(articles: list, max_threads: int = 10, log_callback=None) -> list:
    """OPTIMIZED VERSION - Much faster but keeps same logic"""
    if not articles:
        return []
    
    # PHASE 1: Get authors from ALL article pages in parallel (MAJOR SPEED BOOST)
    if log_callback:
        log_callback(f"Extracting authors from {len(articles)} articles in parallel...", "info")
    
    updated_articles = []
    article_urls = [article["URL"] for article in articles]
    
    # Process articles in batches to avoid memory issues
    batch_size = 20
    total_batches = (len(articles) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(articles))
        batch_articles = articles[start_idx:end_idx]
        
        if log_callback:
            log_callback(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_articles)} articles)", "progress")
        
        # Extract authors from this batch in parallel
        with ThreadPoolExecutor(max_workers=min(max_threads, len(batch_articles))) as executor:
            future_to_article = {}
            for article in batch_articles:
                future = executor.submit(extract_author_from_article_page_fast, article["URL"], log_callback)
                future_to_article[future] = article
            
            # Process results as they complete
            for future in as_completed(future_to_article):
                article = future_to_article[future]
                try:
                    author = future.result(timeout=15)
                    if author:
                        article["Author"] = author
                        updated_articles.append(article)
                        if log_callback and len(updated_articles) % 10 == 0:
                            log_callback(f"Found authors for {len(updated_articles)} articles so far...", "progress")
                except Exception as e:
                    if log_callback:
                        log_callback(f"Failed to get author for {article['URL'][:50]}: {str(e)[:50]}", "error")
    
    if log_callback:
        log_callback(f"Found {len(updated_articles)} articles with authors", "success")
    
    if not updated_articles:
        if log_callback:
            log_callback("No valid authors found in articles", "warning")
        return []
    
    # PHASE 2: Prepare author data (same as your original logic)
    df = pd.DataFrame(updated_articles)
    
    # Clean author names
    df["Author"] = df["Author"].fillna("").astype(str).str.strip()
    
    # Remove empty authors
    df = df[df["Author"] != ""]
    
    if df.empty:
        if log_callback:
            log_callback("No valid authors found in articles", "warning")
        return []
    
    counts = df["Author"].value_counts()

    # Prepare base author data
    base = df[["Author"]].drop_duplicates()
    base["Author Name"] = base["Author"]
    
    # BUSINESS INSIDER AUTHOR PROFILE URL PATTERN
    def create_bi_profile_url(name):
        if not name:
            return ""
        try:
            # Clean the name
            clean_name = re.sub(r'[^\w\s-]', '', name)
            clean_name = clean_name.strip()
            
            if not clean_name:
                return ""
            
            # Convert to slug
            slug = clean_name.lower().replace(" ", "-")
            return f"https://www.businessinsider.com/author/{slug}"
        except:
            return ""
    
    base["Profile URL"] = base["Author"].apply(create_bi_profile_url)
    base["Total Articles"] = base["Author"].map(counts).fillna(0).astype(int)
    base["Primary Topic"] = "General"

    # Filter out authors with no profile URL
    base = base[base["Profile URL"] != ""]
    
    if log_callback:
        log_callback(f"Found {len(base)} unique authors to scrape", "info")
    
    if len(base) == 0:
        return []

    # PHASE 3: Scrape author profiles in parallel
    results = []
    author_records = base.to_dict("records")
    
    # Process authors in smaller batches for better control
    author_batch_size = min(15, len(author_records))
    total_author_batches = (len(author_records) + author_batch_size - 1) // author_batch_size
    
    for author_batch_num in range(total_author_batches):
        start_idx = author_batch_num * author_batch_size
        end_idx = min((author_batch_num + 1) * author_batch_size, len(author_records))
        batch_authors = author_records[start_idx:end_idx]
        
        if log_callback:
            log_callback(f"Scraping author profiles batch {author_batch_num + 1}/{total_author_batches}...", "progress")
        
        with ThreadPoolExecutor(max_workers=min(max_threads, len(batch_authors))) as executor:
            future_to_author = {}
            for author_data in batch_authors:
                future = executor.submit(scrape_author_fast, author_data, log_callback)
                future_to_author[future] = author_data
            
            for future in as_completed(future_to_author):
                author_data = future_to_author[future]
                try:
                    result = future.result(timeout=20)
                    if result:
                        results.append(result)
                        if log_callback and len(results) % 5 == 0:
                            log_callback(f"Scraped {len(results)} author profiles so far...", "progress")
                except Exception as e:
                    if log_callback:
                        log_callback(f"Failed to scrape author {author_data.get('Author Name', 'Unknown')}: {str(e)[:50]}", "error")

    if log_callback:
        log_callback(f"TOTAL AUTHORS SCRAPED: {len(results)}", "success")
    return results

# Keep the original function for backward compatibility
def scrape_authors_from_articles(articles: list, max_threads: int = 6, log_callback=None) -> list:
    """Original function - now calls the fast version"""
    return scrape_authors_from_articles_fast(articles, max_threads, log_callback)

def extract_author_from_article_page(article_url: str, log_callback=None) -> str:
    """Original function - now calls the fast version"""
    return extract_author_from_article_page_fast(article_url, log_callback)

def scrape_author(author_info: dict, log_callback=None) -> dict:
    """Original function - now calls the fast version"""
    return scrape_author_fast(author_info, log_callback)

# Optional: Function to clear cache if needed
def clear_scraper_cache():
    """Clear all cached data"""
    global _article_cache, _author_cache
    _article_cache.clear()
    _author_cache.clear()
