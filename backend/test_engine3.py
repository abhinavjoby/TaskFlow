import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.engine import TaskEngine
engine = TaskEngine()
print("tasks:", engine.data["tasks"])
print("goals:", engine.data["goals"])
