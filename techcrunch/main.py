# main.py - Business Insider Platform Launcher
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

class BusinessInsiderPlatform:
    def __init__(self, root):
        self.root = root
        self.root.title("Business Insider Platform")
        self.root.geometry("900x600")
        
        # Configure styles
        self.configure_styles()
        
        # Center window on screen
        self.center_window()
        
        # Build main menu
        self.build_main_menu()
    
    def configure_styles(self):
        """Configure custom styles for Business Insider theme"""
        style = ttk.Style()
        
        # Business Insider colors
        bi_red = "#E2001A"
        bi_dark = "#1A1A1A"
        bi_light = "#F5F5F5"
        bi_accent = "#0066CC"
        
        # Configure theme
        style.theme_use('clam')
        
        # Configure label colors
        style.configure('Title.TLabel', 
                       font=('Arial', 28, 'bold'),
                       foreground=bi_red)
        style.configure('Subtitle.TLabel',
                       font=('Arial', 12),
                       foreground='#666666')
        style.configure('ToolTitle.TLabel',
                       font=('Arial', 16, 'bold'),
                       foreground=bi_dark)
        style.configure('ToolDesc.TLabel',
                       font=('Arial', 10),
                       foreground='#555555')
        
        # Configure button styles
        style.configure('Primary.TButton',
                       font=('Arial', 11, 'bold'),
                       foreground='white',
                       background=bi_red,
                       padding=10)
        style.map('Primary.TButton',
                 background=[('active', '#C10015'), ('pressed', '#A00012')])
        
        style.configure('Secondary.TButton',
                       font=('Arial', 10),
                       foreground='white',
                       background=bi_accent,
                       padding=8)
        style.map('Secondary.TButton',
                 background=[('active', '#0055AA'), ('pressed', '#004499')])
        
        # Configure frame styles
        style.configure('Header.TFrame', background='white')
        style.configure('Content.TFrame', background='white')
        style.configure('ToolCard.TFrame', 
                       background='#F9F9F9',
                       relief='solid',
                       borderwidth=1)
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 900
        window_height = 600
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def build_main_menu(self):
        """Build the main menu interface"""
        # Set background
        self.root.configure(bg='white')
        
        # Main content area
        main_container = tk.Frame(self.root, bg='white')
        main_container.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Header Section
        header_frame = ttk.Frame(main_container, style='Header.TFrame')
        header_frame.pack(fill="x", pady=(0, 30))
        
        # Business Insider logo and title
        logo_frame = tk.Frame(header_frame, bg='white')
        logo_frame.pack(anchor="center")
        
        # Business Insider icon
        icon_label = tk.Label(logo_frame, 
                             text="📰", 
                             font=("Arial", 48),
                             bg='white')
        icon_label.pack()
        
        # Title
        title_label = ttk.Label(logo_frame, 
                               text="Business Insider Platform", 
                               style='Title.TLabel')
        title_label.pack(pady=(10, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(logo_frame,
                                  text="Complete Media Intelligence & Outreach Suite",
                                  style='Subtitle.TLabel')
        subtitle_label.pack()
        
        # Divider
        ttk.Separator(main_container, orient='horizontal').pack(fill='x', pady=20)
        
        # Tools Section
        tools_container = tk.Frame(main_container, bg='white')
        tools_container.pack(fill="both", expand=True)
        
        # Section Title
        section_label = ttk.Label(tools_container,
                                 text="Select Your Tool",
                                 font=('Arial', 18, 'bold'),
                                 foreground='#333333')
        section_label.pack(anchor="center", pady=(0, 30))
        
        # Tools Grid
        tools_grid = tk.Frame(tools_container, bg='white')
        tools_grid.pack(fill="both", expand=True)
        
        # Scraper Tool Card
        scraper_card = tk.Frame(tools_grid, bg='#F9F9F9', 
                               relief='solid', borderwidth=1,
                               highlightbackground='#E0E0E0',
                               highlightthickness=1)
        scraper_card.grid(row=0, column=0, padx=20, pady=10, sticky='nsew')
        scraper_card.configure(width=350, height=200)
        
        # Scraper Card Content
        scraper_icon = tk.Label(scraper_card, 
                               text="🔍", 
                               font=("Arial", 36),
                               bg='#F9F9F9')
        scraper_icon.pack(pady=(20, 10))
        
        scraper_title = ttk.Label(scraper_card,
                                 text="Business Insider Scraper",
                                 style='ToolTitle.TLabel',
                                 background='#F9F9F9')
        scraper_title.pack()
        
        scraper_desc = ttk.Label(scraper_card,
                                text="Scrape articles, authors & data from Business Insider",
                                style='ToolDesc.TLabel',
                                background='#F9F9F9')
        scraper_desc.pack(pady=(5, 15))
        
        scraper_button = ttk.Button(scraper_card,
                                   text="Launch Scraper",
                                   style='Primary.TButton',
                                   command=self.launch_scraper)
        scraper_button.pack(pady=(0, 20))
        
        # Outreach Tool Card
        outreach_card = tk.Frame(tools_grid, bg='#F9F9F9',
                                relief='solid', borderwidth=1,
                                highlightbackground='#E0E0E0',
                                highlightthickness=1)
        outreach_card.grid(row=0, column=1, padx=20, pady=10, sticky='nsew')
        outreach_card.configure(width=350, height=200)
        
        # Outreach Card Content
        outreach_icon = tk.Label(outreach_card,
                                text="📧",
                                font=("Arial", 36),
                                bg='#F9F9F9')
        outreach_icon.pack(pady=(20, 10))
        
        outreach_title = ttk.Label(outreach_card,
                                  text="Author Outreach Tool",
                                  style='ToolTitle.TLabel',
                                  background='#F9F9F9')
        outreach_title.pack()
        
        outreach_desc = ttk.Label(outreach_card,
                                 text="Send personalized emails to Business Insider authors",
                                 style='ToolDesc.TLabel',
                                 background='#F9F9F9')
        outreach_desc.pack(pady=(5, 15))
        
        outreach_button = ttk.Button(outreach_card,
                                    text="Launch Outreach",
                                    style='Primary.TButton',
                                    command=self.launch_outreach)
        outreach_button.pack(pady=(0, 20))
        
        # Configure grid weights
        tools_grid.columnconfigure(0, weight=1)
        tools_grid.columnconfigure(1, weight=1)
        tools_grid.rowconfigure(0, weight=1)
        
        # Features Section
        features_frame = tk.Frame(main_container, bg='white')
        features_frame.pack(fill="x", pady=(40, 20))
        
        features_label = ttk.Label(features_frame,
                                  text="✨ Key Features",
                                  font=('Arial', 16, 'bold'),
                                  foreground='#333333')
        features_label.pack(anchor="center", pady=(0, 15))
        
        # Features grid
        features_grid = tk.Frame(features_frame, bg='white')
        features_grid.pack()
        
        features = [
            ("🚀", "Multi-category scraping"),
            ("📊", "Data enhancement & scoring"),
            ("🤖", "Smart author identification"),
            ("📈", "Google Sheets integration"),
            ("✉️", "Personalized email templates"),
            ("📋", "Campaign tracking & analytics")
        ]
        
        for i, (icon, text) in enumerate(features):
            feature_frame = tk.Frame(features_grid, bg='white')
            feature_frame.grid(row=i//3, column=i%3, padx=15, pady=8, sticky='w')
            
            feature_icon = tk.Label(feature_frame, 
                                   text=icon, 
                                   font=("Arial", 14),
                                   bg='white')
            feature_icon.pack(side="left", padx=(0, 8))
            
            feature_text = ttk.Label(feature_frame,
                                    text=text,
                                    font=('Arial', 10),
                                    foreground='#555555',
                                    background='white')
            feature_text.pack(side="left")
        
        # Footer
        footer_frame = tk.Frame(main_container, bg='white')
        footer_frame.pack(fill="x", pady=(30, 0))
        
        # Help button
        help_button = ttk.Button(footer_frame,
                                text="❓ Help & Documentation",
                                style='Secondary.TButton',
                                command=self.show_help)
        help_button.pack(side="right")
        
        # Version info
        version_label = ttk.Label(footer_frame,
                                 text="Business Insider Platform v2.0",
                                 font=('Arial', 9),
                                 foreground='#888888',
                                 background='white')
        version_label.pack(side="left")
    
    def launch_scraper(self):
        """Launch the scraper tool"""
        try:
            # Import and launch scraper
            from ui.scraper_ui import ScraperApp
            
            # Create new window for scraper
            scraper_root = tk.Toplevel(self.root)
            scraper_root.title("Business Insider Scraper")
            
            # Set to 95% of screen size
            screen_width = scraper_root.winfo_screenwidth()
            screen_height = scraper_root.winfo_screenheight()
            width = int(screen_width * 0.95)
            height = int(screen_height * 0.9)
            
            scraper_root.geometry(f"{width}x{height}")
            
            # Center window
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            scraper_root.geometry(f"{width}x{height}+{x}+{y}")
            
            # Launch app
            scraper_app = ScraperApp(scraper_root)
            
        except ImportError:
            messagebox.showerror("Error", "Scraper module not found. Make sure ui/scraper_ui.py exists.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch scraper:\n{str(e)}")
    
    def launch_outreach(self):
        """Launch the outreach tool"""
        try:
            # Import and launch outreach
            from ui.outreach_ui import OutreachApp
            
            # Create new window for outreach
            outreach_root = tk.Toplevel(self.root)
            outreach_root.title("Business Insider Author Outreach")
            
            # Set to 90% of screen size
            screen_width = outreach_root.winfo_screenwidth()
            screen_height = outreach_root.winfo_screenheight()
            width = int(screen_width * 0.9)
            height = int(screen_height * 0.85)
            
            outreach_root.geometry(f"{width}x{height}")
            
            # Center window
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            outreach_root.geometry(f"{width}x{height}+{x}+{y}")
            
            # Launch app
            outreach_app = OutreachApp(outreach_root)
            
        except ImportError:
            messagebox.showerror("Error", "Outreach module not found. Make sure ui/outreach_ui.py exists.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch outreach:\n{str(e)}")
    
    def show_help(self):
        """Show help information"""
        help_text = """
        📰 Business Insider Platform - Quick Guide
        
        🔍 Scraper Tool:
        1. Select Business Insider categories to scrape
        2. Set number of pages to crawl
        3. Click "Scrape Articles" to gather content
        4. Click "Scrape Authors" to extract author data
        5. Use enhancement tools to process & score data
        6. Upload to Google Sheets for further analysis
        
        📧 Outreach Tool:
        1. Load author data from Google Sheets
        2. Select authors to contact
        3. Customize email templates with personalization
        4. Preview emails before sending
        5. Send emails individually or in batches
        6. Track sent emails and responses
        
        🔧 Setup Requirements:
        • Google Sheets API credentials
        • Business Insider account (for scraping)
        • SMTP email configuration (for outreach)
        
        💡 Tips:
        • Start with 1-2 pages when testing
        • Use the data enhancement tools before outreach
        • Test email templates before bulk sending
        • Regularly backup your Google Sheets data
        
        Need more help? Check the documentation or contact support.
        """
        
        # Create a styled help window
        help_window = tk.Toplevel(self.root)
        help_window.title("Help & Documentation")
        help_window.geometry("700x500")
        help_window.configure(bg='white')
        
        # Center help window
        help_window.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (350)
        y = (self.root.winfo_screenheight() // 2) - (250)
        help_window.geometry(f"700x500+{x}+{y}")
        
        # Title
        title_label = ttk.Label(help_window,
                               text="Help & Documentation",
                               font=('Arial', 18, 'bold'),
                               foreground='#E2001A',
                               background='white')
        title_label.pack(pady=(20, 10))
        
        # Text widget for help content
        help_text_widget = tk.Text(help_window,
                                  wrap='word',
                                  font=('Arial', 10),
                                  bg='white',
                                  fg='#333333',
                                  padx=20,
                                  pady=10,
                                  height=20)
        help_text_widget.pack(fill='both', expand=True, padx=20, pady=10)
        help_text_widget.insert('1.0', help_text)
        help_text_widget.config(state='disabled')  # Make read-only
        
        # Close button
        close_button = ttk.Button(help_window,
                                 text="Close",
                                 style='Secondary.TButton',
                                 command=help_window.destroy)
        close_button.pack(pady=(0, 20))

def main():
    root = tk.Tk()
    app = BusinessInsiderPlatform(root)
    root.mainloop()

if __name__ == "__main__":
    main()
