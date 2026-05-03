"""
Phase 3: ML Model & Recommendation Engine
Smart Study Planner
--------------------------------------------------------------
HOW TO RUN:
  python ml_model.py

FEATURES:
  - Trains Random Forest Regressor on session CSV data
  - Saves model to models/model.pkl
  - Generates smart personalized recommendations
  - Auto-retrain function called from GUI after each session
"""

import pandas as pd
import numpy as np
import os
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
CSV_FILE   = "data/sessions.csv"
MODEL_DIR  = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "model.pkl")

SUBJECT_DIFFICULTY = {
    "DSA": 5, "OOP": 4, "EEE": 4,
    "MFC": 3, "UID": 3,
    "EOC": 2, 
}
SUBJECTS   = list(SUBJECT_DIFFICULTY.keys())
TIME_SLOTS = [8, 9, 10, 11, 14, 15, 16, 19, 20, 21]


def format_hour(h):
    if h == 12:  return "12:00 PM"
    elif h > 12: return f"{h-12:02d}:00 PM"
    else:        return f"{h:02d}:00 AM"


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
def load_data():
    df = pd.read_csv(CSV_FILE)
    return df


# ─────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────
def engineer_features(df):
    df = df.copy()
    df["Start_Time"] = pd.to_datetime(df["Start_Time"])
    hour = df["Start_Time"].dt.hour
    df["hour_sin"]             = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"]             = np.cos(2 * np.pi * hour / 24)
    df["subject_difficulty"]   = df["Subject"].map(SUBJECT_DIFFICULTY).fillna(3)
    df["drowsy_rate"]          = df["Drowsy_Count"] / (df["Duration_Minutes"] + 0.1)
    df["distracted_rate"]      = df["Distracted_Count"] / (df["Duration_Minutes"] + 0.1)
    df["historical_avg_focus"] = df.groupby("Subject")["Focus_Percentage"].transform("mean")
    return df


# ─────────────────────────────────────────────
# TRAIN MODEL
# ─────────────────────────────────────────────
def train_model(df):
    features = [
        "hour_sin", "hour_cos", "subject_difficulty",
        "Duration_Minutes", "drowsy_rate",
        "distracted_rate", "historical_avg_focus",
    ]
    X = df[features]
    y = df["Quality_Label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae    = mean_absolute_error(y_test, y_pred)
    r2     = r2_score(y_test, y_pred)

    return model, features, mae, r2


# ─────────────────────────────────────────────
# SAVE MODEL
# ─────────────────────────────────────────────
def save_model(model, features):
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_FILE, "wb") as f:
        pickle.dump({"model": model, "features": features}, f)


# ─────────────────────────────────────────────
# SUBJECT RECOMMENDATIONS (best time per subject)
# ─────────────────────────────────────────────
def get_subject_recommendations(model, df):
    used   = {}
    all_s  = {}

    for sub in SUBJECTS:
        af = df[df["Subject"] == sub]["Focus_Percentage"].mean()
        if pd.isna(af):
            af = 70.0
        scores = []
        for h in TIME_SLOTS:
            samp = pd.DataFrame([{
                "hour_sin":             np.sin(2*np.pi*h/24),
                "hour_cos":             np.cos(2*np.pi*h/24),
                "subject_difficulty":   SUBJECT_DIFFICULTY.get(sub, 3),
                "Duration_Minutes":     45,
                "drowsy_rate":          0.05,
                "distracted_rate":      0.05,
                "historical_avg_focus": af,
            }])
            sc = round(min(100, max(0, model.predict(samp)[0])), 1)
            scores.append((sc, h))
        scores.sort(key=lambda x: x[0], reverse=True)
        all_s[sub] = scores

    assigned = {}
    for sub in sorted(SUBJECTS, key=lambda s: all_s[s][0][0], reverse=True):
        for sc, h in all_s[sub]:
            if h not in used:
                used[h] = sub
                assigned[sub] = (sc, h)
                break
        else:
            assigned[sub] = all_s[sub][0]

    results = sorted(
        [(s, format_hour(assigned[s][1]), assigned[s][0]) for s in SUBJECTS],
        key=lambda x: x[2], reverse=True
    )
    return results


