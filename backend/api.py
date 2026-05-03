import eel
from .engine import TaskEngine
from .models import Task
from typing import Dict, Any, List

# Initialize core engine
engine = TaskEngine()

@eel.expose
def create_task(task_data: Dict[str, Any]) -> str:
    """Create a new task from frontend dictionary payload."""
    try:
        # Handle some mapping if needed or rely on kwargs
        task = Task.from_dict(task_data)
        engine.add_task(task)
        return task.id
    except Exception as e:
        return f"Error: {str(e)}"

@eel.expose
def get_urgent_tasks(limit: int = 4, current_energy: int = 2) -> Dict[str, Any]:
    """Retrieve top urgent tasks for the sidebar."""
    tasks, conflict = engine.get_top_urgent_tasks(limit, current_energy)
    return {
        "tasks": tasks,
        "conflict": conflict
    }

@eel.expose
def get_all_tasks() -> List[Dict[str, Any]]:
    """Retrieve all tasks for discovery page."""
    tasks = []
    for k, v in engine.data["tasks"].items():
        tasks.append(v.to_dict())
    return tasks

@eel.expose
def get_all_goals() -> List[Dict[str, Any]]:
    import datetime
    now = datetime.datetime.now()
    goals_to_delete = []
    
    for gid, g in list(engine.data["goals"].items()):
        # Check completion for "Never" goals
        is_completed = (g.metric_type == "BOOLEAN" and g.current_value) or \
                       (g.metric_type in ["COUNT", "DURATION"] and g.current_value >= g.target_value)
        
        if g.reset_period == "Never" and is_completed:
            goals_to_delete.append(gid)
            continue
            
        # Reset logic
        if not is_completed:
            continue
            
        try:
            last_up = datetime.datetime.fromisoformat(g.last_updated)
        except ValueError:
            last_up = now
            
        needs_reset = False
        if g.reset_period == "Daily" and last_up.date() < now.date():
            needs_reset = True
        elif g.reset_period == "Weekly" and (now - last_up).days >= 7:
            needs_reset = True
        elif g.reset_period == "Monthly" and (now.year > last_up.year or now.month > last_up.month):
            needs_reset = True
            
        if needs_reset:
            g.current_value = False if g.metric_type == "BOOLEAN" else 0
            # Do NOT update last_updated here, so it accurately reflects when they actually worked on it last
            
    # Delete completed "Never" goals
    for gid in goals_to_delete:
        del engine.data["goals"][gid]
        
    if goals_to_delete:
        engine.save_data()
        
    return [v.to_dict() for v in engine.data["goals"].values()]

@eel.expose
def get_all_projects() -> List[Dict[str, Any]]:
    return [v.to_dict() for v in engine.data["projects"].values()]

@eel.expose
def update_task_status(task_id: str, new_status: str) -> bool:
    """Update task completion status."""
    if task_id in engine.data["tasks"]:
        t = engine.data["tasks"][task_id]
        if new_status == "Completed":
            engine.log_activity(f"Completed Task: {t.title} - {t.subject}", task_id, "Task")
            # Remove completed tasks visually passing to activity list entirely
            del engine.data["tasks"][task_id]
        elif new_status == "Ongoing":
            engine.log_activity(f"Ongoing Task: {t.title} - {t.subject}", task_id, "Task")
            engine.data["tasks"][task_id].status = new_status
        elif new_status == "Overdue":
            engine.log_activity(f"Overdue Task: {t.title} - {t.subject}", task_id, "Task")
            engine.data["tasks"][task_id].status = new_status
        else:
            engine.data["tasks"][task_id].status = new_status
        engine.save_data()
        return True
    return False

@eel.expose
def add_task(payload: Dict[str, Any]) -> bool:
    from .models import Task
    t = Task(
        title=payload["title"],
        subject=payload["subject"],
        difficulty=payload["difficulty"],
        energy_req=payload["energy_req"],
        deadline=payload["deadline"],
        duration=payload["duration"]
    )
    t.notes = payload.get("notes", [])
    t.parent_refs = payload.get("parent_refs", [])
    engine.add_task(t)
    return True

