import datetime
import json

data = {
    "deadline": "2026-04-19T17:00:00.000Z"
}

try:
    print("Trying:", data["deadline"].replace("Z", "+00:00"))
    dt = datetime.datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
    print("Success:", dt)
except Exception as e:
    print("Error:", e)
