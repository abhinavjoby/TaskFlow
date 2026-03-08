import eel
import sys
import os
import uuid
from datetime import datetime
import tkinter as tk 

# TASK CLASS DEFINITIONS 

class Task:
    def __init__(self, title, subject, difficulty, energy, duration, deadline, notes="", parent_project=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.subject = subject
        self.difficulty = int(difficulty)
        self.energy = int(energy)
        self.duration = int(duration)
        self.deadline = datetime.fromisoformat(deadline)
        self.notes = [notes] if notes else []
        self.status = "pending"
        self.parent_project = parent_project
        self.priority_score = 0

    ## Priority Calculation Logic

    def calculate_priority(self, current_user_energy):
        # 1. Calculate T_rem (Time Remaining in minutes)
        now = datetime.now()
        time_diff = (self.deadline - now).total_seconds() / 60
        
        # 2. Handle the Deadline Paradox (Hard Override)
        # If time remaining is less than 1.5x the task duration, 
        # it bypasses all other logic to stay at the top.
        if time_diff <= (1.5 * self.duration):
            self.priority_score = -float('inf')  # Guaranteed #1 in Min-Heap
            return self.priority_score

        # 3. The Core Formula:
        # We want a LOWER score for HIGHER priority (Min-Heap logic).
        # We subtract (Energy * Difficulty) from Time Remaining.
        # Higher Energy/Difficulty = Lower Score = Higher Priority.
        
        weight_factor = 10 # Constant 
        adjustment = (current_user_energy * self.difficulty * weight_factor)
        
        self.priority_score = time_diff - adjustment
        return self.priority_score

class Goal:
    def __init__(self, title, category, metric_type, target_value, subject=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.category = category
        self.metric_type = metric_type
        self.target_value = target_value
        self.current_value = 0 if metric_type != "BOOLEAN" else False
        self.subject = subject
        self.created_at = datetime.now()

    def update_progress(self, value): 
        if self.metric_type == "BOOLEAN":
            self.current_value = True
        else:
            self.current_value += value
            
    def get_progress_percentage(self):
        if self.metric_type == "BOOLEAN":
            return 100 if self.current_value else 0
        if self.target_value == 0: return 0
        return min((self.current_value / self.target_value) * 100, 100)

class Project:
    def __init__(self, name, subject, notes=""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.subject = subject
        self.notes = notes
        self.task_ids = []
        self.dependency_map = {}
        
    def add_task(self, task_obj):
        self.task_ids.append(task_obj.id)
        task_obj.parent_project = self.id

    def get_completion_status(self, task_pool):
        if not self.task_ids: return 0
        completed = sum(1 for tid in self.task_ids if tid in task_pool and task_pool[tid].status == "done")
        return (completed / len(self.task_ids)) * 100

# EEL INITIALIZATION 

eel.init('web')

# Get exact screen resolution for window size
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()

launch_settings = {
    'size': (screen_width, screen_height), 
    'position': (0, 0),
    'mode': 'chrome',
    'shutdown_delay': 1000,
    'close_callback': None
}
# Attempt to set browser on macOS, with a fallback to default if it fails for other platforms or if the path is incorrect. For better compatibility.
try:
    if sys.platform == "darwin" and os.path.exists('/Applications/Comet.app'):
        eel.browsers.set_path('chrome', '/Applications/Comet.app/Contents/MacOS/Comet')
    eel.start('index.html', **launch_settings)
except Exception as e:
    print(f"Standard launch failed: {e}")
    launch_settings['mode'] = 'default'
    eel.start('index.html', **launch_settings)