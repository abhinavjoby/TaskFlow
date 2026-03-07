import eel
import sys
import os

eel.init('web')

# Portability Logic: Try to find a Chromium browser, fallback to default if not found
try:
    if sys.platform == "darwin": # macOS logic
        # If you want to keep using Comet locally, you can keep this, 
        # but the 'else' will handle teachers' Macs that have Chrome.
        comet_path = '/Applications/Comet.app/Contents/MacOS/Comet'
        if os.path.exists(comet_path):
            eel.browsers.set_path('chrome', comet_path)
    
    # Try starting in Chrome mode (standalone window)
    eel.start('index.html', size=(1280, 800), mode='chrome')

except (OSError, Exception):
    # FALLBACK: If Chrome/Comet isn't found, open in the teacher's default browser tab
    print("Chromium browser not found. Falling back to default browser...")
    eel.start('index.html', size=(1280, 800), mode='default')
    