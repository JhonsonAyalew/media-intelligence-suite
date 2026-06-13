# modules/scraper_core.py — CNET SCRAPER (FIXED + SAFE LOGGING + FAST + AUTHOR DATA)

import time
import requests
from bs4 import BeautifulSoup
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random
import re
from urllib.parse import urljoin

urllib3.disable_warnings()

# ---------------- GLOBAL SESSION ----------------

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
})

_author_cache = {}

# ---------------- SAFE LOGGER ----------------

def safe_log(log_callback, msg, level="info"):
    """Never crash if logger signature differs"""
    if not log_callback:
        return
    try:
        log_callback(msg, level)
    except:
        try:
            log_callback(msg)
        except:
            pass

# ---------------- BASE CONFIG ----------------

BASE_URL = "https://www.cnet.com"

# ---------------- HELPERS ----------------

def clean_author_name(name):
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"^by\s+", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def fetch_url(url, log_callback=None):
    """Fetch URL with error handling"""
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        safe_log(log_callback, f"Fetch error {url}: {e}", "error")
        return None

# ---------------- ARTICLE LINKS SCRAPING ----------------

def get_article_links(page, log_callback=None):
    """Get all article links from a specific page"""
    if page == 1:
        url = f"{BASE_URL}/news/"
    else:
        url = f"{BASE_URL}/news/{page}/"

    safe_log(log_callback, f"Fetching page {page}", "progress")
    
    html = fetch_url(url, log_callback)
    if not html:
        return []
        
    soup = BeautifulSoup(html, "html.parser")
    
    links = []
    articles = soup.select("a.c-storiesNeonLatest_story")
    
    for a in articles:
        href = a.get("href")
        if href:
            full_url = urljoin(BASE_URL, href)
            if full_url not in links:
                links.append(full_url)
    
    safe_log(log_callback, f"Page {page}: Found {len(links)} articles", "success")
    return links

# ---------------- ARTICLE SCRAPING ----------------

