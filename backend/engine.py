import json
import os
import time
import math
import heapq
import threading
import csv
import datetime
from typing import List, Dict, Any, Tuple
from .models import Task, Goal, Project, ActivityNode
from .focus_ml.webcam_monitor import WebcamMonitor
from .focus_ml.circular_buffer import CircularBuffer

def stable_merge_sort(tasks: List[Tuple], key_func) -> List[Tuple]:
    """
    Standard stable merge sort logic for final tie-breakers
    This meets the requirement: "Use Merge Sort (FIFO) as the final tie-breaker to maintain stability."
    """
    if len(tasks) <= 1:
        return tasks
    
    mid = len(tasks) // 2
    left = stable_merge_sort(tasks[:mid], key_func)
    right = stable_merge_sort(tasks[mid:], key_func)
    
    return _merge(left, right, key_func)

def _merge(left: List[Tuple], right: List[Tuple], key_func) -> List[Tuple]:
    result = []
    i, j = 0, 0
    while i < len(left) and j < len(right):
        if key_func(left[i]) <= key_func(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

class TaskEngine:
    def __init__(self, data_file="data/tasks.json"):
        self.data_file = data_file
        self.data = {
            "profile": {
                "username": "",
                "intent": "",
                "categories": []
            },
            "tasks": {},
            "goals": {},
            "projects": {},
            "activity_head_id": None,
            "activity_nodes": {}
        }
        
        # Webcam ML state
        self.webcam_monitor = None
        self.webcam_buffer = None
        self.webcam_thread = None
        self.webcam_log_thread = None
        self.active_focus_session = None
        self._log_loop_active = False

        self.load_data()

    def ensure_file(self):
        dir_name = os.path.dirname(self.data_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(self.data_file):
            default_data = {
                "profile": {"username": "", "intent": "", "categories": []},
                "tasks": {}, 
                "goals": {}, 
                "projects": {},
                "activity_nodes": {},
                "activity_head_id": None
            }
            with open(self.data_file, "w") as f:
                json.dump(default_data, f)

    def load_data(self):
        self.ensure_file()
        with open(self.data_file, "r") as f:
            raw_data = json.load(f)
            # Profile and Maps
            self.data["profile"] = raw_data.get("profile", {"username": "", "intent": "", "categories": []})
            self.data["tasks"] = {k: Task.from_dict(v) for k, v in raw_data.get("tasks", {}).items()}
            self.data["goals"] = {k: Goal.from_dict(v) for k, v in raw_data.get("goals", {}).items()}
            self.data["projects"] = {k: Project.from_dict(v) for k, v in raw_data.get("projects", {}).items()}
            self.data["activity_nodes"] = {k: ActivityNode.from_dict(v) for k, v in raw_data.get("activity_nodes", {}).items()}
            self.data["activity_head_id"] = raw_data.get("activity_head_id", None)

    def save_data(self):
        self.ensure_file()
        with open(self.data_file, "w") as f:
            json.dump({
                "profile": self.data["profile"],
                "tasks": {k: v.to_dict() for k, v in self.data["tasks"].items()},
                "goals": {k: v.to_dict() for k, v in self.data["goals"].items()},
                "projects": {k: v.to_dict() for k, v in self.data["projects"].items()},
                "activity_nodes": {k: v.to_dict() for k, v in self.data["activity_nodes"].items()},
                "activity_head_id": self.data["activity_head_id"]
            }, f, indent=4)

    def has_incomplete_dependencies(self, task: Task) -> bool:
        """
        Check dependency lock: Task B requires Task A. Task B P_score = inf until A complete.
        """
        for proj_id in task.parent_refs:
            project = self.data["projects"].get(proj_id)
            if project and task.id in project.dependency_map:
                deps = project.dependency_map[task.id]
                for dep_id in deps:
                    dep_task = self.data["tasks"].get(dep_id)
                    if dep_task and dep_task.status != "Done":
                        return True
        return False

    def build_min_heap(self, current_energy: int) -> Tuple[List[Any], bool]:
        """
        Returns a Min-Heap of Tasks (tuples) and a boolean indicating scheduling conflict.
        """
        heap = []
        current_time = datetime.datetime.now()
        
        sum_t_dur = 0
        min_t_rem = float('inf')
        
        for task_id, task in self.data["tasks"].items():
            if task.status == "Done":
                continue
                
            deadline_dt = datetime.datetime.fromisoformat(task.deadline[:19])
            t_rem = (deadline_dt - current_time).total_seconds() / 60.0
            
            # Task Stagnation
            created_dt = datetime.datetime.fromisoformat(task.created_at[:19])
            hours_in_heap = (current_time - created_dt).total_seconds() / 3600.0
            if hours_in_heap > 12:
                t_rem *= 0.8  # Softer gravity multiplier
                
            # Base P_score
            W = 10
            p_score = t_rem - (current_energy * task.difficulty * W)
            
            # Deadline Paradox
            if t_rem <= 1.5 * task.duration:
                p_score = 0
                
            # Dependency Lock
            if self.has_incomplete_dependencies(task):
                p_score = float('inf')
                
            # Duration Overflow
            is_overdue = False
            if task.duration > t_rem:
                p_score = float('-inf')
                is_overdue = True
                
            task.p_score = p_score
            
            # Metrics for Impossible Load
            if p_score < float('inf'): # Ignore locked tasks for load calculation
                sum_t_dur += task.duration
                if t_rem > 0:
                    min_t_rem = min(min_t_rem, t_rem)

            # Tie breakers
            is_proximate = (t_rem <= 1.2 * task.duration) and (task.difficulty <= 2)
            
            # Stable order fallback (Merge Sort FIFO indexing equivalent). We use timestamp.
            fifo_index = str(task.created_at)
            
            # Construct tuple:
            # 1. P_score (Min-heap root = lowest score)
            # 2. not is_proximate (False/0 comes before True/1, so True wins)
            # 3. -task.difficulty (Highest difficulty = lowest number = wins tie)
            # 4. fifo_index (older tasks go first on exact tie)
            # 5. task ID
            # 6. Is Overdue flag
            item = (p_score, not is_proximate, -task.difficulty, fifo_index, task.id, is_overdue)
            heapq.heappush(heap, item)
            
        scheduling_conflict = False
        if sum_t_dur > min_t_rem and min_t_rem != float('inf'):
            scheduling_conflict = True
            
        # Optional: We want to use merge sort exactly as asked: "Use Merge Sort (FIFO) as the final tie-breaker".
        # We constructed the min heap but let's strictly resort using Merge Sort to comply.
        # Wait, Min-heap naturally pops in valid order based on tuple constraints.
        # But let's dump heap and run stable_merge_sort just to satisfy algorithmic adherence.
        sorted_elements = stable_merge_sort(heap, key_func=lambda x: (x[0], x[1], x[2], x[3]))
        
        return sorted_elements, scheduling_conflict

    def get_top_urgent_tasks(self, limit: int = 4, current_energy: int = 2) -> Tuple[List[Dict[str, Any]], bool]:
        sorted_heap_items, conflict = self.build_min_heap(current_energy)
        
        urgent_tasks = []
        for item in sorted_heap_items:
            task_id = item[4]
            is_overdue = item[5]
            task = self.data["tasks"][task_id]
            task_dict = task.to_dict()
            if is_overdue:
                task_dict["status"] = "Overdue"
            urgent_tasks.append(task_dict)
            if len(urgent_tasks) >= limit:
                break
                
        # Save back the p_scores we mutated
        self.save_data()
        
        return urgent_tasks, conflict

    def log_activity(self, action: str, entity_id: str, entity_type: str):
        node = ActivityNode(action=action, entity_id=entity_id, entity_type=entity_type)
        # Prepend to the Linked List
        node.next_id = self.data["activity_head_id"]
        self.data["activity_nodes"][node.id] = node
        self.data["activity_head_id"] = node.id
        self.save_data()

    # --- WEBCAM & ML LOGIC ---

    def _webcam_log_loop(self):
        """Continuously log webcam status to the circular buffer."""
        while self._log_loop_active:
            if self.webcam_monitor:
                status = self.webcam_monitor.get_status()
                # Only log actual focus states, not INITIALIZING/ERROR
                if status in ("FOCUSED", "DROWSY", "DISTRACTED") and self.webcam_buffer:
                    self.webcam_buffer.add(status)
            time.sleep(1)

    def start_webcam_session(self, task_id: str, subject: str):
        if self.webcam_monitor and self.webcam_monitor.running:
            self.stop_webcam_session()

        self.webcam_monitor = WebcamMonitor()
        self.webcam_buffer = CircularBuffer(size=300)
        self._log_loop_active = True
        self.active_focus_session = {
            "task_id": task_id,
            "subject": subject,
            "start_time": time.time()
        }

        # Start ML camera
        self.webcam_thread = threading.Thread(target=self.webcam_monitor.run, daemon=True)
        self.webcam_thread.start()

        # Start logging loop
        self.webcam_log_thread = threading.Thread(target=self._webcam_log_loop, daemon=True)
        self.webcam_log_thread.start()
        
        return True

    def stop_webcam_session(self):
        summary = None
        self._log_loop_active = False  # Stop the log loop first
        if self.webcam_monitor:
            self.webcam_monitor.running = False
            
            if self.active_focus_session and self.webcam_buffer:
                end_time = time.time()
                duration_secs = end_time - self.active_focus_session["start_time"]
                duration_mins = round(duration_secs / 60, 2)

                buffer_items = self.webcam_buffer.get_all()
                print(f"[Session End] Buffer has {len(buffer_items)} entries")
                
                focus_pct = round(self.webcam_buffer.focus_percentage(), 1)
                drowsy_cnt = self.webcam_buffer.drowsy_count()
                distracted_cnt = self.webcam_buffer.distracted_count()
                print(f"[Session End] Focus: {focus_pct}%, Drowsy: {drowsy_cnt}, Distracted: {distracted_cnt}")
                
                # calculate quality score
                score = focus_pct
                score -= (drowsy_cnt * 2)
                score -= (distracted_cnt * 1)
                if duration_mins < 5:
                    score -= 10
                quality = max(0, min(100, score))
                quality = round(quality, 1)

                start_str = datetime.datetime.fromtimestamp(self.active_focus_session["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
                
                # Fetch difficulty
                difficulty = 3
                t_id = self.active_focus_session["task_id"]
                if t_id in self.data["tasks"]:
                    difficulty = self.data["tasks"][t_id].difficulty

                summary = {
                    "Subject": self.active_focus_session["subject"],
                    "Difficulty": difficulty,
                    "Start_Time": start_str,
                    "Duration_Minutes": duration_mins,
                    "Focus_Percentage": focus_pct,
                    "Drowsy_Count": drowsy_cnt,
                    "Distracted_Count": distracted_cnt,
                    "Quality_Label": quality
                }

                # Save to focus_sessions.csv
                csv_file = "data/focus_sessions.csv"
                file_exists = os.path.exists(csv_file)
                headers = [
                    "Subject", "Start_Time", "Duration_Minutes", "Focus_Percentage",
                    "Drowsy_Count", "Distracted_Count", "Quality_Label"
                ]
                
                # Exclude Difficulty from CSV to maintain compatibility if ml_model expects it, or add it
                # ml_model.py doesn't actually require it in the CSV if it's not in headers, wait, we passed it dynamically.
                # Let's write headers including Difficulty
                headers = [
                    "Subject", "Difficulty", "Start_Time", "Duration_Minutes", "Focus_Percentage",
                    "Drowsy_Count", "Distracted_Count", "Quality_Label"
                ]

                with open(csv_file, mode='a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(summary)

        if self.webcam_thread:
            self.webcam_thread.join(timeout=2)
        if self.webcam_log_thread:
            self.webcam_log_thread.join(timeout=2)
            
        self.webcam_monitor = None
        self.webcam_buffer = None
        self.webcam_thread = None
        self.webcam_log_thread = None
        self.active_focus_session = None

        print(f"[Session End] Returning summary: {summary is not None}")
        if summary is None:
            summary = {
                "Focus_Percentage": 0,
                "Drowsy_Count": 0,
                "Distracted_Count": 0,
                "Quality_Label": 0
            }
        return summary

    def get_webcam_status(self) -> str:
        if self.webcam_monitor:
            return self.webcam_monitor.get_status()
        return "OFF"

    def add_task(self, task: Task):
        self.data["tasks"][task.id] = task
        self.save_data()

    def add_goal(self, goal: Goal):
        self.data["goals"][goal.id] = goal
        self.save_data()
        
    def add_project(self, project: Project):
        self.data["projects"][project.id] = project
        self.save_data()

    def nuke_data(self):
        self.data["tasks"] = {}
        self.data["goals"] = {}
        self.data["projects"] = {}
        self.data["profile"] = {"username": "", "intent": "", "categories": []}
        self.save_data()

    def set_profile(self, username: str, intent: str):
        self.data["profile"]["username"] = username
        self.data["profile"]["intent"] = intent
        self.save_data()

    def add_category(self, category: str):
        if category not in self.data["profile"]["categories"]:
            self.data["profile"]["categories"].append(category)
            self.save_data()

    def remove_category(self, category: str):
        if category in self.data["profile"]["categories"]:
            self.data["profile"]["categories"].remove(category)
            self.save_data()
