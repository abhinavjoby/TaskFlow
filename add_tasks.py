import json
import datetime
import uuid

data_file = "data/tasks.json"
with open(data_file, "r") as f:
    data = json.load(f)

now = datetime.datetime.now()

# Task A: High Diff (5), Far deadline (300 mins)
task_a_deadline = now + datetime.timedelta(minutes=300)
task_a_id = str(uuid.uuid4())
task_a = {
    "id": task_a_id,
    "title": "Build Architecture Plan",
    "subject": "CS500",
    "notes": ["Needs high energy"],
    "difficulty": 5,
    "energy_req": 5,
    "deadline": task_a_deadline.isoformat(),
    "duration": 60,
    "p_score": 0.0,
    "status": "Pending",
    "parent_refs": [],
    "created_at": now.isoformat()
}

# Task B: Low Diff (1), Near deadline (200 mins)
task_b_deadline = now + datetime.timedelta(minutes=200)
task_b_id = str(uuid.uuid4())
task_b = {
    "id": task_b_id,
    "title": "Reply to Emails",
    "subject": "General",
    "notes": ["Easy task"],
    "difficulty": 1,
    "energy_req": 1,
    "deadline": task_b_deadline.isoformat(),
    "duration": 15,
    "p_score": 0.0,
    "status": "Pending",
    "parent_refs": [],
    "created_at": now.isoformat()
}

data["tasks"][task_a_id] = task_a
data["tasks"][task_b_id] = task_b

with open(data_file, "w") as f:
    json.dump(data, f, indent=4)

print("Tasks added successfully.")
