import os
import sys
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.engine import TaskEngine
from backend.models import Task

engine = TaskEngine("test_tasks.json")

# Add some fake tasks
t1 = Task(title="Task 1", subject="Math", difficulty=5, energy_req=3, duration=60, deadline=(datetime.datetime.now() + datetime.timedelta(minutes=150)).isoformat()) 
t2 = Task(title="Task 2", subject="Science", difficulty=1, energy_req=1, duration=30, deadline=(datetime.datetime.now() + datetime.timedelta(minutes=32)).isoformat()) 

engine.add_task(t1)
engine.add_task(t2)

urgent, conflict = engine.get_top_urgent_tasks(limit=2, current_energy=2)
print("Conflict:", conflict)
print("Urgent count:", len(urgent))
for u in urgent:
    print(u['title'], u['p_score'])
    
os.remove("test_tasks.json")
