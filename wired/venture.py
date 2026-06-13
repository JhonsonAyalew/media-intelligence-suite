import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

BASE_API = "https://venturebeat.com/api/article/byCategories"
BASE_SITE = "https://venturebeat.com"


class VentureBeatScraper:

    def __init__(self, root):
        self.root = root
        root.title("VentureBeat Author Scraper (Fast)")
        root.geometry("1300x700")

        # ---------- INPUT ----------
        frame = tk.Frame(root)
        frame.pack(fill="x", padx=10, pady=5)

        tk.Label(frame, text="Category:").pack(side="left")

        self.category_entry = tk.Entry(frame, width=20)
        self.category_entry.insert(0, "Data")
        self.category_entry.pack(side="left", padx=5)

        tk.Label(frame, text="Page:").pack(side="left")

        self.page_entry = tk.Entry(frame, width=5)
        self.page_entry.insert(0, "1")
        self.page_entry.pack(side="left", padx=5)

        tk.Button(frame, text="Start Scraping", command=self.start).pack(side="left", padx=10)

        # ---------- TABLE ----------
        columns = (
            "article",
            "author",
            "profile",
            "role",
            "email",
            "twitter",
            "linkedin"
        )

        self.tree = ttk.Treeview(root, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=180)

        self.tree.column("article", width=320)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # ---------- LOGS ----------
        tk.Label(root, text="Logs").pack()
        self.log_box = scrolledtext.ScrolledText(root, height=10)
        self.log_box.pack(fill="both", padx=10, pady=5)

    # ---------- LOGGER ----------
    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.root.update()

    # ---------- FETCH ----------
    def fetch(self, url):
        return requests.get(url, headers=HEADERS, timeout=15).text

    # ---------- CLEAR TABLE ----------
    def clear_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def add_row(self, data):
        self.tree.insert("", "end", values=data)

    # ---------- EMAIL ----------
    def extract_email(self, text):
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", text)
        return match.group(0) if match else ""

    # ---------- GET ARTICLES FROM API ----------
    def get_articles(self, category, page):
        self.log("Fetching article list from API...")

        limit = 12
        skip = (page - 1) * limit

        params = {
            "categories": category,
            "limit": limit,
            "skip": skip
        }

        r = requests.get(BASE_API, headers=HEADERS, params=params)
        data = r.json()

        articles = data.get("articles") or data.get("data") or []

        links = []

        for item in articles:
            url = item.get("url") or item.get("link") or ""
            if url:
                if not url.startswith("http"):
                    url = urljoin(BASE_SITE, url)
                links.append(url)

        self.log(f"Found {len(links)} articles")
        return links

    # ---------- SCRAPE ONE ARTICLE ----------
    def process_article(self, article_url):
        try:
            html = self.fetch(article_url)
            soup = BeautifulSoup(html, "html.parser")

            # author link
            author_tag = soup.select_one("address a[href*='/author/']")
            if not author_tag:
                return (article_url, "No Author", "", "", "", "", "")

            author_name = author_tag.get_text(strip=True)
            profile_url = urljoin(BASE_SITE, author_tag["href"])

            # open author profile
            profile_html = self.fetch(profile_url)
            psoup = BeautifulSoup(profile_html, "html.parser")

            # author role/title
            role_tag = psoup.select_one("h1 + p")
            role = role_tag.get_text(strip=True) if role_tag else ""

            text_all = psoup.get_text(" ", strip=True)
            email = self.extract_email(text_all)

            twitter = ""
            linkedin = ""

            # social links
            for a in psoup.select("a[href]"):
                href = a["href"]

                if "twitter.com" in href or "x.com" in href:
                    twitter = href

                if "linkedin.com" in href:
                    linkedin = href

            return (
                article_url,
                author_name,
                profile_url,
                role,
                email,
                twitter,
                linkedin
            )

        except Exception as e:
            return (article_url, "ERROR", "", "", "", "", "")

    # ---------- MAIN ----------
    def start(self):
        self.clear_table()

        category = self.category_entry.get().strip()
        page = int(self.page_entry.get().strip())

        if not category:
            self.log("Enter category")
            return

        self.log("Starting fast batch scraping...\n")

        article_links = self.get_articles(category, page)

        self.log("Processing articles in parallel...\n")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.process_article, link) for link in article_links]

            for future in as_completed(futures):
                result = future.result()
                self.add_row(result)
                self.log(f"Done: {result[1]}")

        self.log("\nFinished!")


# ---------- RUN ----------
root = tk.Tk()
app = VentureBeatScraper(root)
root.mainloop()