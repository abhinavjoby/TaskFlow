import time
import eel

class FocusSession:
    def __init__(self):
        self.is_active = False
        self.start_time = None
        self.accumulated_time = 0
        
    def start(self):
        if not self.is_active:
            self.is_active = True
            self.start_time = time.time()
            return True
        return False
        
    def pause(self):
        if self.is_active:
            self.accumulated_time += time.time() - self.start_time
            self.is_active = False
            return True
        return False
            
    def stop(self):
        self.pause()
        total_minutes = self.accumulated_time / 60.0
        self.accumulated_time = 0
        return total_minutes

tracker = FocusSession()

@eel.expose
def start_focus():
    return tracker.start()

@eel.expose
def pause_focus():
    return tracker.pause()

@eel.expose
def stop_focus():
    return tracker.stop()
