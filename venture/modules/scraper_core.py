# modules/scraper_core.py — VERGE SCRAPER (FIXED + SAFE LOGGING + FAST + AUTHOR DATA)

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


# ---------------- ARTICLE SCRAPING ----------------

def extract_article_info(card, log_callback=None):
    try:
        title_elem = card.find("a", class_=re.compile(r"_1lkmsmo0"))
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        link = urljoin("https://www.theverge.com", title_elem.get("href", ""))

        author_elem = card.find("span", class_=re.compile(r"_1lldluw2"))
        author = clean_author_name(author_elem.get_text(strip=True) if author_elem else "Unknown")

        return {
            "title": title,
            "link": link,
            "author": author,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        safe_log(log_callback, f"Article extraction error: {e}", "warning")
        return None


# ---------------- CATEGORY + ARCHIVE ----------------

def scrape_articles(category, url, max_pages, log_callback=None):
    articles = []

    # -------- MAIN CATEGORY PAGE --------
    safe_log(log_callback, f"[{category}] Scraping main category", "info")

    try:
        response = session.get(url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.find_all("div", class_=re.compile(r"duet--content-cards--content-card|_1ufh7nr1"))

        for card in cards:
            article = extract_article_info(card, log_callback)
            if article:
                article["category"] = category
                articles.append(article)

        safe_log(log_callback, f"[{category}] Main page articles: {len(articles)}", "success")

    except Exception as e:
        safe_log(log_callback, f"[{category}] Main page error: {e}", "error")

    # -------- ARCHIVE PAGES --------
    if max_pages >= 2:
        base_archive_url = "https://www.theverge.com/tech/archives"

        for page in range(1, max_pages):
            try:
                page_url = f"{base_archive_url}/{page}"
                safe_log(log_callback, f"[{category}] Archive page {page}", "progress")

                time.sleep(random.uniform(0.5, 1.2))
                response = session.get(page_url, timeout=15)
                soup = BeautifulSoup(response.text, "html.parser")

                cards = soup.find_all("div", class_=re.compile(r"duet--content-cards--content-card|_1ufh7nr1"))

                for card in cards:
                    article = extract_article_info(card, log_callback)
                    if article:
                        article["category"] = category
                        articles.append(article)

            except Exception as e:
                safe_log(log_callback, f"Archive error: {e}", "error")

    safe_log(log_callback, f"[{category}] TOTAL ARTICLES: {len(articles)}", "success")
    return articles


# ---------------- AUTHOR URL FROM ARTICLE ----------------

def find_author_url_from_article(soup):
    links = soup.find_all("a", href=re.compile(r"/authors/"))
    for link in links:
        href = link.get("href", "")
        if "/authors/" in href and not href.endswith("/rss"):
            return urljoin("https://www.theverge.com", href)
    return None


def extract_author_url_from_article(article_url, author_name, log_callback=None):
    try:
        response = session.get(article_url, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        author_url = find_author_url_from_article(soup)
        if author_url:
            return (author_name, author_url)

    except Exception:
        pass

    return None


# ---------------- AUTHOR DETAILS (RICH DATA) ----------------

def extract_author_details_from_page(author_url, author_name, log_callback=None):

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
            "bluesky": "",
            "linkedin": "",
            "rss": "",
            "bio": "",
            "profile_image": ""
        }

        # title
        h2 = soup.find("h2")
        if h2:
            author_data["title"] = h2.get_text(strip=True)

        # bio
        p = soup.find("p")
        if p:
            author_data["bio"] = p.get_text(strip=True)

        # image
        img = soup.find("img")
        if img and img.get("src"):
            author_data["profile_image"] = img["src"]

        # email
        mailto = soup.find("a", href=re.compile(r"mailto:"))
        if mailto:
            author_data["email"] = mailto["href"].replace("mailto:", "")

        # linkedin
        linkedin = soup.find("a", href=re.compile("linkedin.com"))
        if linkedin:
            author_data["linkedin"] = linkedin["href"]

        # bluesky
        bluesky = soup.find("a", href=re.compile("bsky.app"))
        if bluesky:
            author_data["bluesky"] = bluesky["href"]

        # rss
        rss = soup.find("a", href=re.compile("rss|feed"))
        if rss:
            author_data["rss"] = rss["href"]

        _author_cache[author_url.lower()] = author_data
        return author_data

    except Exception as e:
        safe_log(log_callback, f"Author scrape error: {e}", "error")
        return None


# ---------------- FAST BATCH AUTHOR SCRAPER ----------------

def scrape_authors_from_articles(articles, max_threads=8, log_callback=None):

    if not articles:
        return []

    unique_links = list(set(a["link"] for a in articles if a.get("link")))
    safe_log(log_callback, f"Processing {len(unique_links)} articles", "info")

    author_urls = {}

    # get author urls
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(extract_author_url_from_article, a["link"], a["author"], log_callback)
            for a in articles
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                name, url = result
                author_urls[url] = name

    safe_log(log_callback, f"Found {len(author_urls)} unique authors", "success")

    results = []
    author_items = list(author_urls.items())
    batch_size = 10

    for i in range(0, len(author_items), batch_size):
        batch = author_items[i:i+batch_size]
        safe_log(log_callback, f"Author batch {i//batch_size+1}", "progress")

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
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
                        "Bluesky": author["bluesky"],
                        "LinkedIn": author["linkedin"],
                        "RSS Feed": author["rss"],
                        "Biography": author["bio"],
                        "Profile Image": author["profile_image"],
                        "Publication Name": "The Verge"
                    })

    safe_log(log_callback, f"Authors scraped: {len(results)}", "success")
    return results


# ---------------- ENTRY ----------------

def scrape_authors_directly(section_url, max_pages=3, max_threads=8, log_callback=None):
    safe_log(log_callback, "Starting Verge scraper", "info")

    articles = scrape_articles("Tech", section_url, max_pages, log_callback)
    if not articles:
        return []

    return scrape_authors_from_articles(articles, max_threads, log_callback)


def clear_scraper_cache():
    _author_cache.clear()