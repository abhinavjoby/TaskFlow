# TaskFlow

TaskFlow is an intelligent, cross-platform productivity and task management application built with a Python backend and a stunning Glassmorphic web frontend. 

It acts as a comprehensive study and task planner by not only managing your tasks and projects, but also tracking your focus during study sessions using computer vision (MediaPipe) and machine learning (scikit-learn) to provide personalized, data-driven recommendations on when and what to study.

## Features

- **Dashboard & Task Management:** A sleek, glassmorphic UI to manage Tasks, Projects, and Goals.
- **Urgent Task Prioritization:** An intelligent algorithm that prioritizes tasks based on deadlines, difficulty, and your current energy level.
- **Focus Mode (AI-Powered):** 
  - Monitors your Eye Aspect Ratio (EAR) using your webcam and MediaPipe to detect drowsiness and distraction during study sessions.
  - Automatically logs focus quality, duration, and interruptions.
- **Smart ML Recommendations:** 
  - Uses a Random Forest Regressor trained on your past focus sessions.
  - Analyzes the time of day, subject difficulty, and historical focus rates to recommend the *best subject to study right now*.
- **Data Analytics:** Charts mapping your focus over time, completion rates, and subject-wise performance.
- **Local Privacy-First Data:** All tasks and machine learning data are processed and stored locally on your machine in `data/tasks.json` and `data/focus_sessions.csv`.

## Prerequisites

- **Python 3.8+**
- A working webcam (for Focus Mode).
- Google Chrome or any chromium-based browser (Eel uses the Chromium engine to render the frontend).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/taskflow.git
   cd taskflow
   ```

2. **Create a virtual environment:**
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the application, simply run the `main.py` script from the `backend` folder:

```bash
python backend/main.py
```

This will launch the TaskFlow interface in a standalone app window. On your first launch, you'll be greeted by an onboarding screen to set up your username and initial subjects.

## Project Structure

- `backend/`
  - `main.py`: The entry point that initializes the Eel application.
  - `api.py`: Python-to-JavaScript bridge exposing backend functions to the frontend.
  - `engine.py`: Core logic for data persistence, task prioritization, and logging.
  - `models.py`: Data classes defining Tasks, Goals, Projects, etc.
  - `focus_ml/`: Contains the computer vision (`webcam_monitor.py`) and ML (`ml_model.py`) scripts.
- `web/`
  - `index.html`: The main dashboard view.
  - `focus.html`: The active focus mode session view.
  - `stats.html`: The analytics and ML insights view.
  - `css/` & `js/`: Frontend styling and logic.
- `data/`: Local storage for your tasks (`tasks.json`) and focus sessions (`focus_sessions.csv`).
- `models/`: Stores the trained `model.pkl` Random Forest model.

## Troubleshooting

- **App closes immediately:** Ensure that Google Chrome or any other Chromium-based browser is installed on your system.
- **Webcam not working:** Grant the application permission to access your camera when starting a Focus Mode session. Ensure no other applications are currently using the webcam.

## License

MIT License
