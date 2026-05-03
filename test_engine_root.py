from backend.engine import TaskEngine
engine = TaskEngine()
print("tasks:", engine.data["tasks"])
print("goals:", engine.data["goals"])
import traceback
try:
    print(engine.get_top_urgent_tasks(4, 2))
except Exception as e:
    traceback.print_exc()
