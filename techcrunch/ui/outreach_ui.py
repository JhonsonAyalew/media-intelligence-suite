# ui/outreach_ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import threading
import json
import os
import csv
import sys

# Add the modules directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from modules import email_core, config_manager
from modules.config_manager import ConfigManager
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class OutreachApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Author Outreach Pro")
        self.root.geometry("1200x700")
        
        # Load configuration
        self.config = ConfigManager.load_outreach_config()
        
        # Initialize managers
        self.email_manager = email_core.EmailManager(self.config)
        
        # Data storage
        self.authors = []
        self.selected_authors = set()
        self.sent_history = []
        
        # Build UI
        self.setup_styles()
        self.build_ui()
        
        # Test connection
        self.test_connection_async()
    
    def setup_styles(self):
        """Setup modern styles"""
        style = ttk.Style()
        
        # Configure colors
        self.root.configure(bg="#f5f5f5")
        
        # Custom button styles
        style.configure("Primary.TButton", font=("Arial", 10, "bold"), padding=6)
        style.configure("Success.TButton", font=("Arial", 10, "bold"), foreground="green")
        style.configure("Danger.TButton", font=("Arial", 10, "bold"), foreground="red")
        
        # Configure treeview
        style.configure("Treeview", font=("Arial", 9), rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
    
    def build_ui(self):
        """Build clean, modern UI"""
        # Header
        header = ttk.Frame(self.root, padding="10")
        header.pack(fill="x")
        
        # Logo/Title
        title_frame = ttk.Frame(header)
        title_frame.pack(side="left", fill="y")
        
        ttk.Label(title_frame, text="📧", font=("Arial", 24)).pack(side="left", padx=(0, 10))
        ttk.Label(title_frame, text="Author Outreach Pro", font=("Arial", 16, "bold")).pack(side="left")
        
        # Stats
        self.stats_label = ttk.Label(header, text="Ready | 0 authors loaded", font=("Arial", 10))
        self.stats_label.pack(side="right", padx=20)
        
        # Connection status
        self.connection_label = ttk.Label(header, text="⚪", font=("Arial", 12))
        self.connection_label.pack(side="right")
        
        # Toolbar
        toolbar = ttk.Frame(self.root, padding="10 5 10 5")
        toolbar.pack(fill="x")
        
        # Toolbar buttons
        buttons = [
            ("📂 Load", self.load_authors, "Primary.TButton"),
            ("⚙️ Settings", self.open_settings, ""),
            ("📧 Test", self.test_connection, ""),
            ("📊 Export", self.export_data, ""),
            ("🗑️ Clear", self.clear_data, "Danger.TButton"),
        ]
        
        for text, command, style_ in buttons:
            btn = ttk.Button(toolbar, text=text, command=command, style=style_, width=12)
            btn.pack(side="left", padx=2)
        
        # Bulk actions frame
        bulk_frame = ttk.LabelFrame(toolbar, text="Bulk Actions", padding="5")
        bulk_frame.pack(side="left", padx=(20, 0))
        
        ttk.Button(bulk_frame, text="✉️ Send Selected", command=self.send_selected, width=15).pack(side="left", padx=2)
        ttk.Button(bulk_frame, text="✅ Mark Sent", command=self.mark_selected_sent, width=12).pack(side="left", padx=2)
        ttk.Button(bulk_frame, text="📋 Select All", command=self.select_all, width=12).pack(side="left", padx=2)
        
        # Main content area
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Treeview with scrollbars
        tree_container = ttk.Frame(main_frame)
        tree_container.pack(fill="both", expand=True)
        
        # Columns
        columns = ("Select", "Author", "Email", "Topic", "Articles", "Score", "Status", "Last Contact")
        
        # Create treeview
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="extended")
        
        # Configure columns
        col_configs = [
            ("Select", 50, "center"),
            ("Author", 180, "w"),
            ("Email", 220, "w"),
            ("Topic", 150, "w"),
            ("Articles", 80, "center"),
            ("Score", 80, "center"),
            ("Status", 100, "center"),
            ("Last Contact", 120, "center")
        ]
        
        for col, width, anchor in col_configs:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)
        
        # Add scrollbars
        v_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        # Status bar
        self.status_bar = ttk.Frame(self.root, relief="sunken", padding="5 2")
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_text = ttk.Label(self.status_bar, text="Ready")
        self.status_text.pack(side="left")
        
        # Email stats
        self.email_stats = ttk.Label(self.status_bar, text="Sent: 0 | Failed: 0")
        self.email_stats.pack(side="right", padx=20)
    
    def log(self, message: str, level: str = "info"):
        """Log message to status bar"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }
        
        icon = icons.get(level, "📝")
        self.status_text.config(text=f"[{timestamp}] {icon} {message}")
        
        # Update email stats
        stats = self.email_manager.get_stats()
        self.email_stats.config(text=f"Sent: {stats['sent']} | Failed: {stats['failed']}")
    
    def test_connection_async(self):
        """Test connection in background"""
        def test():
            self.connection_label.config(text="🟡 Testing...")
            success, message = self.email_manager.test_connection()
            
            self.root.after(0, lambda: self.connection_label.config(
                text="🟢" if success else "🔴"
            ))
            
            if success:
                self.root.after(0, lambda: self.log("SMTP connection successful", "success"))
            else:
                self.root.after(0, lambda: self.log(f"Connection failed: {message}", "error"))
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_connection(self):
        """Test connection with dialog"""
        self.log("Testing SMTP connection...", "info")
        self.test_connection_async()
    
    def load_authors(self):
        """Load authors from Google Sheets"""
        try:
            self.log("Loading authors from Google Sheets...", "info")
            
            # Check credentials
            if not os.path.exists(self.config['google_creds_file']):
                self.log("Credentials file not found. Please update settings.", "error")
                messagebox.showerror("Error", "Google credentials file not found. Please update settings.")
                return
            
            # Connect to Google Sheets - USING ORIGINAL WORKING CODE
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.config['google_creds_file'], scope
            )
            client = gspread.authorize(creds)
            
            # Open the sheet - using sheet1 (default worksheet)
            try:
                sheet = client.open(self.config['scraper-service-account']).sheet1
                records = sheet.get_all_records()
            except Exception as e:
                self.log(f"Error opening sheet: {str(e)}", "error")
                # Try Enhanced_Authors worksheet
                try:
                    sheet = client.open(self.config['sheet_name']).worksheet("Authors")
                    records = sheet.get_all_records()
                except:
                    # Try Authors worksheet
                    try:
                        sheet = client.open(self.config['sheet_name']).worksheet("Authors")
                        records = sheet.get_all_records()
                    except:
                        self.log("No data found in any worksheet", "error")
                        messagebox.showerror("Error", "No data found. Please run scraper tool first.")
                        return
            
            # Clear existing data
            self.tree.delete(*self.tree.get_children())
            self.authors = []
            self.selected_authors.clear()
            
            # Process records
            valid_count = 0
            email_count = 0
            
            for idx, record in enumerate(records):
                author = {
                    'name': record.get('Author Name', record.get('Author', '')),
                    'email': record.get('Email', ''),
                    'topic': record.get('Primary Topic', record.get('Topic', '')),
                    'articles': record.get('Total Articles', record.get('Articles', '')),
                    'score': record.get('Relevance Score', record.get('Score', '')),
                    'validation': record.get('Validation Status', record.get('Status', '')),
                    'contact_status': record.get('Contact Status', 'Not Contacted'),
                    'last_contact': record.get('Last Contact', '')
                }
                
                self.authors.append(author)
                
                if author['validation'] == 'VALID':
                    valid_count += 1
                
                if author['email']:
                    email_count += 1
                
                # Insert into treeview
                values = (
                    "□",  # Checkbox
                    author['name'],
                    author['email'],
                    author['topic'],
                    author['articles'],
                    author['score'],
                    author['contact_status'],
                    author['last_contact']
                )
                
                item_id = self.tree.insert("", "end", values=values)
                
                # Set tags based on status
                tags = []
                if author['validation'] == 'VALID':
                    tags.append('valid')
                if author['contact_status'] == 'Contacted':
                    tags.append('contacted')
                
                if tags:
                    self.tree.item(item_id, tags=tags)
            
            # Update stats
            self.stats_label.config(text=f"Loaded: {len(records)} | Valid: {valid_count} | With Email: {email_count}")
            self.log(f"Successfully loaded {len(records)} authors", "success")
            
            # Configure tree tags
            self.tree.tag_configure('valid', background='#e8f5e9')
            self.tree.tag_configure('contacted', background='#e3f2fd')
            
        except FileNotFoundError:
            self.log("Credentials file not found", "error")
            messagebox.showerror("Error", "Credentials file not found. Please update settings.")
        except Exception as e:
            self.log(f"Error loading authors: {str(e)}", "error")
            import traceback
            error_details = traceback.format_exc()
            self.log(f"Error details: {error_details}", "error")
            messagebox.showerror("Error", f"Failed to load authors:\n{str(e)}")
    
    def on_tree_click(self, event):
        """Handle treeview clicks"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        
        if not row:
            return
        
        # Handle checkbox column
        if col == "#1":  # Select column
            item_id = row
            values = list(self.tree.item(item_id, "values"))
            
            if values[0] == "□":  # Unchecked
                values[0] = "☑"
                self.selected_authors.add(item_id)
            else:  # Checked
                values[0] = "□"
                self.selected_authors.discard(item_id)
            
            self.tree.item(item_id, values=values)
        
        # Handle other columns for sending
        elif col == "#8":  # Last Contact column (or any other column you want to use for send)
            item_id = row
            values = self.tree.item(item_id, "values")
            
            # Get author data
            author_idx = self.tree.index(item_id)
            if author_idx < len(self.authors):
                author = self.authors[author_idx]
                if author['email']:
                    self.send_single_email(author)
    
    def on_tree_double_click(self, event):
        """Handle double-click for quick edit"""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            author_idx = self.tree.index(item_id)
            if author_idx < len(self.authors):
                author = self.authors[author_idx]
                self.show_email_editor(author)
    
    def show_email_editor(self, author):
        """Show email editor for a single author"""
        editor = tk.Toplevel(self.root)
        editor.title(f"Send Email to {author['name']}")
        editor.geometry("600x500")
        editor.resizable(True, True)
        
        # Center the window
        editor.transient(self.root)
        editor.grab_set()
        
        # Get template
        template = self.config['email_templates']['default']
        
        # Format subject and body
        subject = template['subject'].format(
            author_name=author['name'],
            topic=author['topic']
        )
        
        body = template['body'].format(
            author_name=author['name'],
            topic=author['topic'],
            your_name=self.config['sender_info']['your_name'],
            your_position=self.config['sender_info']['your_position'],
            company_name=self.config['sender_info']['company_name']
        )
        
        # Create editor
        editor_frame = ttk.Frame(editor, padding=15)
        editor_frame.pack(fill="both", expand=True)
        
        # Recipient info
        info_frame = ttk.LabelFrame(editor_frame, text="Recipient", padding=10)
        info_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Name: {author['name']}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Email: {author['email']}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Topic: {author['topic']}").pack(anchor="w")
        
        # Subject
        ttk.Label(editor_frame, text="Subject:", font=("Arial", 10, "bold")).pack(anchor="w")
        subject_var = tk.StringVar(value=subject)
        subject_entry = ttk.Entry(editor_frame, textvariable=subject_var, font=("Arial", 10))
        subject_entry.pack(fill="x", pady=(0, 10))
        
        # Body editor
        ttk.Label(editor_frame, text="Message:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        body_text = ScrolledText(editor_frame, height=12, wrap="word", font=("Arial", 10))
        body_text.pack(fill="both", expand=True, pady=(0, 15))
        body_text.insert("1.0", body)
        
        # Buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="✉️ Send Email", 
                  command=lambda: self.send_from_editor(editor, author, subject_var.get(), body_text.get("1.0", "end-1c")),
                  style="Primary.TButton").pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="💾 Save Draft", 
                  command=lambda: self.save_draft(author, subject_var.get(), body_text.get("1.0", "end-1c"))).pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="❌ Cancel", 
                  command=editor.destroy).pack(side="right", padx=5)
    
    def send_single_email(self, author):
        """Send email to a single author"""
        if not author['email']:
            self.log(f"No email for {author['name']}", "warning")
            messagebox.showwarning("No Email", "This author doesn't have an email address.")
            return
        
        # Get template
        template = self.config['email_templates']['default']
        
        # Format subject and body
        subject = template['subject'].format(
            author_name=author['name'],
            topic=author['topic']
        )
        
        body = template['body'].format(
            author_name=author['name'],
            topic=author['topic'],
            your_name=self.config['sender_info']['your_name'],
            your_position=self.config['sender_info']['your_position'],
            company_name=self.config['sender_info']['company_name']
        )
        
        # Confirm
        if not messagebox.askyesno("Confirm", f"Send email to {author['name']}?"):
            return
        
        # Send in background
        def send():
            self.log(f"Sending email to {author['name']}...", "info")
            
            success, message = self.email_manager.send_email(
                author['email'],
                subject,
                body
            )
            
            # Update UI
            self.root.after(0, self.update_author_status, author, success, message)
        
        threading.Thread(target=send, daemon=True).start()
    
    def send_from_editor(self, editor, author, subject, body):
        """Send email from editor window"""
        def send():
            self.log(f"Sending email to {author['name']}...", "info")
            
            success, message = self.email_manager.send_email(
                author['email'],
                subject,
                body
            )
            
            # Update UI and close editor
            self.root.after(0, self.update_author_status, author, success, message)
            self.root.after(0, editor.destroy)
        
        threading.Thread(target=send, daemon=True).start()
    
    def update_author_status(self, author, success, message):
        """Update author status after sending"""
        # Find author in tree
        for item_id in self.tree.get_children():
            item_values = self.tree.item(item_id, "values")
            if item_values[1] == author['name']:
                # Update values
                values = list(item_values)
                
                if success:
                    values[6] = "Contacted"
                    values[7] = datetime.now().strftime("%Y-%m-%d")
                    self.tree.item(item_id, values=values, tags=('contacted',))
                    self.log(f"✅ Email sent to {author['name']}", "success")
                else:
                    values[6] = "Failed"
                    self.tree.item(item_id, values=values)
                    self.log(f"❌ Failed to send to {author['name']}: {message}", "error")
                
                break
        
        # Update stats
        self.update_stats()
    
    def send_selected(self):
        """Send emails to all selected authors"""
        if not self.selected_authors:
            self.log("No authors selected", "warning")
            messagebox.showwarning("No Selection", "Please select authors to send emails to.")
            return
        
        selected_count = len(self.selected_authors)
        if not messagebox.askyesno("Confirm", f"Send emails to {selected_count} selected authors?"):
            return
        
        # Get selected authors
        authors_to_send = []
        for item_id in self.selected_authors:
            idx = self.tree.index(item_id)
            if idx < len(self.authors):
                author = self.authors[idx]
                if author['email']:
                    authors_to_send.append(author)
        
        # Send in background
        def send_bulk():
            total = len(authors_to_send)
            for i, author in enumerate(authors_to_send, 1):
                self.root.after(0, lambda a=author, idx=i, total=total: 
                              self.log(f"Sending {idx}/{total}: {a['name']}", "info"))
                
                # Get template
                template = self.config['email_templates']['default']
                subject = template['subject'].format(author_name=author['name'], topic=author['topic'])
                body = template['body'].format(
                    author_name=author['name'],
                    topic=author['topic'],
                    your_name=self.config['sender_info']['your_name'],
                    your_position=self.config['sender_info']['your_position'],
                    company_name=self.config['sender_info']['company_name']
                )
                
                # Send email
                success, message = self.email_manager.send_email(author['email'], subject, body)
                
                # Update status
                self.root.after(0, self.update_author_status, author, success, message)
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(1)
            
            self.root.after(0, lambda: messagebox.showinfo("Complete", 
                                                         f"Finished sending {total} emails"))
        
        threading.Thread(target=send_bulk, daemon=True).start()
    
    def mark_selected_sent(self):
        """Mark selected authors as contacted"""
        if not self.selected_authors:
            self.log("No authors selected", "warning")
            return
        
        for item_id in self.selected_authors:
            values = list(self.tree.item(item_id, "values"))
            values[6] = "Contacted"
            values[7] = datetime.now().strftime("%Y-%m-%d")
            self.tree.item(item_id, values=values, tags=('contacted',))
        
        self.log(f"Marked {len(self.selected_authors)} authors as contacted", "success")
    
    def select_all(self):
        """Select all authors"""
        for item_id in self.tree.get_children():
            if item_id not in self.selected_authors:
                values = list(self.tree.item(item_id, "values"))
                values[0] = "☑"
                self.tree.item(item_id, values=values)
                self.selected_authors.add(item_id)
        
        self.log(f"Selected all authors", "info")
    
    def update_stats(self):
        """Update statistics display"""
        total = len(self.authors)
        contacted = sum(1 for a in self.authors if a['contact_status'] == 'Contacted')
        stats = f"{total} authors | {contacted} contacted"
        self.stats_label.config(text=stats)
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            # Import SettingsDialog here to avoid circular imports
            from ui.settings_dialog import SettingsDialog
            SettingsDialog(self.root, self.config, self.on_settings_saved)
        except ImportError as e:
            self.log(f"Error loading settings dialog: {str(e)}", "error")
            messagebox.showerror("Error", f"Could not load settings dialog:\n{str(e)}")
    
    def on_settings_saved(self, new_config):
        """Handle settings save"""
        self.config = new_config
        self.email_manager = email_core.EmailManager(self.config)
        self.log("Settings saved successfully", "success")
    
    def save_draft(self, author, subject, body):
        """Save email draft"""
        draft = {
            'author': author['name'],
            'email': author['email'],
            'subject': subject,
            'body': body,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to file
        drafts_file = "email_drafts.json"
        drafts = []
        
        if os.path.exists(drafts_file):
            try:
                with open(drafts_file, 'r', encoding='utf-8') as f:
                    drafts = json.load(f)
            except:
                drafts = []
        
        drafts.append(draft)
        
        try:
            with open(drafts_file, 'w', encoding='utf-8') as f:
                json.dump(drafts, f, indent=4, ensure_ascii=False)
            self.log(f"Draft saved for {author['name']}", "success")
        except Exception as e:
            self.log(f"Failed to save draft: {str(e)}", "error")
    
    def export_data(self):
        """Export data to CSV"""
        if not self.authors:
            self.log("No data to export", "warning")
            messagebox.showwarning("No Data", "No data to export. Load authors first.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"authors_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow([
                        'Author Name', 'Email', 'Primary Topic', 'Total Articles',
                        'Relevance Score', 'Validation Status', 'Contact Status',
                        'Last Contact'
                    ])
                    
                    # Write data
                    for author in self.authors:
                        writer.writerow([
                            author['name'],
                            author['email'],
                            author['topic'],
                            author['articles'],
                            author['score'],
                            author['validation'],
                            author['contact_status'],
                            author['last_contact']
                        ])
                
                self.log(f"Data exported to {filename}", "success")
                messagebox.showinfo("Success", f"Data exported to:\n{filename}")
                
            except Exception as e:
                self.log(f"Export failed: {str(e)}", "error")
                messagebox.showerror("Error", f"Failed to export data:\n{str(e)}")
    
    def clear_data(self):
        """Clear all data"""
        if messagebox.askyesno("Confirm", "Clear all loaded data?"):
            self.tree.delete(*self.tree.get_children())
            self.authors = []
            self.selected_authors.clear()
            self.stats_label.config(text="Ready | 0 authors loaded")
            self.log("Data cleared", "info")