@eel.expose
def add_goal(payload: Dict[str, Any]) -> bool:
    from .models import Goal
    g = Goal(
        title=payload["title"],
        category=payload["category"],
        metric_type=payload["metric_type"],
        target_value=payload["target_value"],
        current_value=payload["current_value"],
        reset_period=payload["reset_period"]
    )
    engine.add_goal(g)
    return True

import datetime

@eel.expose
def increment_goal(goal_id: str) -> bool:
    if goal_id in engine.data["goals"]:
        goal = engine.data["goals"][goal_id]
        
        # Prevent incrementing if already completed
        if (goal.metric_type == "BOOLEAN" and goal.current_value) or \
           (goal.metric_type in ["COUNT", "DURATION"] and goal.current_value >= goal.target_value):
            return False
            
        if goal.metric_type == "BOOLEAN":
            goal.current_value = True
        elif goal.metric_type in ["COUNT", "DURATION"]:
            goal.current_value += 1
            
        goal.last_updated = datetime.datetime.now().isoformat()
        
        # If the goal was just completed by this increment
        if (goal.metric_type == "BOOLEAN" and goal.current_value) or \
           (goal.metric_type in ["COUNT", "DURATION"] and goal.current_value >= goal.target_value):
            engine.log_activity(f"Completed Goal: {goal.title}", goal.id, "Goal")
        else:
            # Log the increment as activity
            engine.log_activity(f"Updated Goal: {goal.title} ({goal.current_value}/{goal.target_value})", goal.id, "Goal")
            
        engine.save_data()
        return True
    return False

@eel.expose
def add_project(payload: Dict[str, Any]) -> bool:
    from .models import Project
    p = Project(
        name=payload["name"],
        subject=payload["subject"],
        overall_notes=payload["overall_notes"]
    )
    engine.add_project(p)
    return True

@eel.expose
def log_focus_session(name: str, category: str, duration: int) -> bool:
    # Just generating a UUID for the session instance logic
    import uuid
    session_id = str(uuid.uuid4())
    engine.log_activity(f"Focus Session: {name} ({duration}m) - {category}", session_id, "Focus")
    return True

@eel.expose
def check_user_profile() -> bool:
    """Zero-state onboarding check."""
    # Check if a user profile exists.
    return bool(engine.data["profile"].get("username"))

@eel.expose
def set_user_profile(username: str, intent: str) -> bool:
    engine.set_profile(username, intent)
    return True

@eel.expose
def get_user_profile() -> Dict[str, Any]:
    return engine.data["profile"]

@eel.expose
def set_theme(theme: str) -> bool:
    if "profile" not in engine.data:
        engine.data["profile"] = {}
    engine.data["profile"]["theme"] = theme
    engine.save_data()
    return True

@eel.expose
def add_category(category: str) -> List[str]:
    engine.add_category(category)
    return engine.data["profile"]["categories"]

@eel.expose
def remove_category(category: str) -> List[str]:
    engine.remove_category(category)
    return engine.data["profile"]["categories"]

@eel.expose
def nuke_data() -> bool:
    """Nuke functionality as specified in profile dropdown"""
    engine.nuke_data()
    return True

