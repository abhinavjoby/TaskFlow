from backend.api import get_urgent_tasks
import json

tasks = get_urgent_tasks(10, 2)
print("Dumps:")
print(json.dumps(tasks))
