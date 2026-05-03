import eel
import os
import sys
import tkinter as tk

# Allow easy import from the same directory whether run from root or backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import api
from backend import focus

TK_SILENCE_DEPRECATION=1

def get_screen_resolution():
    root = tk.Tk()
    root.withdraw() # Hide the main tk window
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height

def start_app():
    # Setup eel to use the correct 'web' folder path
    # Back out of /backend up to /taskflow/web
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_dir = os.path.join(base_dir, 'web')
    
    if not os.path.exists(web_dir):
        print(f"Error: web folder not found at {web_dir}")
        sys.exit(1)
        
    eel.init(web_dir)
    
    # Get active resolution for fullscreen simulation
    width, height = get_screen_resolution()
    
    # Check if user has a profile
    has_profile = bool(api.engine.data["profile"].get("username"))
    start_page = 'index.html' if has_profile else 'onboarding.html'
    
    # Start window with a custom close_callback to tolerate refreshes
    def close_callback(page, sockets):
        if not sockets:
            import time
            import threading
            def delayed_exit():
                time.sleep(2) # 2 second grace period for page refresh
                if len(eel._websockets) == 0:
                    os._exit(0)
            threading.Thread(target=delayed_exit, daemon=True).start()

    eel.start(start_page, size=(width, height), position=(0, 0), port=0, mode='chrome', cmdline_args=['--incognito'], close_callback=close_callback)

if __name__ == '__main__':
    start_app()