@eel.expose
def get_activity_log() -> List[Dict[str, Any]]:
    activities = []
    current_id = engine.data["activity_head_id"]
    while current_id and current_id in engine.data["activity_nodes"]:
        node = engine.data["activity_nodes"][current_id]
        activity_dict = node.to_dict()
        
        # Defaults
        name = "-"
        subj = "General"
        duration = "-"
        deadline = "-"
        status = "Completed"
        entity_type = node.entity_type  # Task, Goal, Focus, Project
        
        # Determine status from action string
        if "Ongoing" in node.action:
            status = "Ongoing"
        elif "Overdue" in node.action:
            status = "Overdue"
        elif "Updated" in node.action:
            status = "Ongoing"
        elif "Created" in node.action:
            status = "Pending"
        
        if node.entity_type == "Task":
            if node.entity_id in engine.data["tasks"]:
                t = engine.data["tasks"][node.entity_id]
                name = t.title
                subj = t.subject
                duration = "-"  # Don't show planned duration
                deadline = t.deadline[:10] if t.deadline else "-"
                if "Created" in node.action:
                    status = t.status
            else:
                # Task was deleted/completed, try to parse from action string
                if ":" in node.action:
                    parts = node.action.split(":", 1)[1].strip()
                    if " - " in parts:
                        name, subj = parts.split(" - ", 1)
                        name = name.strip()
                        subj = subj.strip()
                    else:
                        name = parts
        elif node.entity_type == "Goal" and node.entity_id in engine.data["goals"]:
            g = engine.data["goals"][node.entity_id]
            name = g.title
            subj = g.category
        elif node.entity_type == "Project":
            for pid, p in engine.data["projects"].items():
                if pid == node.entity_id:
                    name = p.name if hasattr(p, 'name') else str(p)
                    subj = p.subject if hasattr(p, 'subject') else "General"
                    break
        elif node.entity_type == "Focus":
            # Parse "Focus Session: Name (XXm) - Category"
            action = node.action
            if " - " in action:
                subj = action.split(" - ")[-1]
            if ":" in action:
                after_colon = action.split(":", 1)[1].strip()
                # Extract name and duration
                if "(" in after_colon:
                    name = after_colon.split("(")[0].strip()
                    dur_part = after_colon.split("(")[1].split(")")[0]  # e.g. "23m"
                    duration = dur_part
                else:
                    name = after_colon.split(" - ")[0].strip() if " - " in after_colon else after_colon
            status = "Ongoing"
        
        # Fallback name from action if still "-"
        if name == "-":
            name = node.action
        
        activity_dict["name"] = name
        activity_dict["subject"] = subj
        activity_dict["duration"] = duration
        activity_dict["deadline"] = deadline
        activity_dict["status"] = status
        activity_dict["entity_type"] = entity_type.lower()
        
        activities.append(activity_dict)
        current_id = node.next_id
        
    return activities

