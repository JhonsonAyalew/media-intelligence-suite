# ui/scraper_ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import threading
from datetime import datetime
import pandas as pd
import os
import json
import shutil
import sys


# Import modules
from modules import scraper_core, enhancer_core, sheets_manager, config_manager
from modules.config_manager import ConfigManager


class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Business Insider Pro Scraper + Enhancer")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.config = ConfigManager.load_scraper_config()
        
        # Initialize categories and cat_vars BEFORE building UI
        self.categories = {}
        self.cat_vars = {}  # Initialize cat_vars dictionary here
        
        # Load credentials from settings - DO THIS FIRST
        self.google_creds = self.load_google_credentials()
        
        # Clear any existing environment variable initially
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        
        # Set environment variable if credentials exist
        if self.google_creds and os.path.exists(self.google_creds):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.google_creds
        
        # Initialize sheets manager
        self.sheets_manager = None
        self.sheets_connected = False
        self.initialize_sheets_manager()
        
        # Data storage
        self.articles = []
        self.authors = []
        self.enhanced_authors = []
        self.combined = []
        self.current_sheet_data = {}
        self.selected_sheet = None
        
        # Build UI
        self.build_ui()
        
        # Update status
        self.update_sheets_status()
        
        # Auto-load sheet name from settings
        self.auto_load_settings()
    
    def auto_load_settings(self):
        """Auto-load settings when app starts"""
        try:
            if os.path.exists("data/config.json"):
                with open("data/config.json", 'r') as f:
                    config = json.load(f)
                    sheet_name = config.get('sheet_name')
                    if sheet_name:
                        self.sheet_name_var.set(sheet_name)
                        self.log(f"✓ Auto-loaded sheet name from settings: {sheet_name}", "info")
        except Exception as e:
            print(f"Auto-load settings error: {e}")
    
    def initialize_sheets_manager(self):
        """Initialize Google Sheets manager with proper scopes"""
        try:
            # Only initialize if credentials exist
            if self.google_creds and os.path.exists(self.google_creds):
                self.sheets_manager = sheets_manager.GoogleSheetsManager(self.google_creds)
                self.sheets_connected = self.sheets_manager.connect()
                if self.sheets_connected:
                    print(f"✓ Google Sheets initialized successfully")
                else:
                    print("✗ Google Sheets connection failed")
                return self.sheets_connected
            else:
                self.sheets_manager = None
                self.sheets_connected = False
                print("No Google credentials found")
                return False
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            self.sheets_manager = None
            self.sheets_connected = False
            return False
    
    def load_google_credentials(self):
        """Load Google credentials from settings file"""
        try:
            config_file = "data/config.json"
            if not os.path.exists(config_file):
                return None
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check for credentials in config
            creds_file = config.get('google_creds_file')
            if creds_file and os.path.exists(creds_file):
                return creds_file
            
            # Also check for default location
            default_creds = "data/google_credentials.json"
            if os.path.exists(default_creds):
                return default_creds
            
            return None
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None
    
    def update_sheets_status(self):
        """Update Google Sheets connection status"""
        if hasattr(self, 'sheets_status_label'):
            if self.sheets_connected:
                self.sheets_status_label.config(text="✓ Google Sheets: Connected", foreground="green")
            else:
                self.sheets_status_label.config(text="✗ Google Sheets: Not configured - Click Settings", foreground="red")
    
    def log(self, msg: str, tag: str = "info"):
        """Log message to console"""
        colors = {
            "info": "#00e5ff",
            "success": "#00ff7f",
            "error": "#ff5252",
            "progress": "#ffee58",
            "warning": "#ff9800"
        }
        self.console.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n", tag)
        self.console.tag_config(tag, foreground=colors[tag])
        self.console.see("end")
    
    def build_ui(self):
        """Build the scraper GUI"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Top Control Frame
        top_frame = ttk.LabelFrame(main_container, text="Controls")
        top_frame.pack(fill="x", pady=(0, 5))
        
        # Row 1: Scraping Controls
        row1 = ttk.Frame(top_frame)
        row1.pack(fill="x", pady=5)
        
        self.pages_var = tk.IntVar(value=2)
        self.threads_var = tk.IntVar(value=6)
        
        # Create a frame for the title with background
        title_frame = tk.Frame(row1, bg="#f0f8ff")  # Light blue background
        title_frame.pack(side="left", padx=(0, 20), pady=3)
        
        title_label = tk.Label(
            title_frame,
            text="📊 Business Insider Pro Scraper",
            font=("Arial", 14, "bold"),
            fg="#0066cc",  # Blue text
            bg="#f0f8ff",  # Light blue background
            padx=10,
            pady=5
        )
        title_label.pack()
        
        # Add pages and threads entries back
        controls_frame = ttk.Frame(row1)
        controls_frame.pack(side="left", padx=10)
        
        ttk.Label(controls_frame, text="Pages:").pack(side="left")
        ttk.Entry(controls_frame, textvariable=self.pages_var, width=5).pack(side="left", padx=(5, 15))
        
        ttk.Label(controls_frame, text="Threads:").pack(side="left")
        ttk.Entry(controls_frame, textvariable=self.threads_var, width=5).pack(side="left", padx=(5, 15))
        
        ttk.Button(row1, text="Scrape Articles", command=self.start_articles).pack(side="left", padx=5)
        ttk.Button(row1, text="Scrape Authors", command=self.start_authors).pack(side="left", padx=5)
        ttk.Button(row1, text="Clear All Data", command=self.clear_data).pack(side="left", padx=5)
        
        # Row 2: Category Selection Frame
        row2 = ttk.Frame(top_frame)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Main Category:").pack(side="left")
        
        # Main category dropdown
        self.main_cat_var = tk.StringVar()
        self.main_cat_dropdown = ttk.Combobox(row2, textvariable=self.main_cat_var, width=15, state="readonly")
        self.main_cat_dropdown.pack(side="left", padx=(5, 15))
        self.main_cat_dropdown.bind('<<ComboboxSelected>>', self.on_main_category_selected)
        
        # "Select All" button
        self.select_all_var = tk.BooleanVar(value=False)
        self.select_all_btn = ttk.Checkbutton(row2, text="Select All", 
                                             variable=self.select_all_var,
                                             command=self.toggle_select_all)
        self.select_all_btn.pack(side="left", padx=(0, 15))
        
        # Subcategories frame (will be populated dynamically)
        self.subcat_frame = ttk.Frame(top_frame)
        self.subcat_frame.pack(fill="x", pady=5)
        
        # Initialize categories
        self.initialize_categories()
        
        # Google Sheets Frame
        sheets_frame = ttk.LabelFrame(main_container, text="Google Sheets")
        sheets_frame.pack(fill="x", pady=(0, 5))
        
        sheets_row = ttk.Frame(sheets_frame)
        sheets_row.pack(fill="x", pady=5)
        
        # Sheet selection
        ttk.Label(sheets_row, text="Sheet:").pack(side="left")
        self.sheet_name_var = tk.StringVar(value="business-insider-authors")
        
        self.sheet_box = ttk.Combobox(sheets_row, textvariable=self.sheet_name_var, width=30)
        self.sheet_box.pack(side="left", padx=5)
        
        ttk.Button(sheets_row, text="Load Sheets", command=self.load_sheets).pack(side="left", padx=5)
        
        # Settings button
        ttk.Button(sheets_row, text="⚙️ Settings", 
                  command=self.open_settings, width=12).pack(side="right", padx=5)
        
        # Sheet Actions
        actions_row = ttk.Frame(sheets_frame)
        actions_row.pack(fill="x", pady=5)
        
        ttk.Button(actions_row, text="Upload Articles", command=self.upload_articles).pack(side="left", padx=5)
        ttk.Button(actions_row, text="Upload Authors", command=self.upload_authors).pack(side="left", padx=5)
        ttk.Button(actions_row, text="Upload Enhanced", command=self.upload_enhanced).pack(side="left", padx=5)
        ttk.Button(actions_row, text="Save Enhanced", command=self.save_enhanced_to_sheet).pack(side="left", padx=5)
        ttk.Button(actions_row, text="Load All Data", command=self.load_all_sheet_data).pack(side="left", padx=5)
        
        # Status indicator for Google Sheets
        self.sheets_status_label = ttk.Label(sheets_frame, text="")
        self.sheets_status_label.pack(pady=5)
        
        # Middle Section: Console
        console_frame = ttk.LabelFrame(main_container, text="Log Output")
        console_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        self.console = ScrolledText(console_frame, bg="#0b0f14", fg="#00ff7f", height=10)
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bottom Section: Enhancement Tools WITH SCROLLBAR
        enh_frame = ttk.LabelFrame(main_container, text="Enhancement Tools")
        enh_frame.pack(fill="both", expand=True)
        
        # Create a container frame with scrollbar
        enh_container = ttk.Frame(enh_frame)
        enh_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(enh_container)
        scrollbar = ttk.Scrollbar(enh_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scroll region
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create window in canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create two columns inside scrollable frame
        left_column = ttk.Frame(scrollable_frame)
        left_column.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        right_column = ttk.Frame(scrollable_frame)
        right_column.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # LEFT COLUMN: Data Processing
        left_frame = ttk.LabelFrame(left_column, text="Data Processing")
        left_frame.pack(fill="both", expand=True, pady=5)
        
        left_grid = ttk.Frame(left_frame)
        left_grid.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Buttons for left column
        ttk.Button(left_grid, text="Apply All Enhancements", 
                  command=self.apply_enhancements_api, width=25).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(left_grid, text="Load & Enhance Sheet", 
                  command=self.load_and_enhance_sheet, width=25).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(left_grid, text="Deduplication:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(left_grid, text="Articles", 
                  command=self.deduplicate_articles_api, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(left_grid, text="Authors", 
                  command=self.deduplicate_authors_api, width=15).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(left_grid, text="Validation:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(left_grid, text="Link Check", 
                  command=self.validate_relationships_api, width=15).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(left_grid, text="Recency Check", 
                  command=self.check_recency_api, width=15).grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(left_grid, text="Filtering:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(left_grid, text="Low-Signal", 
                  command=self.filter_low_signal_api, width=15).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(left_grid, text="By Status", 
                  command=self.filter_by_status, width=15).grid(row=3, column=2, padx=5, pady=5, sticky="ew")
        
        # Configure grid
        for i in range(3):
            left_grid.columnconfigure(i, weight=1)
        
        # RIGHT COLUMN: Scoring & Analysis
        right_frame = ttk.LabelFrame(right_column, text="Scoring & Analysis")
        right_frame.pack(fill="both", expand=True, pady=5)
        
        right_grid = ttk.Frame(right_frame)
        right_grid.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Buttons for right column
        ttk.Label(right_grid, text="Scoring:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(right_grid, text="Activity", 
                  command=self.calculate_activity_scores_api, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(right_grid, text="Relevance", 
                  command=self.calculate_relevance_scores_api, width=15).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(right_grid, text="Topics:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(right_grid, text="Assign Topics", 
                  command=self.assign_topics_api, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(right_grid, text="Topic Stats", 
                  command=self.show_topic_stats, width=15).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(right_grid, text="Analysis:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(right_grid, text="Statistics", 
                  command=self.show_statistics, width=15).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(right_grid, text="Validation Report", 
                  command=self.generate_report, width=15).grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(right_grid, text="Export:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(right_grid, text="Export CSV", 
                  command=self.export_csv, width=15).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(right_grid, text="Preview Data", 
                  command=self.preview_data, width=15).grid(row=3, column=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(right_grid, text="Quick Actions:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(right_grid, text="Validate All", 
                  command=self.validate_all_api, width=15).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(right_grid, text="Score All", 
                  command=self.score_all_api, width=15).grid(row=4, column=2, padx=5, pady=5, sticky="ew")
        
        # Configure grid
        for i in range(3):
            right_grid.columnconfigure(i, weight=1)
        
        # Add mouse wheel scrolling for better UX
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def initialize_categories(self):
        """Initialize Business Insider categories"""
        self.categories = {
            "Business": [
                "business", "strategy", "economy", "finance", "retail",
                "advertising", "careers", "media", "real-estate", "smallbusiness",
                "the-better-work-project"
            ],
            "Tech": [
                "tech", "science", "artificial-intelligence", "enterprise",
                "transportation", "startups", "innovation"
            ],
            "Market": [
                "markets", "stocks", "indices", "commodities"
            ],
            "Lifestyle": [
                "lifestyle", "entertainment", "culture", "travel",
                "food", "health", "parenting"
            ],
            "Politics": [
                "politics", "defense", "law", "education"
            ]
        }
        
        # Set main categories in dropdown
        self.main_cat_dropdown["values"] = list(self.categories.keys())
        self.main_cat_var.set(list(self.categories.keys())[0])  # Set first as default
        
        # Initialize ALL category variables upfront for all subcategories
        for main_cat, subcats in self.categories.items():
            for subcat in subcats:
                if subcat not in self.cat_vars:
                    self.cat_vars[subcat] = tk.BooleanVar(value=False)
        
        self.on_main_category_selected()  # Trigger to load first category's subcategories
    
    def on_main_category_selected(self, event=None):
        """When a main category is selected, populate subcategories"""
        main_cat = self.main_cat_var.get()
        if not main_cat:
            return
        
        # Clear previous subcategories
        for widget in self.subcat_frame.winfo_children():
            widget.destroy()
        
        # Get subcategories for selected main category
        subcategories = self.categories.get(main_cat, [])
        
        # Create checkbuttons for each subcategory
        for i, subcat in enumerate(subcategories):
            # Create variable for this subcategory if not exists
            if subcat not in self.cat_vars:
                self.cat_vars[subcat] = tk.BooleanVar(value=False)
            
            # Create checkbutton
            cb = ttk.Checkbutton(self.subcat_frame, text=subcat, 
                               variable=self.cat_vars[subcat])
            cb.grid(row=0, column=i, padx=2, pady=2, sticky="w")
    
    def toggle_select_all(self):
        """Toggle selection of all subcategories in current main category"""
        if not self.select_all_var.get():
            # Deselect all
            for var in self.cat_vars.values():
                var.set(False)
            return
        
        # Select all subcategories in current main category
        main_cat = self.main_cat_var.get()
        if main_cat and main_cat in self.categories:
            subcategories = self.categories[main_cat]
            for subcat in subcategories:
                if subcat in self.cat_vars:
                    self.cat_vars[subcat].set(True)
    
    def open_settings(self):
        """Open settings window for Google credentials"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Google Sheets Settings")
        settings_window.geometry("600x650")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center window
        settings_window.update_idletasks()
        w_width = 600
        w_height = 650
        x = (self.root.winfo_screenwidth() // 2) - (w_width // 2)
        y = (self.root.winfo_screenheight() // 2) - (w_height // 2)
        settings_window.geometry(f"{w_width}x{w_height}+{x}+{y}")
        
        # Main frame with padding
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="⚙️ Google Sheets Settings", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Connection Status", padding="10")
        status_frame.pack(fill="x", pady=(0, 15))
        
        status_label = ttk.Label(status_frame, text="Current Status: ")
        status_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Create status value label that we can update
        self.settings_status_value = ttk.Label(status_frame, text="", foreground="red")
        if self.sheets_connected:
            self.settings_status_value.config(text="✓ Connected", foreground="green")
        else:
            self.settings_status_value.config(text="✗ Not Connected", foreground="red")
        self.settings_status_value.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Credentials section
        creds_frame = ttk.LabelFrame(main_frame, text="Google Service Account Credentials", padding="15")
        creds_frame.pack(fill="x", pady=(0, 15))
        
        # JSON file selection
        ttk.Label(creds_frame, text="Service Account JSON File:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.json_file_var = tk.StringVar()
        
        # Load existing file if available
        if self.google_creds and os.path.exists(self.google_creds):
            self.json_file_var.set(self.google_creds)
        
        json_entry = ttk.Entry(creds_frame, textvariable=self.json_file_var, width=50)
        json_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        def browse_json_file():
            filename = filedialog.askopenfilename(
                title="Select Google Service Account JSON File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                self.json_file_var.set(filename)
        
        browse_button = ttk.Button(creds_frame, text="Browse...", command=browse_json_file)
        browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Google Sheet Name
        ttk.Label(creds_frame, text="Google Sheet Name:").grid(
            row=2, column=0, sticky="w", padx=5, pady=10)
        
        self.sheet_name_entry_var = tk.StringVar(value=self.sheet_name_var.get())
        sheet_name_entry = ttk.Entry(creds_frame, textvariable=self.sheet_name_entry_var, width=50)
        sheet_name_entry.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))
        
        # Configure grid weights
        creds_frame.columnconfigure(0, weight=1)
        
        # Test Connection Button - FIXED TO CONNECT MAIN APP AFTER TEST
        def test_connection():
            json_file = self.json_file_var.get()
            sheet_name = self.sheet_name_entry_var.get()
            
            if not json_file:
                messagebox.showerror("Error", "Please select a JSON credentials file")
                return
            
            if not os.path.exists(json_file):
                messagebox.showerror("Error", "JSON file does not exist")
                return
            
            if not sheet_name or not sheet_name.strip():
                messagebox.showerror("Error", "Please enter a Google Sheet name")
                return
            
            try:
                # Test the connection using Google API
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                
                # Scopes needed
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive.readonly'
                ]
                
                # Load credentials
                credentials = service_account.Credentials.from_service_account_file(
                    json_file,
                    scopes=scopes
                )
                
                # Test Google Sheets API
                sheets_service = build('sheets', 'v4', credentials=credentials)
                
                # Test Google Drive API to list sheets
                drive_service = build('drive', 'v3', credentials=credentials)
                results = drive_service.files().list(
                    q="mimeType='application/vnd.google-apps.spreadsheet'",
                    pageSize=10,
                    fields="files(id, name)"
                ).execute()
                sheets = results.get('files', [])
                
                # Check if the specific sheet exists
                sheet_exists = False
                sheet_id = None
                for sheet in sheets:
                    if sheet['name'].lower() == sheet_name.lower():
                        sheet_exists = True
                        sheet_id = sheet['id']
                        break
                
                # Try to access the specific sheet
                if sheet_exists:
                    try:
                        sheet_service = sheets_service.spreadsheets()
                        sheet_info = sheet_service.get(spreadsheetId=sheet_id).execute()
                        sheet_title = sheet_info.get('properties', {}).get('title', 'Unknown')
                        
                        # Check if we can actually read the sheet
                        result = sheet_service.values().get(
                            spreadsheetId=sheet_id,
                            range="A1:A1"
                        ).execute()
                        
                        sheet_access_ok = True
                    except Exception as sheet_error:
                        sheet_access_ok = False
                        access_error = str(sheet_error)
                else:
                    sheet_access_ok = False
                    access_error = f"Sheet '{sheet_name}' not found in your Google Drive"
                
                # IMPORTANT: Update the main app with tested credentials immediately
                # Temporarily set environment variable with tested file
                if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_file
                
                # Try to initialize sheets manager with tested credentials
                try:
                    self.sheets_manager = sheets_manager.GoogleSheetsManager(json_file)
                    self.sheets_connected = self.sheets_manager.connect()
                    self.google_creds = json_file
                    
                    # Update status in both settings window and main window
                    if sheet_exists and sheet_access_ok:
                        self.settings_status_value.config(text="✓ Test Successful", foreground="green")
                        message = (f"✅ Connection successful!\n"
                                  f"Found {len(sheets)} Google Sheets.\n"
                                  f"✅ Sheet '{sheet_title}' exists and is accessible.\n"
                                  f"Main app is now connected!")
                    elif sheet_exists and not sheet_access_ok:
                        self.settings_status_value.config(text="⚠️ Access Issues", foreground="orange")
                        message = (f"⚠️ Partial success\n"
                                  f"Credentials work but cannot access sheet '{sheet_name}'.\n"
                                  f"Error: {access_error}\n\n"
                                  f"Make sure the sheet is shared with the service account email.")
                    else:
                        self.settings_status_value.config(text="✗ Sheet Not Found", foreground="red")
                        message = (f"❌ Sheet not found\n"
                                  f"Credentials work but sheet '{sheet_name}' not found.\n"
                                  f"Available sheets: {', '.join([s['name'] for s in sheets[:3]])}...")
                    
                    messagebox.showinfo("Connection Test", message)
                    self.update_sheets_status()  # Update main window status
                    
                except Exception as e:
                    self.settings_status_value.config(text="✗ App Connect Failed", foreground="red")
                    messagebox.showerror("App Connection Failed", 
                                       f"Test succeeded but app connection failed:\n{str(e)}")
                
            except Exception as e:
                self.settings_status_value.config(text="✗ Test Failed", foreground="red")
                error_msg = str(e)
                if "insufficient authentication scopes" in error_msg.lower():
                    error_msg += "\n\n⚠️ Please ensure your Service Account has both:\n"
                    error_msg += "1. Google Sheets API enabled\n"
                    error_msg += "2. Google Drive API enabled\n"
                    error_msg += "3. The Google Sheet is shared with the service account email"
                messagebox.showerror("Connection Failed", f"❌ Error:\n{error_msg}")
        
        test_button = ttk.Button(main_frame, text="🔌 Test & Connect", 
                               command=test_connection, width=20)
        test_button.pack(pady=10)
        
        # Instructions section
        instructions_frame = ttk.LabelFrame(main_frame, text="Setup Instructions", padding="15")
        instructions_frame.pack(fill="x", pady=(0, 15))
        
        instructions = """1. Go to Google Cloud Console (console.cloud.google.com)
2. Create a new project or select existing
3. Enable both Google Sheets API and Google Drive API
4. Create a Service Account
5. Generate and download JSON key
6. Share your Google Sheet with the Service Account email
7. Select the JSON file above
8. Enter your Google Sheet name
9. Test the connection
10. Save settings"""
        
        instructions_label = ttk.Label(instructions_frame, text=instructions, 
                                      justify="left", font=("Arial", 9))
        instructions_label.pack(anchor="w")
        
        # Buttons frame at the bottom
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=20)
        
        def save_settings():
            json_file = self.json_file_var.get()
            sheet_name = self.sheet_name_entry_var.get()
            
            if not json_file:
                messagebox.showerror("Error", "Please select a JSON credentials file")
                return
            
            if not sheet_name:
                messagebox.showerror("Error", "Please enter a Google Sheet name")
                return
            
            if not os.path.exists(json_file):
                messagebox.showerror("Error", "JSON file does not exist")
                return
            
            try:
                # Ensure data directory exists
                os.makedirs("data", exist_ok=True)
                
                # Copy JSON file to data folder
                dest_file = "data/google_credentials.json"
                shutil.copy2(json_file, dest_file)
                
                # Save config
                config = {}
                try:
                    if os.path.exists("data/config.json"):
                        with open("data/config.json", 'r') as f:
                            config = json.load(f)
                except:
                    config = {}
                
                config.update({
                    "google_creds_file": dest_file,
                    "sheet_name": sheet_name,
                    "smtp_configured": config.get('smtp_configured', False)
                })
                
                with open("data/config.json", 'w') as f:
                    json.dump(config, f, indent=4)
                
                # Update current settings
                self.google_creds = dest_file
                self.sheet_name_var.set(sheet_name)
                
                # Clear and set environment variable
                if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = dest_file
                
                # Reinitialize sheets manager
                success = self.initialize_sheets_manager()
                
                # Update status in both settings window and main window
                if success:
                    self.settings_status_value.config(text="✓ Connected", foreground="green")
                    self.update_sheets_status()  # Update main window status
                    self.log("✅ Google Sheets settings saved and connected", "success")
                    messagebox.showinfo("Success", "✅ Settings saved successfully!\nGoogle Sheets is now connected.")
                    settings_window.destroy()
                else:
                    self.settings_status_value.config(text="✗ Save Failed", foreground="red")
                    messagebox.showerror("Error", "❌ Failed to initialize Google Sheets connection after saving.")
                
            except Exception as e:
                messagebox.showerror("Error", f"❌ Failed to save settings:\n{str(e)}")
        
        def reset_settings():
            """Reset all settings to defaults"""
            result = messagebox.askyesno("Reset Settings", 
                                        "Are you sure you want to reset all Google Sheets settings?\n"
                                        "This will remove your credentials.")
            if result:
                try:
                    # Remove credentials file if it exists
                    creds_file = "data/google_credentials.json"
                    if os.path.exists(creds_file):
                        os.remove(creds_file)
                    
                    # Clear config
                    config = {"smtp_configured": False}
                    with open("data/config.json", 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    # Clear environment variable
                    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                        del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                    
                    # Reset UI
                    self.google_creds = None
                    self.sheet_name_var.set("business-insider-authors")  # Fixed to Business Insider default
                    self.json_file_var.set("")
                    self.sheet_name_entry_var.set("business-insider-authors")  # Fixed to Business Insider default
                    
                    # Reinitialize
                    self.sheets_manager = None
                    self.sheets_connected = False
                    
                    # Update status in both windows
                    self.settings_status_value.config(text="✗ Not Connected", foreground="red")
                    self.update_sheets_status()
                    
                    self.log("Settings reset to defaults", "info")
                    messagebox.showinfo("Reset Complete", "✅ Settings have been reset to defaults.")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to reset: {str(e)}")
        
        # Save button
        save_button = ttk.Button(buttons_frame, text="💾 Save Settings", 
                               command=save_settings, width=20)
        save_button.pack(side="left", padx=(0, 10))
        
        # Reset button
        reset_button = ttk.Button(buttons_frame, text="🔄 Reset", 
                                command=reset_settings, width=15)
        reset_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_button = ttk.Button(buttons_frame, text="Cancel", 
                                 command=settings_window.destroy, width=15)
        cancel_button.pack(side="left")
        
        # Make buttons frame expand
        buttons_frame.columnconfigure(0, weight=1)
    
    # =========================
    # BASIC ACTIONS
    # =========================
    
    def start_articles(self):
        """Start article scraping in background"""
        threading.Thread(target=self.scrape_articles, daemon=True).start()
    
    def scrape_articles(self):
        """Scrape articles from selected categories"""
        self.articles.clear()
        
        # Get all selected subcategories from the UI checkboxes
        selected_categories = []
        for cat_name, var in self.cat_vars.items():
            if var.get():  # Check if the checkbox is checked
                selected_categories.append(cat_name)
        
        if not selected_categories:
            self.log("No categories selected! Please select at least one subcategory.", "error")
            return
        
        self.log(f"Selected {len(selected_categories)} subcategories", "info")
        
        # Get categories from config manager (which now has Business Insider URLs)
        all_categories = ConfigManager.get_categories()
        
        for subcat in selected_categories:
            if subcat in all_categories:
                url = all_categories[subcat]
                self.log(f"Scraping {subcat} from {url}...", "progress")
                
                articles = scraper_core.scrape_articles(
                    subcat, 
                    url, 
                    self.pages_var.get(), 
                    self.log
                )
                self.articles.extend(articles)
                self.log(f"  {subcat}: {len(articles)} articles", "info")
            else:
                self.log(f"  Warning: No URL found for '{subcat}'", "warning")
        
        self.log(f"TOTAL ARTICLES SCRAPED: {len(self.articles)}", "success")
    
    def start_authors(self):
        """Start author scraping in background"""
        threading.Thread(target=self.scrape_authors, daemon=True).start()
    
    def scrape_authors(self):
        """Scrape authors from articles"""
        self.authors = scraper_core.scrape_authors_from_articles(
            self.articles,
            self.threads_var.get(),
            self.log
        )
    
    def clear_data(self):
        """Clear all data"""
        self.articles = []
        self.authors = []
        self.enhanced_authors = []
        self.current_sheet_data = {}
        self.log("All data cleared", "info")
    
    # =========================
    # GOOGLE SHEETS ACTIONS
    # =========================
    
    def load_sheets(self):
        """Load available Google Sheets - using settings credentials"""
        if not self.sheets_manager or not self.sheets_connected:
            self.log("Google Sheets not configured. Click Settings to configure.", "error")
            messagebox.showerror("Error", "Google Sheets not configured. Click Settings to configure credentials.")
            return
        
        try:
            # List all sheets
            sheets = self.sheets_manager.list_sheets()
            
            if not sheets:
                self.log("No Google Sheets found. Please check:", "error")
                self.log("1. Google Sheets API is enabled", "error")
                self.log("2. Sheet is shared with service account", "error")
                self.log("3. Correct credentials file", "error")
                return
            
            self.sheet_box["values"] = sheets
            
            # Auto-select the sheet from settings if it exists
            current_sheet = self.sheet_name_var.get()
            if current_sheet in sheets:
                self.select_sheet()  # Auto-select it
                self.log(f"✓ Auto-selected sheet: {current_sheet}", "success")
            elif sheets:
                self.sheet_name_var.set(sheets[0])  # Select first sheet
                self.select_sheet()
                self.log(f"Loaded {len(sheets)} Google Sheets. Selected: {sheets[0]}", "success")
            else:
                self.log(f"Loaded {len(sheets)} Google Sheets", "success")
                
        except Exception as e:
            self.log(f"Error loading sheets: {str(e)}", "error")
    
    def select_sheet(self):
        """Select a Google Sheet"""
        sheet_name = self.sheet_name_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Enter sheet name")
            return
        
        if not self.sheets_manager or not self.sheets_connected:
            self.log("Google Sheets not configured", "error")
            return
        
        try:
            worksheet_names = self.sheets_manager.get_worksheet_names(sheet_name)
            self.selected_sheet = sheet_name
            self.log(f"✓ Selected sheet: {sheet_name} with {len(worksheet_names)} worksheets", "success")
        except Exception as e:
            if "not found" in str(e).lower():
                self.log(f"❌ Sheet '{sheet_name}' not found. Click 'Load Sheets' to see available sheets.", "error")
            else:
                self.log(f"Error selecting sheet: {str(e)}", "error")
    
    def launch_email_tool(self):
        """Launch the email outreach tool - works in both dev and EXE mode"""
        try:
            # Check if running as EXE or as Python script
            import sys
            if getattr(sys, 'frozen', False):
                # Running as compiled EXE
                # Show message to use the main launcher
                messagebox.showinfo(
                    "Email Outreach", 
                    "The email outreach tool is built into the main application.\n\n"
                    "Please return to the main launcher and click:\n"
                    "📧 Author Outreach Tool"
                )
            else:
                # Running as Python script (development mode)
                import subprocess
                import sys
                import os
                
                # Get the root project directory (one level up from ui/)
                current_dir = os.path.dirname(os.path.abspath(__file__))  # ui folder
                project_root = os.path.dirname(current_dir)  # techcrunch-outreach folder
                email_tool = os.path.join(project_root, "main_outreach.py")
                
                if os.path.exists(email_tool):
                    subprocess.Popen([sys.executable, email_tool])
                    self.log("✓ Email Outreach Tool launched", "success")
                else:
                    messagebox.showinfo("Info", 
                                      "Email outreach tool not found.\nMake sure 'main_outreach.py' is in the project root folder.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not launch: {str(e)}")
    
    def load_all_sheet_data(self):
        """Load all data from selected sheet"""
        sheet_name = self.selected_sheet or self.sheet_name_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Select a sheet first")
            return
        
        if not self.sheets_manager or not self.sheets_connected:
            self.log("Google Sheets not configured", "error")
            return
        
        try:
            # First verify the sheet exists
            try:
                worksheet_names = self.sheets_manager.get_worksheet_names(sheet_name)
            except Exception as e:
                if "not found" in str(e).lower():
                    self.log(f"❌ Sheet '{sheet_name}' not found. Available sheets:", "error")
                    # List available sheets
                    try:
                        available = self.sheets_manager.list_sheets()
                        if available:
                            self.log(f"Available sheets: {', '.join(available[:5])}", "info")
                            if len(available) > 5:
                                self.log(f"... and {len(available)-5} more", "info")
                        else:
                            self.log("No sheets available. Check sharing permissions.", "error")
                    except:
                        pass
                    return
                else:
                    raise e
            
            self.log(f"Loading all data from {sheet_name}...", "progress")
            
            for ws_name in worksheet_names:
                data = self.sheets_manager.load_worksheet(sheet_name, ws_name)
                if data:
                    self.current_sheet_data[ws_name] = data
                    
                    # Auto-detect and load
                    if ws_name.lower() == "articles":
                        self.articles = data
                        self.log(f"  ✅ Loaded {len(data)} articles", "info")
                    elif ws_name.lower() == "authors":
                        self.authors = data
                        self.log(f"  ✅ Loaded {len(data)} authors", "info")
                    elif "enhanced" in ws_name.lower():
                        self.enhanced_authors = data
                        self.log(f"  ✅ Loaded {len(data)} enhanced authors", "info")
                    else:
                        self.log(f"  Loaded {len(data)} records from '{ws_name}'", "info")
            
            if self.current_sheet_data:
                self.log(f"✅ Total worksheets loaded: {len(self.current_sheet_data)}", "success")
            else:
                self.log("⚠️ No data found in worksheets", "warning")
                
        except Exception as e:
            self.log(f"❌ Error loading all data: {str(e)}", "error")
    
    def load_and_enhance_sheet(self):
        """Load data from sheet and apply enhancements"""
        sheet_name = self.selected_sheet or self.sheet_name_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Select a sheet first")
            return
        
        self.log(f"Loading and enhancing data from {sheet_name}...", "progress")
        self.load_all_sheet_data()
        self.apply_enhancements_api()
    
    def save_enhanced_to_sheet(self):
        """Save enhanced data back to Google Sheets"""
        sheet_name = self.selected_sheet or self.sheet_name_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Select a sheet first")
            return
        
        if not self.sheets_manager or not self.sheets_connected:
            self.log("Google Sheets not configured", "error")
            return
        
        if not self.enhanced_authors:
            self.log("No enhanced data to save", "error")
            return
        
        success = self.sheets_manager.upload_enhanced_authors(sheet_name, self.enhanced_authors)
        if success:
            self.log(f"✅ Enhanced data saved to '{sheet_name}' (Enhanced_Authors worksheet)", "success")
        else:
            self.log("❌ Failed to save enhanced data", "error")
    
    def upload_articles(self):
        """Upload articles to Google Sheets"""
        sheet_name = self.selected_sheet or self.sheet_name_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Select or enter sheet name")
            return
        
        if not self.sheets_manager or not self.sheets_connected:
            self.log("Google Sheets not configured", "error")
            return
        
        if not self.articles:
            self.log("No articles to upload", "error")
            return
        
        success = self.sheets_manager.upload_articles(sheet_name, self.articles)
        if success:
            self.log("✅ Articles uploaded", "success")
        else:
            self.log("❌ Failed to upload articles", "error")
    
    def upload_authors(self):
        """Upload authors to Google Sheets"""
        sheet_name = self.selected_sheet or self.sheet_name_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Select or enter sheet name")
            return
        
        if not self.sheets_manager or not self.sheets_connected:
            self.log("Google Sheets not configured", "error")
            return
        
        if not self.authors:
            self.log("No authors to upload", "error")
            return
        
        success = self.sheets_manager.upload_authors(sheet_name, self.authors)
        if success:
            self.log("✅ Authors uploaded", "success")
        else:
            self.log("❌ Failed to upload authors", "error")
    
    def upload_enhanced(self):
        """Upload enhanced authors to Google Sheets"""
        sheet_name = self.selected_sheet or self.sheet_name_var.get()
        if not sheet_name:
            messagebox.showerror("Error", "Select or enter sheet name")
            return
        
        if not self.sheets_manager or not self.sheets_connected:
            self.log("Google Sheets not configured", "error")
            return
        
        if not self.enhanced_authors:
            self.log("No enhanced authors to upload", "error")
            return
        
        success = self.sheets_manager.upload_enhanced_authors(sheet_name, self.enhanced_authors)
        if success:
            self.log(f"✅ Enhanced authors uploaded: {len(self.enhanced_authors)} records", "success")
        else:
            self.log("❌ Failed to upload enhanced authors", "error")
    
    # =========================
    # ENHANCEMENT ACTIONS
    # =========================
    
    def deduplicate_articles_api(self):
        if not self.articles:
            self.log("No articles to deduplicate", "error")
            return
        
        original_count = len(self.articles)
        self.articles = enhancer_core.deduplicate_articles(self.articles)
        removed = original_count - len(self.articles)
        
        self.log(f"✅ Article deduplication complete. Removed {removed} duplicates.", "success")
        self.log(f"Articles: {original_count} → {len(self.articles)}", "info")
    
    def deduplicate_authors_api(self):
        if not self.authors:
            self.log("No authors to deduplicate", "error")
            return
        
        original_count = len(self.authors)
        self.authors = enhancer_core.deduplicate_authors(self.authors)
        removed = original_count - len(self.authors)
        
        self.log(f"✅ Author deduplication complete. Removed {removed} duplicates.", "success")
        self.log(f"Authors: {original_count} → {len(self.authors)}", "info")
    
    def validate_relationships_api(self):
        if not self.articles or not self.authors:
            self.log("Need both articles and authors data", "error")
            return
        
        articles_df = pd.DataFrame(self.articles)
        valid_authors = []
        invalid_authors = []
        
        for author in self.authors:
            is_valid, message = enhancer_core.validate_author_article_relationship(author, articles_df)
            if is_valid:
                valid_authors.append(author)
            else:
                invalid_authors.append((author.get("Author Name", "Unknown"), message))
        
        self.log(f"✅ Author-article validation complete:", "success")
        self.log(f"  Valid authors: {len(valid_authors)}", "info")
        self.log(f"  Invalid authors: {len(invalid_authors)}", "warning")
        
        if invalid_authors:
            self.log("Invalid authors (first 5):", "warning")
            for name, reason in invalid_authors[:5]:
                self.log(f"  - {name}: {reason}", "warning")
    
    def check_recency_api(self):
        if not self.articles or not self.authors:
            self.log("Need both articles and authors data", "error")
            return
        
        articles_df = pd.DataFrame(self.articles)
        recent_authors = []
        outdated_authors = []
        
        for author in self.authors:
            author_name = author.get("Author Name", "")
            if author_name:
                is_recent, message = enhancer_core.check_recency(articles_df, author_name)
                if is_recent:
                    recent_authors.append(author_name)
                else:
                    outdated_authors.append((author_name, message))
        
        self.log(f"✅ Recency check complete:", "success")
        self.log(f"  Authors with recent articles: {len(recent_authors)}", "info")
        self.log(f"  Authors outdated: {len(outdated_authors)}", "warning")
    
    def filter_low_signal_api(self):
        if not self.authors:
            self.log("No authors to filter", "error")
            return
        
        original_count = len(self.authors)
        filtered_authors = []
        removed_authors = []
        
        for author in self.authors:
            is_valid, message = enhancer_core.filter_low_signal_authors(author)
            if is_valid:
                filtered_authors.append(author)
            else:
                removed_authors.append((author.get("Author Name", "Unknown"), message))
        
        self.authors = filtered_authors
        removed = original_count - len(self.authors)
        
        self.log(f"✅ Low-signal filter complete. Removed {removed} authors.", "success")
        self.log(f"Authors: {original_count} → {len(self.authors)}", "info")
    
    def calculate_activity_scores_api(self):
        if not self.articles or not self.authors:
            self.log("Need both articles and authors data", "error")
            return
        
        articles_df = pd.DataFrame(self.articles)
        
        for author in self.authors:
            author_name = author.get("Author Name", "")
            if author_name:
                score = enhancer_core.calculate_activity_score(articles_df, author_name)
                author["Activity Score"] = score
        
        self.log(f"✅ Activity scores calculated for {len(self.authors)} authors", "success")
        
        # Show score distribution
        score_counts = {}
        for author in self.authors:
            score = author.get("Activity Score", 0)
            score_counts[score] = score_counts.get(score, 0) + 1
        
        for score in sorted(score_counts.keys()):
            self.log(f"  Score {score}: {score_counts[score]} authors", "info")
    
    def calculate_relevance_scores_api(self):
        if not self.articles or not self.authors:
            self.log("Need both articles and authors data", "error")
            return
        
        articles_df = pd.DataFrame(self.articles)
        
        for author in self.authors:
            author_name = author.get("Author Name", "")
            if author_name:
                score = enhancer_core.calculate_relevance_score(articles_df, author_name)
                author["Relevance Score"] = score
        
        self.log(f"✅ Relevance scores calculated for {len(self.authors)} authors", "success")
        
        # Show score distribution
        score_counts = {}
        for author in self.authors:
            score = author.get("Relevance Score", 0)
            score_counts[score] = score_counts.get(score, 0) + 1
        
        for score in sorted(score_counts.keys()):
            self.log(f"  Score {score}: {score_counts[score]} authors", "info")
    
    def assign_topics_api(self):
        if not self.articles or not self.authors:
            self.log("Need both articles and authors data", "error")
            return
        
        articles_df = pd.DataFrame(self.articles)
        
        for author in self.authors:
            author_name = author.get("Author Name", "")
            if author_name:
                topic = enhancer_core.assign_primary_topic(articles_df, author_name)
                author["Primary Topic"] = topic
        
        self.log(f"✅ Primary topics assigned for {len(self.authors)} authors", "success")
        
        # Show topic distribution
        topic_counts = {}
        for author in self.authors:
            topic = author.get("Primary Topic", "Unknown")
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
            self.log(f"  {topic}: {count} authors", "info")
    
    def validate_all_api(self):
        """Run all validation checks"""
        self.log("Running all validations...", "progress")
        self.validate_relationships_api()
        self.check_recency_api()
        self.filter_low_signal_api()
        self.log("✅ All validations complete", "success")
    
    def score_all_api(self):
        """Run all scoring functions"""
        self.log("Calculating all scores...", "progress")
        self.calculate_activity_scores_api()
        self.calculate_relevance_scores_api()
        self.assign_topics_api()
        self.log("✅ All scores calculated", "success")
    
    def apply_enhancements_api(self):
        """Apply all enhancements"""
        self.log("Applying all enhancements...", "progress")
        
        enhanced_articles, enhanced_authors, valid_authors = enhancer_core.apply_enhancements(
            self.articles, self.authors
        )
        
        self.articles = enhanced_articles
        self.enhanced_authors = enhanced_authors
        
        self.log(f"✅ Enhanced articles: {len(self.articles)} (deduplicated)", "success")
        self.log(f"✅ Enhanced authors: {len(self.enhanced_authors)} (all)", "success")
        self.log(f"✅ Valid authors: {len(valid_authors)} (non-INVALID)", "success")
        
        # Show statistics
        status_counts = {}
        for author in self.enhanced_authors:
            status = author.get("Validation Status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            self.log(f"  {status}: {count} authors", "info")
    
    # =========================
    # ANALYSIS & EXPORT
    # =========================
    
    def show_statistics(self):
        self.log("=== DATA STATISTICS ===", "info")
        self.log(f"Articles: {len(self.articles)}", "info")
        self.log(f"Authors: {len(self.authors)}", "info")
        self.log(f"Enhanced Authors: {len(self.enhanced_authors)}", "info")
        
        if self.enhanced_authors:
            # Validation status distribution
            status_counts = {}
            for author in self.enhanced_authors:
                status = author.get("Validation Status", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            self.log("Validation Status:", "info")
            for status, count in sorted(status_counts.items()):
                self.log(f"  {status}: {count}", "info")
            
            # Score averages
            if any("Activity Score" in author for author in self.enhanced_authors):
                avg_activity = sum(a.get("Activity Score", 0) for a in self.enhanced_authors) / len(self.enhanced_authors)
                avg_relevance = sum(a.get("Relevance Score", 0) for a in self.enhanced_authors) / len(self.enhanced_authors)
                self.log(f"Avg Activity Score: {avg_activity:.2f}", "info")
                self.log(f"Avg Relevance Score: {avg_relevance:.2f}", "info")
    
    def show_topic_stats(self):
        if not self.enhanced_authors and not self.authors:
            self.log("No data to analyze", "error")
            return
        
        data = self.enhanced_authors if self.enhanced_authors else self.authors
        
        topic_counts = {}
        for author in data:
            topic = author.get("Primary Topic", "Unknown")
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        self.log("=== TOPIC DISTRIBUTION ===", "info")
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
            self.log(f"  {topic}: {count} authors", "info")
    
    def filter_by_status(self):
        if not self.enhanced_authors:
            self.log("No enhanced authors to filter", "error")
            return
        
        # Create filter dialog
        filter_window = tk.Toplevel(self.root)
        filter_window.title("Filter by Status")
        filter_window.geometry("300x200")
        
        status_var = tk.StringVar(value="VALID")
        
        ttk.Label(filter_window, text="Select Status:").pack(pady=10)
        ttk.Radiobutton(filter_window, text="VALID", variable=status_var, value="VALID").pack()
        ttk.Radiobutton(filter_window, text="REVIEW", variable=status_var, value="REVIEW").pack()
        ttk.Radiobutton(filter_window, text="INVALID", variable=status_var, value="INVALID").pack()
        
        def apply_filter():
            status = status_var.get()
            filtered = [a for a in self.enhanced_authors if a.get("Validation Status") == status]
            
            self.log(f"Filtered authors by status '{status}': {len(filtered)} found", "success")
            
            # Show preview
            if filtered:
                self.log(f"First 5 {status} authors:", "info")
                for i, author in enumerate(filtered[:5], 1):
                    name = author.get("Author Name", "Unknown")
                    self.log(f"  {i}. {name}", "info")
            
            filter_window.destroy()
        
        ttk.Button(filter_window, text="Apply Filter", command=apply_filter).pack(pady=20)
    
    def generate_report(self):
        if not self.enhanced_authors:
            self.log("No enhanced authors to report on", "error")
            return
        
        self.log("=== VALIDATION REPORT ===", "success")
        
        # Count by status
        valid_count = sum(1 for a in self.enhanced_authors if a.get("Validation Status") == "VALID")
        review_count = sum(1 for a in self.enhanced_authors if a.get("Validation Status") == "REVIEW")
        invalid_count = sum(1 for a in self.enhanced_authors if a.get("Validation Status") == "INVALID")
        
        self.log(f"VALID: {valid_count} authors (ready for outreach)", "success")
        self.log(f"REVIEW: {review_count} authors (needs manual check)", "warning")
        self.log(f"INVALID: {invalid_count} authors (excluded)", "error")
        
        # Show top authors by activity
        if valid_count > 0:
            valid_authors = [a for a in self.enhanced_authors if a.get("Validation Status") == "VALID"]
            sorted_authors = sorted(valid_authors, 
                                  key=lambda x: (x.get("Activity Score", 0), x.get("Relevance Score", 0)), 
                                  reverse=True)[:10]
            
            self.log("Top 10 authors for outreach:", "info")
            for i, author in enumerate(sorted_authors, 1):
                name = author.get("Author Name", "Unknown")
                activity = author.get("Activity Score", 0)
                relevance = author.get("Relevance Score", 0)
                topic = author.get("Primary Topic", "Unknown")
                self.log(f"  {i}. {name} | Activity: {activity} | Relevance: {relevance} | Topic: {topic}", "info")
    
    def export_csv(self):
        if not self.enhanced_authors:
            self.log("No enhanced authors to export", "error")
            return
        
        try:
            df = pd.DataFrame(self.enhanced_authors)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_authors_{timestamp}.csv"
            df.to_csv(filename, index=False)
            self.log(f"✅ Exported {len(df)} authors to {filename}", "success")
        except Exception as e:
            self.log(f"❌ Export failed: {str(e)}", "error")
    
    def preview_data(self):
        """Show preview of current data"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Data Preview")
        preview_window.geometry("800x600")
        
        notebook = ttk.Notebook(preview_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Articles tab
        if self.articles:
            articles_frame = ttk.Frame(notebook)
            notebook.add(articles_frame, text=f"Articles ({len(self.articles)})")
            
            articles_text = ScrolledText(articles_frame, height=20)
            articles_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Show first 50 articles
            for i, article in enumerate(self.articles[:50], 1):
                title = article.get("Article Title", "No Title")[:50]
                articles_text.insert("end", f"{i}. {title}...\n")
        
        # Authors tab
        if self.authors:
            authors_frame = ttk.Frame(notebook)
            notebook.add(authors_frame, text=f"Authors ({len(self.authors)})")
            
            authors_text = ScrolledText(authors_frame, height=20)
            authors_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Show first 50 authors
            for i, author in enumerate(self.authors[:50], 1):
                name = author.get("Author Name", "No Name")
                authors_text.insert("end", f"{i}. {name}\n")
        
        # Enhanced Authors tab
        if self.enhanced_authors:
            enhanced_frame = ttk.Frame(notebook)
            notebook.add(enhanced_frame, text=f"Enhanced ({len(self.enhanced_authors)})")
            
            enhanced_text = ScrolledText(enhanced_frame, height=20)
            enhanced_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Show first 50 enhanced authors with scores
            for i, author in enumerate(self.enhanced_authors[:50], 1):
                name = author.get("Author Name", "No Name")
                activity = author.get("Activity Score", "N/A")
                relevance = author.get("Relevance Score", "N/A")
                status = author.get("Validation Status", "UNKNOWN")
                enhanced_text.insert("end", f"{i}. {name} | A:{activity} R:{relevance} | {status}\n")
