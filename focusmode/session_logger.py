

import time
import csv
import os
import threading
from datetime import datetime
from circular_buffer import CircularBuffer
from webcam_monitor import WebcamMonitor



# CONSTANTS

DATA_FOLDER  = "data"
CSV_FILE     = os.path.join(DATA_FOLDER, "sessions.csv")
BUFFER_SIZE  = 300   # store last 300 seconds of attention states

# CSV column headers 

CSV_HEADERS = [
    "Subject",
    "Start_Time",
    "Duration_Minutes",
    "Focus_Percentage",
    "Drowsy_Count",
    "Distracted_Count",
    "Quality_Label"
]



#   Calculate Quality Score (0-100)

def calculate_quality_score(focus_pct, drowsy_count, distracted_count, duration_mins):
    """
    Simple formula to calculate session quality (0-100):
    - Higher focus % → higher score
    - More drowsy/distracted events → lower score
    - Penalty for very short sessions
    """
    score = focus_pct                          # start with focus percentage
    score -= (drowsy_count * 2)                # each drowsy event costs 2 points
    score -= (distracted_count * 1)            # each distracted event costs 1 point

    if duration_mins < 5:
        score -= 10                            # penalty for sessions under 5 mins

    score = max(0, min(100, score))            # clamp between 0 and 100
    return round(score, 1)



#  Setup CSV file

def setup_csv():
    """Creates the data folder and CSV file with headers if they don't exist."""
    os.makedirs(DATA_FOLDER, exist_ok=True)    # create data/ folder if missing

    if not os.path.exists(CSV_FILE):           # only write headers if file is new
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
        print(f" Created new CSV file at: {CSV_FILE}")
    else:
        print(f" Found existing CSV file at: {CSV_FILE}")



#  Save session to CSV

def save_session(subject, start_time, buffer):
    """
    Calculates session summary and saves it as one row in the CSV.
    """
    end_time       = time.time()
    duration_secs  = end_time - start_time
    duration_mins  = round(duration_secs / 60, 2)

    focus_pct      = round(buffer.focus_percentage(), 1)
    drowsy_cnt     = buffer.drowsy_count()
    distracted_cnt = buffer.distracted_count()
    quality        = calculate_quality_score(focus_pct, drowsy_cnt, distracted_cnt, duration_mins)

    # Format start time 
    start_str = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")

    row = {
        "Subject":           subject,
        "Start_Time":        start_str,
        "Duration_Minutes":  duration_mins,
        "Focus_Percentage":  focus_pct,
        "Drowsy_Count":      drowsy_cnt,
        "Distracted_Count":  distracted_cnt,
        "Quality_Label":     quality
    }

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(row)

    print("\n" + "="*50)
    print(" SESSION SUMMARY")
    print("="*50)
    print(f"  Subject:          {subject}")
    print(f"  Start Time:       {start_str}")
    print(f"  Duration:         {duration_mins} minutes")
    print(f"  Focus:            {focus_pct}%")
    print(f"  Drowsy Events:    {drowsy_cnt}")
    print(f"  Distracted:       {distracted_cnt}")
    print(f"  Quality Score:    {quality}/100")
    print("="*50)
    print(f" Saved to {CSV_FILE}")

    return row


# MAIN — SessionLogger class

class SessionLogger:
    def __init__(self, subject):
        self.subject    = subject
        self.buffer     = CircularBuffer(size=BUFFER_SIZE)
        self.monitor    = WebcamMonitor()
        self.running    = False
        self.start_time = None

    def _log_loop(self):
        """
        Runs in background thread — reads status every second
        and adds it to the circular buffer.
        """
        while self.running:
            status = self.monitor.get_status()   # get current status from webcam
            self.buffer.add(status)              # store in circular buffer

            # Print live stats every 10 seconds
            if self.buffer.count % 10 == 0 and self.buffer.count > 0:
                print(f"  ⏱ {self.buffer.count}s | "
                      f"Focus: {self.buffer.focus_percentage():.1f}% | "
                      f"Drowsy: {self.buffer.drowsy_count()} | "
                      f"Status: {status}")

            time.sleep(1)   # wait 1 second before next reading

    def run(self):
        """Starts the webcam + logging together."""
        setup_csv()

        print(f"\n Starting session for subject: {self.subject}")
        print("Press Q in the webcam window to end session\n")

        self.start_time = time.time()
        self.running    = True

        # Start logging in a background thread
        log_thread = threading.Thread(target=self._log_loop, daemon=True)
        log_thread.start()

        # Run webcam (this blocks until Q is pressed)
        self.monitor.run()

        # When webcam closes, stop logging
        self.running = False
        log_thread.join(timeout=2)

        # Save session to CSV
        save_session(self.subject, self.start_time, self.buffer)


# ENTRY POINT

if __name__ == "__main__":
    print("="*50)
    print("   STUDY SESSION QUALITY PREDICTOR")
    print("="*50)

    subject = input("\nEnter subject you are studying: ").strip()
    if not subject:
        subject = "General"

    logger = SessionLogger(subject)
    logger.run()