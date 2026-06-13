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
            ws = sheet.add_worksheet(title=title, rows="1000", cols=str(len(headers)))
            ws.append_row(headers)
        return ws
    
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
        """Upload articles to Google Sheets - SIMPLIFIED"""
        if not articles:
            return False
        
        # Simplified headers for articles
        headers = ["Author", "Article Title", "URL", "Category", "Publish Date", "Scraped_At"]
        
        # Create DataFrame with only necessary columns
        df = pd.DataFrame(articles)
        
        # Filter to only include headers that exist in data
        available_headers = [h for h in headers if h in df.columns]
        
        # Add missing headers with empty values
        for header in headers:
            if header not in df.columns:
                df[header] = ""
        
        df = df[headers]
        
        return self.save_to_sheet(
            sheet_name, 
            "Articles", 
            df.values.tolist(), 
            headers
        )
    
    def upload_authors(self, sheet_name: str, authors: List[Dict]) -> bool:
        """Upload authors to Google Sheets - SIMPLIFIED"""
        if not authors:
            return False
        
        # SIMPLIFIED HEADERS: Only essential columns with social URLs
        headers = [
            "Author Name", 
            "Profile URL", 
            "Role / Bio", 
            "Total Articles",
            "Email",
            "Twitter URL", 
            "LinkedIn URL"
        ]
        
        df = pd.DataFrame(authors)
        
        # Ensure all headers exist in DataFrame
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
        """Upload enhanced authors to Google Sheets - SIMPLIFIED"""
        if not enhanced_authors:
            return False
        
        # SIMPLIFIED HEADERS: Clean minimal set
        headers = [
            "Author Name", 
            "Profile URL", 
            "Role / Bio", 
            "Primary Topic", 
            "Total Articles", 
            "Publication Name",
            "Twitter URL", 
            "LinkedIn URL",
            "Social Source"
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
    
    def upload_direct_authors(self, sheet_name: str, authors: List[Dict]) -> bool:
        """Upload directly scraped authors (from scrape_authors_directly)"""
        if not authors:
            return False
        
        # Headers for direct author scraping
        headers = [
            "Author Name",
            "Profile URL",
            "Role / Bio",
            "Primary Topic",
            "Publication Name",
            "Twitter URL",
            "LinkedIn URL",
            "Social Source"
        ]
        
        df = pd.DataFrame(authors)
        
        # Ensure all headers exist
        for header in headers:
            if header not in df.columns:
                df[header] = ""
        
        # Add default values for missing columns
        if "Publication Name" not in df.columns:
            df["Publication Name"] = "The New York Times"
        if "Primary Topic" not in df.columns:
            df["Primary Topic"] = "General"
        if "Social Source" not in df.columns:
            df["Social Source"] = "Author Profile Page"
        
        df = df[headers]
        
        return self.save_to_sheet(
            sheet_name,
            "Direct_Authors",
            df.values.tolist(),
            headers
        )
    
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
    
    def clear_worksheet(self, sheet_name: str, worksheet_name: str) -> bool:
        """Clear all data from a worksheet (keep headers)"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            
            # Get headers
            headers = ws.row_values(1)
            
            # Clear everything
            ws.clear()
            
            # Restore headers
            if headers:
                ws.append_row(headers)
            
            return True
        except Exception as e:
            print(f"Error clearing worksheet: {e}")
            return False
    
    def append_data(self, sheet_name: str, worksheet_name: str, data: List[List]) -> bool:
        """Append data to existing worksheet"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            
            if data:
                ws.append_rows(data, value_input_option="RAW")
            
            return True
        except Exception as e:
            print(f"Error appending data: {e}")
            return False
    
    def update_cell(self, sheet_name: str, worksheet_name: str, row: int, col: int, value: str) -> bool:
        """Update a specific cell"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            ws.update_cell(row, col, value)
            return True
        except Exception as e:
            print(f"Error updating cell: {e}")
            return False
    
    def get_cell_value(self, sheet_name: str, worksheet_name: str, row: int, col: int) -> Optional[str]:
        """Get value from a specific cell"""
        if not self.client:
            if not self.connect():
                return None
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            return ws.cell(row, col).value
        except Exception as e:
            print(f"Error getting cell value: {e}")
            return None
    
    def batch_update(self, sheet_name: str, worksheet_name: str, updates: List[Dict]) -> bool:
        """Batch update multiple cells"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            
            # Prepare batch update
            cells = []
            for update in updates:
                cells.append({
                    'range': update.get('range'),
                    'values': [[update.get('value')]]
                })
            
            ws.batch_update(cells)
            return True
        except Exception as e:
            print(f"Error in batch update: {e}")
            return False
    
    def create_worksheet(self, sheet_name: str, worksheet_name: str, headers: List[str]) -> bool:
        """Create a new worksheet with headers"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.open_or_create(sheet_name)
            self.get_or_create_ws(sheet, worksheet_name, headers)
            return True
        except Exception as e:
            print(f"Error creating worksheet: {e}")
            return False
    
    def delete_worksheet(self, sheet_name: str, worksheet_name: str) -> bool:
        """Delete a worksheet"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            sheet.del_worksheet(ws)
            return True
        except Exception as e:
            print(f"Error deleting worksheet: {e}")
            return False
    
    def format_headers(self, sheet_name: str, worksheet_name: str) -> bool:
        """Format headers (bold)"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            sheet = self.client.open(sheet_name)
            ws = sheet.worksheet(worksheet_name)
            
            # Format header row
            ws.format('1:1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            # Auto-resize columns
            ws.columns_auto_resize(0, len(ws.row_values(1)))
            
            return True
        except Exception as e:
            print(f"Error formatting headers: {e}")
            return False
    
    def export_to_excel(self, sheet_name: str, worksheet_name: str, output_path: str) -> bool:
        """Export worksheet to Excel file"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            data = self.get_sheet_data(sheet_name, worksheet_name)
            if data:
                df = pd.DataFrame(data)
                df.to_excel(output_path, index=False)
                return True
            return False
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False


# Quick usage functions
def quick_upload_authors(sheet_name: str, authors: List[Dict], json_path: str = "data/google_creds.json"):
    """Quick function to upload authors"""
    manager = GoogleSheetsManager(json_path)
    return manager.upload_authors(sheet_name, authors)


def quick_upload_articles(sheet_name: str, articles: List[Dict], json_path: str = "data/google_creds.json"):
    """Quick function to upload articles"""
    manager = GoogleSheetsManager(json_path)
    return manager.upload_articles(sheet_name, articles)


def quick_get_authors(sheet_name: str, json_path: str = "data/google_creds.json") -> List[Dict]:
    """Quick function to get authors from sheet"""
    manager = GoogleSheetsManager(json_path)
    return manager.get_sheet_data(sheet_name, "Authors")
