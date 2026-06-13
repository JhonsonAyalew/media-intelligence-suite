# main_scraper.py
import tkinter as tk
from ui.scraper_ui import ScraperApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