def scrape_articles(pages_to_scrape=1, log_callback=None):
    """Scrape article links from multiple pages"""
    all_links = []
    
    for page in range(1, pages_to_scrape + 1):
        page_links = get_article_links(page, log_callback)
        all_links.extend(page_links)
        time.sleep(random.uniform(0.3, 0.8))  # Be polite
    
    articles = []
    for link in all_links:
        articles.append({
            "link": link,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    safe_log(log_callback, f"Total articles collected: {len(articles)}", "success")
    return articles

# ---------------- EXTRACT SOCIAL FROM PROFILE ----------------

def extract_social_from_profile(soup):
    """Extract social media links from author profile page"""
    twitter = facebook = email = ""
    
    links = soup.select(".c-socialSharebar_container a")
    
    for link in links:
        href = link.get("href", "")
        if "twitter.com" in href or "x.com" in href:
            twitter = href
        elif "facebook.com" in href:
            facebook = href
        elif "mailto:" in href:
            email = href.replace("mailto:", "")
    
    return twitter, facebook, email

# ---------------- AUTHOR DETAILS FROM ARTICLE ----------------

def extract_author_from_article(article_url, log_callback=None):
    """Extract author name and profile URL from a single article"""
    try:
        html = fetch_url(article_url, log_callback)
        if not html:
            return None
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract author name
        author_tag = soup.select_one('[data-cy="authorName"]')
        if not author_tag:
            return {
                "article_url": article_url,
                "author_name": "Not found",
                "profile_url": "",
                "twitter": "",
                "facebook": "",
                "email": ""
            }
        
        author_name = clean_author_name(author_tag.get_text(strip=True))
        
        # Extract profile URL
        profile_tag = soup.select_one('a[rel="author"]')
        profile_url = ""
        twitter = facebook = email = ""
        
        if profile_tag:
            profile_url = urljoin(BASE_URL, profile_tag["href"])
            
            # Fetch profile page for social links
            profile_html = fetch_url(profile_url, log_callback)
            if profile_html:
                profile_soup = BeautifulSoup(profile_html, "html.parser")
                twitter, facebook, email = extract_social_from_profile(profile_soup)
        
        return {
            "article_url": article_url,
            "author_name": author_name,
            "profile_url": profile_url,
            "twitter": twitter,
            "facebook": facebook,
            "email": email
        }
        
    except Exception as e:
        safe_log(log_callback, f"Error processing {article_url}: {e}", "error")
        return {
            "article_url": article_url,
            "author_name": "ERROR",
            "profile_url": "",
            "twitter": "",
            "facebook": "",
            "email": ""
        }

# ---------------- FAST BATCH ARTICLE PROCESSING ----------------

def process_articles_batch(articles, max_threads=10, log_callback=None):
    """Process multiple articles in parallel"""
    if not articles:
        return []
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(extract_author_from_article, article["link"], log_callback)
            for article in articles
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
                safe_log(log_callback, f"Processed: {result['author_name']}", "debug")
    
    return results

# ---------------- UNIQUE AUTHORS WITH CACHE ----------------

def extract_unique_authors(article_results, log_callback=None):
    """Extract unique authors from article results with caching"""
    unique_authors = {}
    
    for result in article_results:
        if result.get("profile_url") and result.get("author_name") and result["author_name"] not in ["Not found", "ERROR"]:
            profile_url = result["profile_url"]
            if profile_url not in unique_authors:
                unique_authors[profile_url] = {
                    "Author Name": result["author_name"],
                    "Profile URL": profile_url,
                    "Twitter": result.get("twitter", ""),
                    "Facebook": result.get("facebook", ""),
                    "Email": result.get("email", ""),
                    "Articles": []
                }
            # Add article to author's articles
            unique_authors[profile_url]["Articles"].append(result["article_url"])
    
    safe_log(log_callback, f"Unique authors found: {len(unique_authors)}", "success")
    return list(unique_authors.values())

# ---------------- AUTHOR DETAILS ENRICHMENT ----------------

def enrich_author_details(author_data, log_callback=None):
    """Enrich author data with additional details (can be extended)"""
    # Check cache first
    cache_key = author_data["Profile URL"].lower()
    if cache_key in _author_cache:
        return _author_cache[cache_key]
    
    # Add publication name
    author_data["Publication Name"] = "CNET"
    
    # Add article count
    author_data["Article Count"] = len(author_data.get("Articles", []))
    
    # Remove Articles list from final output (optional)
    if "Articles" in author_data:
        del author_data["Articles"]
    
    # Cache the result
    _author_cache[cache_key] = author_data
    
    return author_data

# ---------------- MAIN SCRAPER FUNCTION ----------------

def scrape_authors_directly(section_url=None, max_pages=1, max_threads=10, log_callback=None):
    """
    Main function to scrape authors from CNET
    
    Args:
        section_url: Not used for CNET (kept for compatibility)
        max_pages: Number of pages to scrape
        max_threads: Number of concurrent threads
        log_callback: Logging callback function
    
    Returns:
        List of author data dictionaries
    """
    safe_log(log_callback, "Starting CNET scraper", "info")
    
    # Step 1: Scrape article links
    articles = scrape_articles(max_pages, log_callback)
    if not articles:
        safe_log(log_callback, "No articles found", "warning")
        return []
    
    # Step 2: Process articles in parallel to get author info
    article_results = process_articles_batch(articles, max_threads, log_callback)
    
    # Step 3: Extract unique authors
    unique_authors = extract_unique_authors(article_results, log_callback)
    
    # Step 4: Enrich author data
    enriched_authors = []
    for author in unique_authors:
        enriched = enrich_author_details(author, log_callback)
        enriched_authors.append(enriched)
    
    safe_log(log_callback, f"Final authors scraped: {len(enriched_authors)}", "success")
    return enriched_authors

# ---------------- COMPATIBILITY FUNCTION ----------------

def scrape_authors_from_articles(articles, max_threads=10, log_callback=None):
    """
    Compatibility function to match Verge scraper interface
    """
    article_results = process_articles_batch(articles, max_threads, log_callback)
    unique_authors = extract_unique_authors(article_results, log_callback)
    
    enriched_authors = []
    for author in unique_authors:
        enriched = enrich_author_details(author, log_callback)
        enriched_authors.append(enriched)
    
    return enriched_authors

# ---------------- CACHE CLEAR ----------------

def clear_scraper_cache():
    """Clear the author cache"""
    global _author_cache
    _author_cache.clear()