# ─────────────────────────────────────────────
# SMART INSIGHTS (3 personalized tips)
# ─────────────────────────────────────────────
def get_smart_insights(df):
    insights = []
    df = df.copy()
    df["Start_Time"] = pd.to_datetime(df["Start_Time"])
    df["hour"]       = df["Start_Time"].dt.hour

    # ── Insight 1: Peak Focus Time ──────────────
    hour_focus = df.groupby("hour")["Focus_Percentage"].mean()
    if not hour_focus.empty:
        best_hour = hour_focus.idxmax()
        best_pct  = round(hour_focus.max(), 1)
        insights.append({
            "icon":  "",
            "title": "Peak Focus Time",
            "text":  f"You focus best around {format_hour(best_hour)} with an average of {best_pct}% focus. Try scheduling your hardest subjects then."
        })

    # ── Insight 2: Optimal Session Length ───────
    focused_sessions = df[df["Focus_Percentage"] >= 70]
    if not focused_sessions.empty:
        avg_dur = round(focused_sessions["Duration_Minutes"].mean(), 1)
        insights.append({
            "icon":  "",
            "title": "Optimal Session Length",
            "text":  f"Your most focused sessions last around {avg_dur} minutes. Consider taking a short break after that to maintain quality."
        })
    else:
        insights.append({
            "icon":  "",
            "title": "Optimal Session Length",
            "text":  "Not enough focused sessions yet. Aim for sessions of 30–45 minutes with short breaks in between."
        })

    # ── Insight 3: Weekly Progress ───────────────
    df["week"] = df["Start_Time"].dt.isocalendar().week
    weeks = sorted(df["week"].unique())
    if len(weeks) >= 2:
        this_week = round(df[df["week"] == weeks[-1]]["Quality_Label"].mean(), 1)
        last_week = round(df[df["week"] == weeks[-2]]["Quality_Label"].mean(), 1)
        diff      = round(this_week - last_week, 1)
        arrow     = "↑" if diff >= 0 else "↓"
        direction = "up" if diff >= 0 else "down"
        insights.append({
            "icon":  "",
            "title": "Weekly Progress",
            "text":  f"Your average quality score this week is {this_week}/100 — {arrow} {abs(diff)} points {direction} from last week."
        })
    else:
        avg_q = round(df["Quality_Label"].mean(), 1)
        insights.append({
            "icon":  "",
            "title": "Overall Performance",
            "text":  f"Your average session quality score so far is {avg_q}/100. Keep logging sessions for weekly progress tracking."
        })

    return insights


# ─────────────────────────────────────────────
# AUTO-RETRAIN (called from GUI)
# ─────────────────────────────────────────────
RETRAIN_EVERY = 5        # retrain after every 5 new sessions
RETRAIN_TRACKER = os.path.join(MODEL_DIR, "last_trained_count.txt")

def _get_last_trained_count():
    """Returns how many sessions the model was last trained on."""
    if os.path.exists(RETRAIN_TRACKER):
        try:
            with open(RETRAIN_TRACKER) as f:
                return int(f.read().strip())
        except Exception:
            return 0
    return 0

def _save_trained_count(count):
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(RETRAIN_TRACKER, "w") as f:
        f.write(str(count))

def auto_retrain():
    """
    Smart auto-retrain — only retrains when RETRAIN_EVERY new sessions
    have been added since the last training.
    Returns result dict if retrained, None if skipped.
    """
    try:
        if not os.path.exists(CSV_FILE):
            return None

        df          = load_data()
        total       = len(df)
        last_count  = _get_last_trained_count()
        new_since   = total - last_count

        # Minimum 5 sessions to train at all
        if total < 5:
            print(f"  ⏭  Skipping retrain — need at least 5 sessions (have {total})")
            return None

        # Only retrain if enough new sessions added
        if new_since < RETRAIN_EVERY and os.path.exists(MODEL_FILE):
            print(f"  ⏭  Skipping retrain — only {new_since} new sessions since last train (need {RETRAIN_EVERY})")
            return None

        print(f"  🔄 Retraining on {total} sessions ({new_since} new since last train)...")
        df_feat              = engineer_features(df)
        model, features, mae, r2 = train_model(df_feat)
        save_model(model, features)
        _save_trained_count(total)

        recs     = get_subject_recommendations(model, df_feat)
        insights = get_smart_insights(df)
        print(f"  ✅ Retrain complete — MAE: {mae:.2f}, R²: {r2:.2f}")
        return {"recs": recs, "insights": insights, "mae": mae, "r2": r2}

    except Exception as e:
        print(f"  ❌ Auto-retrain error: {e}")
        return None


# ─────────────────────────────────────────────
# ENTRY POINT (manual run)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("   SMART STUDY PLANNER — ML MODEL (Phase 3)")
    print("=" * 55)

    df = load_data()
    print(f"    {len(df)} sessions loaded")

    df_feat = engineer_features(df)
    

    print("\n Training model...")
    model, features, mae, r2 = train_model(df_feat)
    print(f"    Mean Absolute Error : {mae:.2f}")
    print(f"    R² Score            : {r2:.2f}")

    save_model(model, features)
    print(f"\n Model saved to {MODEL_FILE}")

    print("\n Subject Recommendations:")
    print("=" * 55)
    recs = get_subject_recommendations(model, df_feat)
    for i, (sub, t, sc) in enumerate(recs):
        medal = ["🥇","🥈","🥉"][i] if i < 3 else "  "
        print(f"  {medal}  {sub:<20} {t:<12}  {sc}/100")
    print("=" * 55)

    print("\n Smart Insights:")
    insights = get_smart_insights(df)
    for ins in insights:
        print(f"\n  {ins['icon']}  {ins['title']}")
        print(f"     {ins['text']}")

    