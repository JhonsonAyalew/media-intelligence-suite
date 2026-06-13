# ui/settings_dialog.py
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
import json
from modules.config_manager import ConfigManager


class SettingsDialog:
    def __init__(self, parent, config, on_save):
        self.parent = parent
        self.config = config
        self.on_save = on_save
        self.create_dialog()
    
    def create_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Email Settings Tab
        self.create_email_tab(notebook)
        
        # Template Settings Tab
        self.create_template_tab(notebook)
        
        # Google Sheets Tab
        self.create_sheets_tab(notebook)
        
        # UI Settings Tab
        self.create_ui_tab(notebook)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Save", command=self.save_settings).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side="right", padx=5)
    
    def create_email_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Email")
        
        # SMTP Settings
        ttk.Label(frame, text="SMTP Settings", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w")
        
        ttk.Label(frame, text="SMTP Server:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.smtp_server = ttk.Entry(frame, width=40)
        self.smtp_server.grid(row=1, column=1, padx=10, pady=5)
        self.smtp_server.insert(0, self.config.get('smtp_server', ''))
        
        ttk.Label(frame, text="SMTP Port:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.smtp_port = ttk.Entry(frame, width=40)
        self.smtp_port.grid(row=2, column=1, padx=10, pady=5)
        self.smtp_port.insert(0, str(self.config.get('smtp_port', '')))
        
        ttk.Label(frame, text="Email Address:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.email_address = ttk.Entry(frame, width=40)
        self.email_address.grid(row=3, column=1, padx=10, pady=5)
        self.email_address.insert(0, self.config.get('email_address', ''))
        
        ttk.Label(frame, text="App Password:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.email_password = ttk.Entry(frame, width=40, show="*")
        self.email_password.grid(row=4, column=1, padx=10, pady=5)
        self.email_password.insert(0, self.config.get('email_password', ''))
        
        # Sender Info
        ttk.Label(frame, text="Sender Information", font=("Arial", 11, "bold")).grid(row=5, column=0, columnspan=2, pady=(20, 5), sticky="w")
        
        ttk.Label(frame, text="Your Name:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.your_name = ttk.Entry(frame, width=40)
        self.your_name.grid(row=6, column=1, padx=10, pady=5)
        self.your_name.insert(0, self.config.get('sender_info', {}).get('your_name', ''))
        
        ttk.Label(frame, text="Your Position:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.your_position = ttk.Entry(frame, width=40)
        self.your_position.grid(row=7, column=1, padx=10, pady=5)
        self.your_position.insert(0, self.config.get('sender_info', {}).get('your_position', ''))
        
        ttk.Label(frame, text="Company Name:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.company_name = ttk.Entry(frame, width=40)
        self.company_name.grid(row=8, column=1, padx=10, pady=5)
        self.company_name.insert(0, self.config.get('sender_info', {}).get('company_name', ''))
    
    def create_template_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Templates")
        
        # Subject
        ttk.Label(frame, text="Email Subject:", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(10, 5))
        self.email_subject = ttk.Entry(frame, width=60)
        self.email_subject.pack(fill="x", padx=10, pady=(0, 10))
        template = self.config.get('email_templates', {}).get('default', {})
        self.email_subject.insert(0, template.get('subject', ''))
        
        # Body
        ttk.Label(frame, text="Email Body:", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(0, 5))
        
        body_frame = ttk.Frame(frame)
        body_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Variables info
        vars_frame = ttk.LabelFrame(body_frame, text="Available Variables", padding=5)
        vars_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(vars_frame, text="{author_name} - Author's name\n{topic} - Primary topic\n{your_name} - Your name\n{your_position} - Your position\n{company_name} - Company name").pack()
        
        # Text editor
        self.email_body = ScrolledText(body_frame, height=15, wrap="word", font=("Arial", 10))
        self.email_body.pack(fill="both", expand=True)
        self.email_body.insert("1.0", template.get('body', ''))
    
    def create_sheets_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Google Sheets")
        
        ttk.Label(frame, text="Google Sheets Settings", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w")
        
        ttk.Label(frame, text="Credentials JSON File:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        creds_frame = ttk.Frame(frame)
        creds_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.creds_file = ttk.Entry(creds_frame, width=35)
        self.creds_file.pack(side="left", fill="x", expand=True)
        self.creds_file.insert(0, self.config.get('google_creds_file', ''))
        
        ttk.Button(creds_frame, text="Browse", width=8, 
                  command=self.browse_creds_file).pack(side="right", padx=(5, 0))
        
        ttk.Label(frame, text="Sheet Name:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.sheet_name = ttk.Entry(frame, width=40)
        self.sheet_name.grid(row=2, column=1, padx=10, pady=5)
        self.sheet_name.insert(0, self.config.get('sheet_name', ''))
    
    def create_ui_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="UI Settings")
        
        ttk.Label(frame, text="Theme:", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(10, 5))
        self.theme_var = tk.StringVar(value=self.config.get('ui_settings', {}).get('theme', 'light'))
        theme_combo = ttk.Combobox(frame, textvariable=self.theme_var, values=["light", "dark"], width=20, state="readonly")
        theme_combo.pack(anchor="w", padx=10, pady=(0, 10))
        
        ttk.Label(frame, text="Font Size:", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(0, 5))
        self.font_size_var = tk.StringVar(value=str(self.config.get('ui_settings', {}).get('font_size', 10)))
        font_size_combo = ttk.Combobox(frame, textvariable=self.font_size_var, values=["9", "10", "11", "12"], width=20, state="readonly")
        font_size_combo.pack(anchor="w", padx=10, pady=(0, 10))
        
        self.auto_save_var = tk.BooleanVar(value=self.config.get('ui_settings', {}).get('auto_save', True))
        ttk.Checkbutton(frame, text="Auto-save templates", variable=self.auto_save_var).pack(anchor="w", padx=10, pady=(0, 10))
    
    def browse_creds_file(self):
        filename = filedialog.askopenfilename(
            title="Select Google Credentials JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.creds_file.delete(0, tk.END)
            self.creds_file.insert(0, filename)
    
    def save_settings(self):
        # Update config
        self.config['smtp_server'] = self.smtp_server.get()
        self.config['smtp_port'] = int(self.smtp_port.get())
        self.config['email_address'] = self.email_address.get()
        self.config['email_password'] = self.email_password.get()
        
        # Update sender info
        self.config['sender_info'] = {
            'your_name': self.your_name.get(),
            'your_position': self.your_position.get(),
            'company_name': self.company_name.get()
        }
        
        # Update templates
        self.config['email_templates'] = {
            'default': {
                'subject': self.email_subject.get(),
                'body': self.email_body.get("1.0", "end-1c")
            }
        }
        
        # Update Google Sheets
        self.config['google_creds_file'] = self.creds_file.get()
        self.config['sheet_name'] = self.sheet_name.get()
        
        # Update UI settings
        self.config['ui_settings'] = {
            'theme': self.theme_var.get(),
            'font_size': int(self.font_size_var.get()),
            'auto_save': self.auto_save_var.get()
        }
        
        # Save and notify
        ConfigManager.save_outreach_config(self.config)
        self.on_save(self.config)
        self.dialog.destroy()
        messagebox.showinfo("Success", "Settings saved successfully!")
