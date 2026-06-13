# modules/scraper_core.py — WIRED SCRAPER (FIXED + SAFE LOGGING + FAST + AUTHOR DATA)

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


# ---------------- HELPERS ----------------

def clean_author_name(name):
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"^by\s+", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def extract_email(text):
    """Extract email from text using regex"""
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", text)
    return match.group(0) if match else ""


# ---------------- ARTICLE SCRAPING ----------------

def extract_article_info(card, log_callback=None):
    try:
        title_elem = card.find("a", class_="summary-item__hed-link")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        link = urljoin("https://www.wired.com", title_elem.get("href", ""))

        # Author name is usually in the byline - not directly in the card
        # We'll get it from the article page later
        author = "Unknown"  # Placeholder, will be updated when processing article

        return {
            "title": title,
            "link": link,
            "author": author,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        safe_log(log_callback, f"Article extraction error: {e}", "warning")
        return None


# ---------------- CATEGORY PAGES ----------------

def scrape_articles(category_url, max_pages=1, log_callback=None):
    """
    Scrape articles from a WIRED category URL
    
    Args:
        category_url: Full URL to the category page (e.g., https://www.wired.com/category/politics/)
        max_pages: Number of pages to scrape (WIRED uses infinite scroll, but we'll just get first page)
        log_callback: Logging function
    
    Returns:
        List of article dictionaries
    """
    articles = []

    safe_log(log_callback, f"Scraping category: {category_url}", "info")

    try:
        response = session.get(category_url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all article cards - WIRED uses summary-item class
        cards = soup.find_all("div", class_="summary-item")

        for card in cards:
            article = extract_article_info(card, log_callback)
            if article:
                articles.append(article)

        safe_log(log_callback, f"Found {len(articles)} articles on page", "success")

    except Exception as e:
        safe_log(log_callback, f"Category page error: {e}", "error")

    # Note: WIRED uses infinite scroll/pagination via JavaScript
    # For simplicity, we're only scraping the first page
    # Advanced pagination would require handling their API or scrolling

    safe_log(log_callback, f"TOTAL ARTICLES: {len(articles)}", "success")
    return articles


# ---------------- AUTHOR URL FROM ARTICLE ----------------

def find_author_url_from_article(soup):
    """Find author profile URL in article page"""
    author_link = soup.select_one("a.byline__name-link")
    if author_link and author_link.get("href"):
        return urljoin("https://www.wired.com", author_link["href"])
    return None


def extract_author_name_from_article(soup):
    """Extract author name from article page"""
    author_tag = soup.select_one("a.byline__name-link")
    if author_tag:
        return clean_author_name(author_tag.get_text(strip=True))
    return None


def extract_author_url_from_article(article_url, author_name=None, log_callback=None):
    """Extract author profile URL from an article page"""
    try:
        response = session.get(article_url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        author_url = find_author_url_from_article(soup)
        actual_author_name = extract_author_name_from_article(soup) or author_name or "Unknown"

        if author_url:
            return (actual_author_name, author_url)

    except Exception as e:
        safe_log(log_callback, f"Error extracting author from {article_url}: {e}", "debug")

    return None


# ---------------- AUTHOR DETAILS (RICH DATA) ----------------

def extract_author_details_from_page(author_url, author_name, log_callback=None):
    """Extract detailed author information from profile page"""

    if author_url.lower() in _author_cache:
        return _author_cache[author_url.lower()]

    try:
        safe_log(log_callback, f"Fetching author: {author_name}", "debug")

        response = session.get(author_url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        author_data = {
            "name": author_name,
            "url": author_url,
            "title": "",
            "email": "",
            "twitter": "",
            "linkedin": "",
            "bio": "",
            "profile_image": ""
        }

        # Author title/role
        title_tag = soup.select_one('[data-testid="ContributorHeaderTitle"]')
        if title_tag:
            author_data["title"] = title_tag.get_text(strip=True)

        # Bio text
        bio_tag = soup.select_one('[data-testid="ContributorHeaderBio"]')
        if bio_tag:
            bio_text = bio_tag.get_text(" ", strip=True)
            author_data["bio"] = bio_text
            # Try to extract email from bio
            email = extract_email(bio_text)
            if email:
                author_data["email"] = email

        # Profile image
        img_tag = soup.find("img", class_="contributor__image")
        if img_tag and img_tag.get("src"):
            author_data["profile_image"] = img_tag["src"]

        # Look for social links in the page
        all_links = soup.find_all("a", href=True)
        for link in all_links:
            href = link["href"]
            if "twitter.com" in href or "x.com" in href:
                author_data["twitter"] = href
            elif "linkedin.com" in href:
                author_data["linkedin"] = href
            elif "mailto:" in href and not author_data["email"]:
                author_data["email"] = href.replace("mailto:", "")

        # Cache the result
        _author_cache[author_url.lower()] = author_data
        return author_data

    except Exception as e:
        safe_log(log_callback, f"Author scrape error: {e}", "error")
        return None


# ---------------- FAST BATCH AUTHOR SCRAPER ----------------

def scrape_authors_from_articles(articles, max_threads=8, log_callback=None):
    """
    Extract author information from a list of articles
    
    Args:
        articles: List of article dictionaries (must have 'link' field)
        max_threads: Maximum number of concurrent threads
        log_callback: Logging function
    
    Returns:
        List of author data dictionaries
    """

    if not articles:
        return []

    unique_links = list(set(a["link"] for a in articles if a.get("link")))
    safe_log(log_callback, f"Processing {len(unique_links)} articles", "info")

    author_urls = {}  # url -> name

    # Step 1: Get author profile URLs from each article
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(extract_author_url_from_article, link, None, log_callback)
            for link in unique_links
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                name, url = result
                if url not in author_urls:  # Keep first occurrence
                    author_urls[url] = name

    safe_log(log_callback, f"Found {len(author_urls)} unique authors", "success")

    if not author_urls:
        return []

    # Step 2: Scrape details for each unique author
    results = []
    author_items = list(author_urls.items())
    batch_size = 10  # Process authors in batches to avoid overwhelming

    for i in range(0, len(author_items), batch_size):
        batch = author_items[i:i+batch_size]
        safe_log(log_callback, f"Author batch {i//batch_size + 1}/{(len(author_items)-1)//batch_size + 1}", "progress")

        with ThreadPoolExecutor(max_workers=min(max_threads, len(batch))) as executor:
            futures = [
                executor.submit(extract_author_details_from_page, url, name, log_callback)
                for url, name in batch
            ]

            for future in as_completed(futures):
                author = future.result()
                if author:
                    results.append({
                        "Author Name": author["name"],
                        "Title": author["title"],
                        "Profile URL": author["url"],
                        "Email": author["email"],
                        "Twitter": author["twitter"],
                        "LinkedIn": author["linkedin"],
                        "Biography": author["bio"],
                        "Profile Image": author["profile_image"],
                        "Publication Name": "WIRED"
                    })

        # Small delay between batches
        if i + batch_size < len(author_items):
            time.sleep(random.uniform(0.5, 1.0))

    safe_log(log_callback, f"Authors scraped: {len(results)}", "success")
    return results


# ---------------- ENTRY POINTS ----------------

def scrape_authors_directly(category_url, max_pages=1, max_threads=8, log_callback=None):
    """
    Main entry point - scrape authors from a WIRED category
    
    Args:
        category_url: Full URL to the category page
        max_pages: Number of pages to scrape (WIRED typically only needs 1)
        max_threads: Maximum concurrent threads
        log_callback: Logging function
    
    Returns:
        List of author data dictionaries
    """
    safe_log(log_callback, "Starting WIRED scraper", "info")

    articles = scrape_articles(category_url, max_pages, log_callback)
    if not articles:
        safe_log(log_callback, "No articles found", "warning")
        return []

    return scrape_authors_from_articles(articles, max_threads, log_callback)


def scrape_from_multiple_categories(category_urls, max_pages=1, max_threads=8, log_callback=None):
    """
    Scrape authors from multiple WIRED categories
    
    Args:
        category_urls: List of category URLs
        max_pages: Number of pages per category
        max_threads: Maximum concurrent threads
        log_callback: Logging function
    
    Returns:
        Combined list of author data dictionaries
    """
    all_authors = []
    all_articles = []

    for url in category_urls:
        safe_log(log_callback, f"Processing category: {url}", "info")
        articles = scrape_articles(url, max_pages, log_callback)
        all_articles.extend(articles)

    if all_articles:
        all_authors = scrape_authors_from_articles(all_articles, max_threads, log_callback)

    return all_authors


def clear_scraper_cache():
    """Clear the author cache"""
    global _author_cache
    _author_cache.clear()
