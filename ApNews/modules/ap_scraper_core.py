# modules/scraper_core.py — AP NEWS SCRAPER (FIXED + SAFE LOGGING + FAST + AUTHOR DATA)

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

BASE_URL = "https://apnews.com"
POLITICS_URL = "https://apnews.com/politics"

# ---------------- CLOUDFLARE EMAIL DECODER ----------------

def decode_cf_email(encoded_string):
    """Decode Cloudflare protected email addresses"""
    try:
        # Remove the /cdn-cgi/l/email-protection# part if present
        if '#39;' in encoded_string:
            encoded_string = encoded_string.split('#39;')[-1].split("'")[0]
        elif '#' in encoded_string:
            encoded_string = encoded_string.split('#')[-1]
        
        r = int(encoded_string[:2], 16)
        email = ''.join([chr(int(encoded_string[i:i+2], 16) ^ r) for i in range(2, len(encoded_string), 2)])
        return email
    except:
        return encoded_string

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

def extract_email_from_page(soup, log_callback=None):
    """Extract email from page using multiple methods"""
    email = ""
    
    # Method 1: Look for mailto links
    mailto_links = soup.find_all("a", href=re.compile(r"^mailto:"))
    for link in mailto_links:
        email = link["href"].replace("mailto:", "").strip()
        if email:
            return email
    
    # Method 2: Look for Cloudflare protected emails in links
    cf_links = soup.find_all("a", href=re.compile(r"/cdn-cgi/l/email-protection"))
    for link in cf_links:
        href = link.get("href", "")
        if "#" in href:
            encoded = href.split("#")[-1]
            decoded = decode_cf_email(encoded)
            if decoded and "@" in decoded:
                return decoded
    
    # Method 3: Look for data-social-service="mailto" links
    social_links = soup.find_all("a", attrs={"data-social-service": "mailto"})
    for link in social_links:
        href = link.get("href", "")
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").strip()
            return email
        elif "/cdn-cgi/l/email-protection" in href:
            if "#" in href:
                encoded = href.split("#")[-1]
                decoded = decode_cf_email(encoded)
                if decoded and "@" in decoded:
                    return decoded
    
    # Method 4: Search script tags for encoded emails
    script_tags = soup.find_all("script")
    for script in script_tags:
        if script.string and "email-protection" in str(script.string):
            cf_matches = re.findall(r'#([a-f0-9]{20,})', str(script.string))
            for match in cf_matches:
                decoded = decode_cf_email(match)
                if decoded and "@" in decoded and "." in decoded:
                    return decoded
    
    # Method 5: Regex search entire page
    page_text = str(soup)
    cf_pattern = r'/cdn-cgi/l/email-protection#([a-f0-9]{20,})'
    cf_matches = re.findall(cf_pattern, page_text)
    for match in cf_matches:
        decoded = decode_cf_email(match)
        if decoded and "@" in decoded and "." in decoded:
            return decoded
    
    return email

# ---------------- ARTICLE LINKS SCRAPING ----------------

def get_article_links(category_url=POLITICS_URL, log_callback=None):
    """Get all article links from a category page"""
    safe_log(log_callback, f"Fetching category page", "progress")
    
    html = fetch_url(category_url, log_callback)
    if not html:
        return []
        
    soup = BeautifulSoup(html, "html.parser")
    
    links = set()
    articles = soup.find_all("div", class_="PagePromo")
    
    for article in articles:
        link_tag = article.find("a", href=True)
        if link_tag and "/article/" in link_tag["href"]:
            full_link = urljoin(BASE_URL, link_tag["href"])
            links.add(full_link)
    
    safe_log(log_callback, f"Found {len(links)} articles", "success")
    return list(links)

# ---------------- ARTICLE SCRAPING ----------------

