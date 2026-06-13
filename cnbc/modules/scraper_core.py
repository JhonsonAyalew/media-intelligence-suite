# modules/scraper_core.py - OPTIMIZED FOR CNBC WITH TWITTER EXTRACTION
import threading
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import random
import re
from collections import defaultdict
import json
import html

# Disable SSL warnings
urllib3.disable_warnings()

# Global session with optimized settings
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
})

# Simple in-memory cache
_article_cache = {}
_author_cache = {}
_article_soup_cache = {}

def scrape_articles(category: str, url: str, max_pages: int, log_callback=None) -> list:
    """Scrape articles from CNBC category - OPTIMIZED VERSION"""
    articles = []
    page = 1
    
    # Generate page URLs (CNBC pagination pattern)
    while page <= max_pages:
        if log_callback:
            log_callback(f"[{category}] Scraping page {page}/{max_pages}", "progress")
        
        try:
            # Add page parameter for pagination
            page_url = f"{url}?page={page}" if page > 1 else url
            
            # Slight delay to be respectful
            time.sleep(random.uniform(0.5, 1.5))
            
            r = session.get(page_url, timeout=15, verify=False)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            
            # CNBC ARTICLE SELECTORS - Multiple patterns to catch all articles
            article_selectors = [
                "div.Card-standardBreakerCard",
                "div.Card-rectangleCard", 
                "div.Card-mediaCard",
                "a.Card-title",
                "div.RiverHeadline-headline",
                "div.RiverCard-riverCard"
            ]
            
            found_on_page = 0
            
            # Try different selectors
            for selector in article_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    try:
                        # Get article link
                        if selector == "a.Card-title":
                            link_elem = elem
                        else:
                            link_elem = elem.select_one("a.Card-title") or elem.select_one("a")
                        
                        if not link_elem:
                            continue
                        
                        href = link_elem.get("href", "")
                        if not href:
                            continue
                        
                        # Make absolute URL
                        if not href.startswith("http"):
                            href = f"https://www.cnbc.com{href}"
                        
                        # Skip duplicates
                        if any(article["URL"] == href for article in articles):
                            continue
                        
                        # Get title
                        title = ""
                        title_elem = link_elem.select_one("span") or link_elem
                        if title_elem:
                            title = title_elem.text.strip()
                        
                        # If no title, try alternative selectors
                        if not title:
                            title_elem = elem.select_one("div.Card-headline") or elem.select_one("h3")
                            if title_elem:
                                title = title_elem.text.strip()
                        
                        if not title:
                            continue
                        
                        # Get publication date
                        pub_date = datetime.now().strftime("%Y-%m-%d")
                        date_elem = elem.select_one("time") or elem.select_one("span.RiverByline-datePublished")
                        if date_elem:
                            date_text = date_elem.text.strip()
                            # Try to parse various date formats
                            try:
                                if "ago" in date_text.lower():
                                    # Handle relative dates like "2 hours ago"
                                    pub_date = datetime.now().strftime("%Y-%m-%d")
                                else:
                                    # Try to parse absolute date
                                    pub_date = date_text[:10]  # Get first 10 chars for YYYY-MM-DD
                            except:
                                pass
                        
                        articles.append({
                            "Author": "",  # Will be filled later
                            "Article Title": title[:500],  # Limit title length
                            "URL": href,
                            "Category": category,
                            "Publish Date": pub_date,
                            "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        found_on_page += 1
                        
                        # Early exit if we found a reasonable number
                        if found_on_page >= 25:  # CNBC shows ~20-30 articles per page
                            break
                            
                    except Exception as e:
                        continue  # Skip this element if error
                
                if found_on_page >= 25:
                    break
            
            if log_callback:
                log_callback(f"[{category}] Page {page}: Found {found_on_page} articles", "info")
            
            # Check if there are more pages
            next_button = soup.select_one("a[data-testid='pagination-next']") or soup.select_one("a:contains('Next')")
            if not next_button and found_on_page < 10:
                # If we didn't find many articles and no next button, likely no more pages
                break
                
            page += 1
            
        except Exception as e:
            if log_callback:
                log_callback(f"[{category}] Error on page {page}: {str(e)[:100]}", "error")
            break
    
    if log_callback:
        log_callback(f"[{category}] TOTAL ARTICLES: {len(articles)}", "success")
    
    return articles

def extract_twitter_from_author_page(author_url: str, log_callback=None) -> str:
    """Extract Twitter handle from CNBC author profile page"""
    try:
        if not author_url or not author_url.startswith("http"):
            return ""
        
        r = session.get(author_url, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # METHOD 1: Look for Twitter links in social channels
        social_channels = soup.select_one("ul.RenderBioDetails-socialChannels")
        if social_channels:
            # Look for Twitter/X links
            twitter_links = social_channels.select("a[href*='twitter.com'], a[href*='x.com']")
            for link in twitter_links:
                href = link.get("href", "").strip()
                if href:
                    # Extract handle from URL
                    handle_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', href)
                    if handle_match:
                        return f"@{handle_match.group(1)}"
        
        # METHOD 2: Look for Twitter icon with class
        twitter_icon = soup.select_one("a.icon-social_twitter")
        if twitter_icon:
            href = twitter_icon.get("href", "").strip()
            if href:
                handle_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', href)
                if handle_match:
                    return f"@{handle_match.group(1)}"
        
        # METHOD 3: Look for any Twitter link on the page
        all_twitter_links = soup.select("a[href*='twitter.com'], a[href*='x.com']")
        for link in all_twitter_links:
            href = link.get("href", "").strip()
            if href and ("twitter.com" in href or "x.com" in href):
                # Skip if it's a generic Twitter/X homepage
                if href.endswith("twitter.com") or href.endswith("x.com"):
                    continue
                    
                handle_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', href)
                if handle_match:
                    return f"@{handle_match.group(1)}"
        
        return ""
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error extracting Twitter from {author_url[:50]}: {str(e)[:50]}", "error")
        return ""

def extract_author_and_twitter_from_article_page_fast(article_url: str, log_callback=None) -> dict:
    """ULTRA-FAST author extraction from CNBC article pages (without email)"""
    try:
        # Check cache first
        if article_url in _article_cache:
            return _article_cache[article_url]
        
        # Get page
        r = session.get(article_url, timeout=8, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        
        author_data = {"name": "", "author_url": "", "twitter": ""}
        
        # STRATEGY 1: Author link with href (for name and author_url)
        author_link = soup.select_one("a.Author-authorName")
        if author_link:
            author_name = author_link.text.strip()
            author_url = author_link.get("href", "")
            if not author_url.startswith("http"):
                author_url = f"https://www.cnbc.com{author_url}"
            
            author_data["name"] = author_name
            author_data["author_url"] = author_url
        
        # STRATEGY 2: Meta tags (fastest for name)
        if not author_data["name"]:
            meta_author = soup.find("meta", {"name": "author"}) or soup.find("meta", {"property": "article:author"})
            if meta_author and meta_author.get("content"):
                author_name = meta_author["content"].strip()
                if author_name:
                    author_data["name"] = author_name
                    if not author_data["author_url"]:
                        # Try to construct author URL from name
                        slug = author_name.lower().replace(' ', '-').replace('.', '').replace(',', '')
                        author_data["author_url"] = f"https://www.cnbc.com/{slug}/"
        
        # Cache the result
        _article_cache[article_url] = author_data
        return author_data
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error extracting author from {article_url[:50]}: {str(e)[:50]}", "error")
        return {"name": "", "author_url": "", "twitter": ""}

def scrape_cnbc_author_fast(author_url: str, author_name: str = "", log_callback=None) -> dict:
    """Fast CNBC author profile scraping with Twitter extraction"""
    try:
        # Check cache first
        cache_key = f"{author_url}_{author_name}"
        if cache_key in _author_cache:
            return _author_cache[cache_key]
        
        # If no author_url but we have name, try to construct it
        if not author_url and author_name:
            slug = author_name.lower().replace(" ", "-").replace(".", "").replace(",", "")
            author_url = f"https://www.cnbc.com/{slug}/"
        
        role = ""
        bio = ""
        twitter_handle = ""
        linkedin_url = ""
        
        # Try to get additional info from author page if URL exists
        if author_url and author_url.startswith("http"):
            try:
                r = session.get(author_url, timeout=10, verify=False)
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Extract role/Title
                role_elem = soup.select_one("span.RenderBioDetails-jobTitle") or soup.select_one("div.author-title")
                if role_elem:
                    role = role_elem.text.strip()
                
                # Extract bio
                bio_elem = soup.select_one("div.RenderBioDetails-bioText") or soup.select_one("div.author-bio")
                if bio_elem:
                    bio = bio_elem.text.strip()[:500]
                
                # Extract Twitter handle
                twitter_handle = extract_twitter_from_author_page(author_url, log_callback)
                
                # Extract LinkedIn URL
                linkedin_elem = soup.select_one("a[href*='linkedin.com']")
                if linkedin_elem:
                    linkedin_url = linkedin_elem.get("href", "").strip()
                    
            except Exception as e:
                if log_callback:
                    log_callback(f"Could not fetch author page {author_url}: {str(e)[:50]}", "warning")
        
        # Prepare contact info
        contact_info = []
        if twitter_handle:
            contact_info.append(f"Twitter: {twitter_handle}")
        if linkedin_url:
            contact_info.append(f"LinkedIn: {linkedin_url}")
        
        result = {
            "Author Name": author_name or "Unknown",
            "Profile URL": author_url or "",
            "Email": "",  # Empty since we're not extracting emails anymore
            "Role / Bio": f"{role} | {bio}" if role or bio else "",
            "Contact Info": "; ".join(contact_info) if contact_info else "",
            "Primary Topic": "General",
            "Total Articles": 1,
            "Publication Name": "CNBC",
            "Tier": "High",
            "Notes": bio[:200] if bio else "",
            "Twitter Handle": twitter_handle,
            "LinkedIn URL": linkedin_url,
            "Social Source": "Author Page"
        }
        
        # Cache the result
        _author_cache[cache_key] = result
        return result
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error scraping author {author_name or author_url}: {str(e)[:50]}", "error")
        
        # Return basic info if scraping fails
        return {
            "Author Name": author_name or "Unknown",
            "Profile URL": author_url or "",
            "Email": "",
            "Role / Bio": "",
            "Contact Info": "",
            "Primary Topic": "General",
            "Total Articles": 1,
            "Publication Name": "CNBC",
            "Tier": "High",
            "Notes": "Profile scraping failed",
            "Twitter Handle": "",
            "LinkedIn URL": "",
            "Social Source": "Failed"
        }

def scrape_authors_from_articles_ultrafast_with_twitter(articles: list, max_threads: int = 15, log_callback=None) -> list:
    """ULTRA-FAST author scraping with Twitter extraction from author pages"""
    if not articles:
        return []
    
    total_articles = len(articles)
    
    # PHASE 1: Extract authors from ALL articles in parallel
    if log_callback:
        log_callback(f"⚡ EXTRACTING AUTHORS from {total_articles} articles...", "info")
    
    all_author_data = []
    article_urls = [article["URL"] for article in articles]
    
    # Process in batches for maximum speed
    batch_size = min(40, total_articles)
    total_batches = (total_articles + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, total_articles)
        batch_urls = article_urls[start_idx:end_idx]
        
        if log_callback:
            log_callback(f"🔧 Batch {batch_num + 1}/{total_batches} ({len(batch_urls)} articles)", "progress")
        
        # Extract authors from this batch in parallel
        with ThreadPoolExecutor(max_workers=min(max_threads, len(batch_urls))) as executor:
            futures = {executor.submit(extract_author_and_twitter_from_article_page_fast, url, log_callback): url 
                      for url in batch_urls}
            
            # Process results as they complete
            for future in as_completed(futures):
                try:
                    author_info = future.result(timeout=12)
                    if author_info and author_info["name"]:
                        article_url = futures[future]
                        all_author_data.append({
                            "name": author_info["name"],
                            "author_url": author_info["author_url"],
                            "article_url": article_url
                        })
                        
                        # Progress update
                        if len(all_author_data) % 10 == 0:
                            if log_callback:
                                log_callback(f"📊 Found {len(all_author_data)} authors...", "progress")
                            
                except Exception as e:
                    if log_callback:
                        log_callback(f"⚠️ Failed to process article: {str(e)[:50]}", "warning")
                    continue
    
    if not all_author_data:
        if log_callback:
            log_callback("❌ No authors found in articles", "error")
        return []
    
    if log_callback:
        log_callback(f"✅ Found {len(all_author_data)} author mentions", "success")
    
    # PHASE 2: Group authors
    author_dict = {}
    
    for author_data in all_author_data:
        name = author_data["name"]
        author_url = author_data["author_url"]
        
        if name not in author_dict:
            author_dict[name] = {
                "name": name,
                "author_urls": set(),
                "article_count": 0,
                "article_urls": []
            }
        
        author_dict[name]["article_count"] += 1
        author_dict[name]["article_urls"].append(author_data["article_url"])
        
        if author_url:
            author_dict[name]["author_urls"].add(author_url)
    
    # Prepare author records for scraping
    author_records = []
    for name, data in author_dict.items():
        # Choose best author URL (prefer non-empty)
        best_author_url = next(iter(data["author_urls"]), "")
        
        author_records.append({
            "Author Name": name,
            "Profile URL": best_author_url,
            "Total Articles": data["article_count"],
            "Article URLs": data["article_urls"][:3]  # Keep first 3 for reference
        })
    
    # PHASE 3: Scrape additional author info with Twitter extraction
    if log_callback:
        log_callback(f"👥 Enriching {len(author_records)} author profiles with Twitter...", "info")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=min(max_threads * 2, len(author_records))) as executor:
        futures = {executor.submit(scrape_cnbc_author_fast, 
                                  author["Profile URL"], 
                                  author["Author Name"], 
                                  log_callback): author 
                  for author in author_records}
        
        for future in as_completed(futures):
            try:
                author_result = future.result(timeout=15)
                if author_result:
                    results.append(author_result)
                    
                    # Progress update
                    if len(results) % 10 == 0:
                        twitter_found = sum(1 for r in results if r.get("Twitter Handle"))
                        if log_callback:
                            log_callback(f"👤 Enriched {len(results)} profiles ({twitter_found} with Twitter)...", "progress")
                            
            except Exception as e:
                author_data = futures[future]
                if log_callback:
                    log_callback(f"⚠️ Failed to enrich {author_data['Author Name']}: {str(e)[:50]}", "warning")
                
                # Add basic author info even if enrichment fails
                results.append({
                    "Author Name": author_data["Author Name"],
                    "Profile URL": author_data["Profile URL"],
                    "Email": "",
                    "Role / Bio": "",
                    "Contact Info": "",
                    "Primary Topic": "General",
                    "Total Articles": author_data["Total Articles"],
                    "Publication Name": "CNBC",
                    "Tier": "High",
                    "Notes": f"Found in {author_data['Total Articles']} articles",
                    "Twitter Handle": "",
                    "LinkedIn URL": "",
                    "Social Source": "Failed"
                })
    
    # Final statistics
    twitter_found = sum(1 for r in results if r.get("Twitter Handle"))
    if log_callback:
        log_callback(f"🎉 FINAL: {len(results)} authors processed ({twitter_found} with Twitter)", "success")
        log_callback(f"🐦 Twitter extraction rate: {(twitter_found/len(results)*100):.1f}%", "info")
    
    return results

def scrape_authors_from_articles(articles: list, max_threads: int = 6, log_callback=None) -> list:
    """Main function - calls the ultra-fast version with Twitter extraction"""
    # Use more threads by default for CNBC
    threads = max(max_threads, 12)
    return scrape_authors_from_articles_ultrafast_with_twitter(articles, threads, log_callback)

def extract_author_from_article_page(article_url: str, log_callback=None) -> str:
    """Wrapper for backward compatibility - returns author name only"""
    result = extract_author_and_twitter_from_article_page_fast(article_url, log_callback)
    return result["name"]

def scrape_author(author_info: dict, log_callback=None) -> dict:
    """Wrapper for backward compatibility"""
    return scrape_cnbc_author_fast(
        author_info.get("Profile URL", ""),
        author_info.get("Author Name", ""),
        log_callback
    )

def clear_scraper_cache():
    """Clear all cached data"""
    global _article_cache, _author_cache, _article_soup_cache
    _article_cache.clear()
    _author_cache.clear()
    _article_soup_cache.clear()

# Test function
def test_twitter_extraction():
    """Test Twitter extraction from CNBC author pages"""
    test_urls = [
        "https://www.cnbc.com/katie-tarallo/",  # Example author page
        "https://www.cnbc.com/megan-cassella/",
        "https://www.cnbc.com/lauren-feiner/"
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        twitter = extract_twitter_from_author_page(url)
        print(f"Twitter: {twitter}")
        
        # Also test full author scraping
        author_info = scrape_cnbc_author_fast(url, "Test Author")
        print(f"Full Info: {author_info}")
