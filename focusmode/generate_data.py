"""
Generate Fake Session Data
Project: Study Session Quality Predictor
-----------------------------------------
Generates 100 realistic fake study sessions into sessions.csv
Run once to populate data for ML training.
"""

import csv
import os
import random
from datetime import datetime, timedelta

DATA_FOLDER = "data"
CSV_FILE    = os.path.join(DATA_FOLDER, "sessions.csv")

CSV_HEADERS = [
    "Subject",
    "Start_Time",
    "Duration_Minutes",
    "Focus_Percentage",
    "Drowsy_Count",
    "Distracted_Count",
    "Quality_Label"
]

SUBJECTS = ["EOC", "EEE", "DSA", "UID", "MFC", "OOP", ]

# Subjects with difficulty weights (harder = more drowsy/distracted)
SUBJECT_DIFFICULTY = {
    "DSA": 5, "OOP": 4, "EEE": 4,
    "MFC": 3, "UID": 3,
    "EOC": 2, 
}

def generate_session(base_time, subject):
    """Generates one realistic fake session row."""

    difficulty = SUBJECT_DIFFICULTY[subject]
    hour       = base_time.hour

    # Morning sessions (8-11am) → better focus
    # Afternoon (2-4pm) → moderate
    # Night (9pm+) → worse focus
    if 8 <= hour <= 11:
        base_focus = random.uniform(75, 95)
    elif 14 <= hour <= 16:
        base_focus = random.uniform(60, 80)
    elif hour >= 21 or hour <= 5:
        base_focus = random.uniform(40, 65)
    else:
        base_focus = random.uniform(55, 80)

    # Harder subjects reduce focus
    base_focus -= (difficulty - 3) * 5
    base_focus = max(20, min(98, base_focus))

    duration      = round(random.uniform(15, 90), 1)
    focus_pct     = round(base_focus + random.uniform(-5, 5), 1)
    drowsy_count  = random.randint(0, int(difficulty * 1.5))
    distracted    = random.randint(0, int((100 - focus_pct) / 15))

    # Quality score formula
    quality = focus_pct - (drowsy_count * 2) - (distracted * 1)
    if duration < 5:
        quality -= 10
    quality = round(max(0, min(100, quality)), 1)

    return {
        "Subject":           subject,
        "Start_Time":        base_time.strftime("%Y-%m-%d %H:%M:%S"),
        "Duration_Minutes":  duration,
        "Focus_Percentage":  focus_pct,
        "Drowsy_Count":      drowsy_count,
        "Distracted_Count":  distracted,
        "Quality_Label":     quality
    }


def generate_all():
    os.makedirs(DATA_FOLDER, exist_ok=True)

    # Start from 30 days ago
    base_date = datetime.now() - timedelta(days=30)
    rows = []

    for i in range(100):
        # Spread sessions across last 30 days at realistic hours
        day_offset  = random.randint(0, 30)
        hour        = random.choice([8, 9, 10, 14, 15, 16, 19, 20, 21, 22])
        minute      = random.randint(0, 59)
        session_time = base_date + timedelta(days=day_offset, hours=hour, minutes=minute)

        subject = random.choice(SUBJECTS)
        row     = generate_session(session_time, subject)
        rows.append(row)

    # Sort by time
    rows.sort(key=lambda r: r["Start_Time"])

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated {len(rows)} fake sessions → saved to {CSV_FILE}")
    print("\nSample rows:")
    for row in rows[:5]:
        print(f"  {row['Start_Time']} | {row['Subject']:20s} | Focus: {row['Focus_Percentage']}% | Quality: {row['Quality_Label']}")


if __name__ == "__main__":
    generate_all()