def scrape_articles(category_url=POLITICS_URL, log_callback=None):
    """Scrape article links from a category page"""
    article_links = get_article_links(category_url, log_callback)
    
    articles = []
    for link in article_links:
        articles.append({
            "link": link,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    safe_log(log_callback, f"Total articles collected: {len(articles)}", "success")
    return articles

# ---------------- AUTHOR DETAILS FROM ARTICLE ----------------

def extract_article_info(article_url, log_callback=None):
    """Extract article title from article page"""
    try:
        html = fetch_url(article_url, log_callback)
        if not html:
            return None
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract article title
        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "No Title"
        
        # Find author byline
        byline = soup.find("div", class_="Page-authors")
        if not byline:
            return None
        
        author_tag = byline.find("a", href=True)
        if not author_tag:
            return None
        
        author_name = clean_author_name(author_tag.text.strip())
        author_url = urljoin(BASE_URL, author_tag["href"])
        
        return {
            "article_url": article_url,
            "article_title": title,
            "author_name": author_name,
            "author_url": author_url
        }
        
    except Exception as e:
        safe_log(log_callback, f"Error processing {article_url}: {e}", "error")
        return None

# ---------------- AUTHOR DETAILS FROM PROFILE ----------------

def extract_author_details(author_url, author_name, log_callback=None):
    """Extract detailed author information from profile page"""
    
    cache_key = author_url.lower()
    if cache_key in _author_cache:
        return _author_cache[cache_key]
    
    try:
        html = fetch_url(author_url, log_callback)
        if not html:
            return None
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract job title
        job_title_tag = soup.find("div", class_="AuthorLead-jobTitle")
        job_title = job_title_tag.text.strip() if job_title_tag else ""
        
        # Extract biography
        bio_tag = soup.find("div", class_="AuthorLead-biography")
        biography = bio_tag.text.strip() if bio_tag else ""
        
        # Extract social links and email
        twitter = ""
        email = ""
        
        social_links = soup.find_all("a", class_="SocialLink")
        
        for link in social_links:
            href = link.get("href", "").strip()
            
            # Check for Twitter
            if "twitter.com" in href or "x.com" in href:
                twitter = href
            
            # Check for data-social-service attribute
            social_service = link.get("data-social-service", "")
            if social_service == "mailto" and not email:
                if href.startswith("mailto:"):
                    email = href.replace("mailto:", "").strip()
                elif "/cdn-cgi/l/email-protection" in href:
                    if "#" in href:
                        encoded = href.split("#")[-1]
                        email = decode_cf_email(encoded)
        
        # If email still not found, try full page extraction
        if not email:
            email = extract_email_from_page(soup, log_callback)
        
        author_data = {
            "name": author_name,
            "url": author_url,
            "title": job_title,
            "bio": biography,
            "twitter": twitter,
            "email": email,
            "profile_image": ""
        }
        
        # Try to find profile image
        img_tag = soup.find("img", class_="Image")
        if img_tag and img_tag.get("src"):
            author_data["profile_image"] = urljoin(BASE_URL, img_tag["src"])
        
        # Cache the result
        _author_cache[cache_key] = author_data
        return author_data
        
    except Exception as e:
        safe_log(log_callback, f"Author scrape error: {e}", "error")
        return None

# ---------------- FAST BATCH ARTICLE PROCESSING ----------------

def process_articles_batch(articles, max_threads=10, log_callback=None):
    """Process multiple articles in parallel to get article info"""
    if not articles:
        return []
    
    article_info = []
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(extract_article_info, article["link"], log_callback)
            for article in articles
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                article_info.append(result)
                safe_log(log_callback, f"Processed article: {result['article_title'][:50]}...", "debug")
    
    return article_info

# ---------------- UNIQUE AUTHORS WITH CACHE ----------------

def extract_unique_authors(article_info, log_callback=None):
    """Extract unique authors from article info"""
    unique_authors = {}
    
    for info in article_info:
        if info and info.get("author_url"):
            author_url = info["author_url"]
            if author_url not in unique_authors:
                unique_authors[author_url] = {
                    "Author Name": info["author_name"],
                    "Profile URL": author_url,
                    "Articles": []
                }
            # Add article to author's articles
            unique_authors[author_url]["Articles"].append({
                "title": info["article_title"],
                "url": info["article_url"]
            })
    
    safe_log(log_callback, f"Unique authors found: {len(unique_authors)}", "success")
    return list(unique_authors.values())

# ---------------- AUTHOR DETAILS ENRICHMENT ----------------

def enrich_author_details(author_data, log_callback=None):
    """Enrich author data with profile details"""
    
    # Extract profile details
    profile = extract_author_details(
        author_data["Profile URL"], 
        author_data["Author Name"], 
        log_callback
    )
    
    if profile:
        enriched = {
            "Author Name": profile["name"],
            "Job Title": profile["title"],
            "Biography": profile["bio"],
            "Profile URL": profile["url"],
            "Twitter": profile["twitter"],
            "Email": profile["email"],
            "Profile Image": profile["profile_image"],
            "Article Count": len(author_data.get("Articles", [])),
            "Publication Name": "AP News"
        }
        
        # Add first article title as sample
        if author_data.get("Articles") and len(author_data["Articles"]) > 0:
            enriched["Sample Article"] = author_data["Articles"][0]["title"]
        
        return enriched
    else:
        # Return basic info if profile extraction failed
        return {
            "Author Name": author_data["Author Name"],
            "Profile URL": author_data["Profile URL"],
            "Job Title": "",
            "Biography": "",
            "Twitter": "",
            "Email": "",
            "Profile Image": "",
            "Article Count": len(author_data.get("Articles", [])),
            "Publication Name": "AP News"
        }

# ---------------- MAIN SCRAPER FUNCTION ----------------

def scrape_authors_directly(category_url=POLITICS_URL, max_threads=10, log_callback=None):
    """
    Main function to scrape authors from AP News
    
    Args:
        category_url: Category URL to scrape (default: Politics)
        max_threads: Number of concurrent threads
        log_callback: Logging callback function
    
    Returns:
        List of author data dictionaries
    """
    safe_log(log_callback, f"Starting AP News scraper for {category_url}", "info")
    
    # Step 1: Scrape article links
    articles = scrape_articles(category_url, log_callback)
    if not articles:
        safe_log(log_callback, "No articles found", "warning")
        return []
    
    # Step 2: Process articles to get author info
    article_info = process_articles_batch(articles, max_threads, log_callback)
    
    # Step 3: Extract unique authors
    unique_authors = extract_unique_authors(article_info, log_callback)
    
    # Step 4: Enrich author data with profile details
    enriched_authors = []
    
    # Process authors in batches to avoid overwhelming
    batch_size = 10
    for i in range(0, len(unique_authors), batch_size):
        batch = unique_authors[i:i+batch_size]
        safe_log(log_callback, f"Author batch {i//batch_size + 1}/{(len(unique_authors)-1)//batch_size + 1}", "progress")
        
        for author in batch:
            enriched = enrich_author_details(author, log_callback)
            enriched_authors.append(enriched)
            safe_log(log_callback, f"Enriched: {author['Author Name']}", "debug")
        
        # Small delay between batches
        if i + batch_size < len(unique_authors):
            time.sleep(random.uniform(0.5, 1.0))
    
    safe_log(log_callback, f"Final authors scraped: {len(enriched_authors)}", "success")
    return enriched_authors

# ---------------- COMPATIBILITY FUNCTION ----------------

def scrape_authors_from_articles(articles, max_threads=10, log_callback=None):
    """
    Compatibility function to scrape authors from a list of articles
    """
    article_info = process_articles_batch(articles, max_threads, log_callback)
    unique_authors = extract_unique_authors(article_info, log_callback)
    
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

# ---------------- MULTI-CATEGORY SCRAPER ----------------

def scrape_multiple_categories(category_urls, max_threads=10, log_callback=None):
    """
    Scrape authors from multiple AP News categories
    
    Args:
        category_urls: List of category URLs
        max_threads: Maximum concurrent threads
        log_callback: Logging function
    
    Returns:
        Combined list of author data dictionaries
    """
    all_authors = []
    all_articles = []
    
    for url in category_urls:
        safe_log(log_callback, f"Processing category: {url}", "info")
        articles = scrape_articles(url, log_callback)
        all_articles.extend(articles)
    
    if all_articles:
        all_authors = scrape_authors_from_articles(all_articles, max_threads, log_callback)
    
    return all_authors