@eel.expose
def get_focus_stats(period: str = "all") -> Dict[str, Any]:
    import os
    import pandas as pd
    
    csv_file = "data/focus_sessions.csv"
    if not os.path.exists(csv_file):
        return {"timeline": [], "subjects": [], "summary": {"total_hours": 0, "avg_focus_score": 0, "total_sessions": 0, "completion_pct": 0}}
    
    df = pd.read_csv(csv_file)
    if len(df) == 0:
        return {"timeline": [], "subjects": [], "summary": {"total_hours": 0, "avg_focus_score": 0, "total_sessions": 0, "completion_pct": 0}}
    
    df["Start_Time"] = pd.to_datetime(df["Start_Time"])
    
    df_all = df.copy()
    
    # Filter by period
    now = pd.Timestamp.now()
    if period == "week":
        df = df[df["Start_Time"] >= now - pd.Timedelta(days=7)]
    elif period == "month":
        df = df[df["Start_Time"] >= now - pd.Timedelta(days=30)]
    
    # Calculate all-time summary
    all_total_hours = int(round(df_all["Duration_Minutes"].sum() / 60)) if len(df_all) > 0 else 0
    all_avg_score = int(round(df_all["Quality_Label"].mean())) if len(df_all) > 0 else 0
    all_total_sessions = len(df_all)
    
    # Completion %
    current_tasks_count = len(engine.data.get("tasks", {}))
    completed_tasks = sum(1 for v in engine.data.get("activity_nodes", {}).values() if v.action.startswith("Completed Task"))
    total_tasks = current_tasks_count + completed_tasks
    completion_pct = int(round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0))

    all_time_summary = {
        "total_hours": all_total_hours,
        "avg_focus_score": all_avg_score,
        "total_sessions": all_total_sessions,
        "completion_pct": completion_pct
    }
    
    if len(df) == 0:
        return {"timeline": [], "subjects": [], "summary": {"total_hours": 0, "avg_focus_score": 0, "total_sessions": 0, "completion_pct": completion_pct}, "all_time_summary": all_time_summary}
    
    # Timeline: group by date, avg quality score
    df["date_str"] = df["Start_Time"].dt.strftime("%b %d")
    timeline_df = df.groupby("date_str").agg(
        score=("Quality_Label", "mean"),
        date_sort=("Start_Time", "min")
    ).reset_index()
    timeline_df = timeline_df.sort_values("date_sort")
    timeline = [{"date": row["date_str"], "score": round(row["score"], 1)} for _, row in timeline_df.iterrows()]
    
    # Subjects: avg focus % and total hours per subject
    pill_colors = ["--pillColor1","--pillColor2","--pillColor3","--pillColor4","--pillColor5","--pillColor6","--pillColor7","--pillColor8"]
    subj_df = df.groupby("Subject").agg(
        avg_focus=("Focus_Percentage", "mean"),
        total_mins=("Duration_Minutes", "sum")
    ).reset_index()
    subjects = []
    for i, row in subj_df.iterrows():
        subjects.append({
            "name": row["Subject"],
            "avg_focus": round(row["avg_focus"], 1),
            "total_hours": round(row["total_mins"] / 60, 1),
            "color": f"var({pill_colors[i % len(pill_colors)]})"
        })
    
    # Summary (Filtered)
    total_hours = int(round(df["Duration_Minutes"].sum() / 60))
    avg_score = int(round(df["Quality_Label"].mean()))
    total_sessions = len(df)
    
    return {
        "timeline": timeline,
        "subjects": subjects,
        "summary": {
            "total_hours": total_hours,
            "avg_focus_score": avg_score,
            "total_sessions": total_sessions,
            "completion_pct": completion_pct
        },
        "all_time_summary": all_time_summary
    }

@eel.expose
def add_global_note(content: str) -> bool:
    if "notes" not in engine.data["profile"]:
        engine.data["profile"]["notes"] = []
    
    note_obj = {
        "content": content,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    engine.data["profile"]["notes"].append(note_obj)
    engine.save_data()
    return True

@eel.expose
def get_all_notes() -> list:
    return engine.data["profile"].get("notes", [])

@eel.expose
def update_user_energy(level: int) -> bool:
    engine.data["profile"]["energy"] = level
    engine.save_data()
    return True

@eel.expose
def start_webcam_session(task_id: str, subject: str) -> bool:
    try:
        engine.start_webcam_session(task_id, subject)
        return True
    except Exception as e:
        print(f"Error starting webcam: {e}")
        return False

@eel.expose
def stop_webcam_session() -> Dict[str, Any]:
    return engine.stop_webcam_session()

@eel.expose
def get_webcam_status() -> str:
    return engine.get_webcam_status()

@eel.expose
def get_ml_insights() -> Dict[str, Any]:
    try:
        from .focus_ml.ml_model import auto_retrain, get_smart_insights, get_subject_recommendations, load_data, engineer_features, train_model
        import os
        import pandas as pd
        
        csv_file = "data/focus_sessions.csv"
        if not os.path.exists(csv_file):
            return {"error": "Not enough data"}
            
        df = pd.read_csv(csv_file)
        if len(df) == 0:
            return {"error": "Not enough data"}
            
        insights = get_smart_insights(df)
        
        # Try to auto-retrain or just get recommendations using an existing model
        result = auto_retrain() 
        if result and "recs" in result:
            recs = result["recs"]
        else:
            # Train on the fly for recs if auto-retrain didn't run (e.g., due to < 20 sessions)
            df_feat = engineer_features(df)
            model, _, _, _ = train_model(df_feat)
            recs = get_subject_recommendations(model, df_feat)
            
        return {
            "insights": insights,
            "recommendations": recs
        }
    except Exception as e:
        print(f"Error getting ML insights: {e}")
        return {"error": str(e)}
