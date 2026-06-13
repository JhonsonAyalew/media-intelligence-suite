# main_outreach.py
import tkinter as tk
from ui.outreach_ui import OutreachApp

if __name__ == "__main__":
    root = tk.Tk()
    
    # Center window on screen
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 1200
    window_height = 700
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    app = OutreachApp(root)
    root.mainloop()
