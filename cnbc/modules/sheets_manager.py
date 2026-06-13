# modules/sheets_manager.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from typing import List, Dict, Optional


class GoogleSheetsManager:
    def __init__(self, json_path: str = "data/google_creds.json"):
        self.json_path = json_path
        self.client = None
    
    def connect(self) -> bool:
        """Connect to Google Sheets"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.json_path, scope)
            self.client = gspread.authorize(creds)
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def list_sheets(self) -> List[str]:
        """List all available spreadsheets"""
        if not self.client:
            if not self.connect():
                return []
        try:
            return [s.title for s in self.client.openall()]
        except Exception as e:
            print(f"Error listing sheets: {e}")
            return []
    
    def open_or_create(self, name: str):
        """Open existing sheet or create new one"""
        if not self.client:
            if not self.connect():
                return None
        
        try:
            return self.client.open(name)
        except Exception:
            return self.client.create(name)
    
    def get_or_create_ws(self, sheet, title: str, headers: List[str]):
        """Get or create worksheet with headers"""
        try:
            ws = sheet.worksheet(title)
            existing = ws.row_values(1)
            if existing != headers:
                ws.clear()
                ws.append_row(headers)
        except Exception:
            ws = sheet.add_worksheet(title=title, rows="1000", cols="20")
            ws.append_row(headers)
        return ws
    
    def upload_df(self, ws, df: pd.DataFrame):
        """Upload DataFrame to worksheet"""
        if not df.empty:
            ws.append_rows(df.values.tolist(), value_input_option="RAW")
    
    def load_worksheet(self, sheet_name: str, worksheet_name: str) -> Optional[List[Dict]]:
        """Load data from a specific worksheet"""
        if not self.client:
            if not self.connect():
                return None
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            return ws.get_all_records()
        except Exception as e:
            print(f"Error loading worksheet: {e}")
            return None
    
    def get_worksheet_names(self, sheet_name: str) -> List[str]:
        """Get all worksheet names in a spreadsheet"""
        if not self.client:
            if not self.connect():
                return []
        
        try:
            sheet = self.client.open(sheet_name)
            return [ws.title for ws in sheet.worksheets()]
        except Exception as e:
            print(f"Error getting worksheet names: {e}")
            return []
    
    def save_to_sheet(self, sheet_name: str, worksheet_name: str, data: List[List], headers: List[str]) -> bool:
        """Save data to Google Sheets"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.open_or_create(sheet_name)
            ws = self.get_or_create_ws(sheet, worksheet_name, headers)
            
            # Clear existing data (keep headers)
            ws.clear()
            ws.append_row(headers)
            
            # Add new data
            if data:
                ws.append_rows(data, value_input_option="RAW")
            
            return True
        except Exception as e:
            print(f"Error saving to sheet: {e}")
            return False
    
    def get_sheet_data(self, sheet_name: str, worksheet_name: str) -> Optional[List[Dict]]:
        """Get data from sheet as list of dicts"""
        if not self.client:
            if not self.connect():
                return None
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            return ws.get_all_records()
        except Exception as e:
            print(f"Error getting sheet data: {e}")
            return None
    
    def upload_articles(self, sheet_name: str, articles: List[Dict]) -> bool:
        """Upload articles to Google Sheets"""
        if not articles:
            return False
        
        headers = ["Author", "Article Title", "URL", "Category", "Publish Date"]
        df = pd.DataFrame(articles)[headers]
        
        return self.save_to_sheet(
            sheet_name, 
            "Articles", 
            df.values.tolist(), 
            headers
        )
    
    def upload_authors(self, sheet_name: str, authors: List[Dict]) -> bool:
    
        if not authors:
           return False
    
    
        headers = [
             "Author Name", "Profile URL", "Email", "Role / Bio", 
           "Contact Info", "Primary Topic", "Total Articles"
          ]
    
        df = pd.DataFrame(authors)
    
  
        for header in headers:
            if header not in df.columns:
                 df[header] = ""
    
        df = df[headers]
        return self.save_to_sheet(
              sheet_name, 
              "Authors", 
              df.values.tolist(), 
              headers
                 )
    
    def upload_enhanced_authors(self, sheet_name: str, enhanced_authors: List[Dict]) -> bool:
        """Upload enhanced authors to Google Sheets"""
        if not enhanced_authors:
            return False
        
        headers = [
            "Author Name", "Profile URL", "Role / Bio", "Primary Topic", 
            "Total Articles", "Activity Score", "Relevance Score", 
            "Validation Status", "Status Details", "Last Validated"
        ]
        
        df = pd.DataFrame(enhanced_authors)
        
        # Ensure all headers exist
        for header in headers:
            if header not in df.columns:
                df[header] = ""
        
        df = df[headers]
        return self.save_to_sheet(
            sheet_name, 
            "Enhanced_Authors", 
            df.values.tolist(), 
            headers
        )
