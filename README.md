# Smart Traffic AI

AI-powered adaptive traffic signal control using YOLOv8, OpenCV, and Streamlit.

## Features
- Real-time vehicle detection using **YOLOv8 (Ultralytics)**.
- Detects: **car, bike (motorcycle/bicycle), bus, truck**.
- Input sources:
  - 4-lane simulation videos (recommended demo mode)
  - webcam (auto-split into 4 virtual lanes)
- Lane-wise counting with bounding box overlays.
- Adaptive traffic timing with:
  - `priority_score = (vehicle_count * 0.6) + (waiting_time * 0.4)`
  - Fair scheduling (no starvation)
- Fairness constraints:
  - `MIN_GREEN_TIME = 15 sec`
  - `MAX_GREEN_TIME = 60 sec`
  - `TOTAL_CYCLE_TIME = 120 sec`
- Green-time density mapping:
  - 0–10 vehicles → 15 sec
  - 11–25 vehicles → 25 sec
  - 26–50 vehicles → 40 sec
  - 50+ vehicles → 60 sec
- Dashboard includes:
  - live lane counts
  - current green lane
  - countdown timer
  - waiting times
  - priority scores
  - vehicle-count trend graph
- CSV logging to `logs/traffic_log.csv`.
- Dummy traffic video generation for demo mode.

## Folder Structure
```text
smart_traffic_ai/
├── app.py
├── requirements.txt
├── README.md
├── models/
│   └── yolov8n.pt
├── videos/
│   ├── lane1.mp4
│   ├── lane2.mp4
│   ├── lane3.mp4
│   └── lane4.mp4
├── src/
│   ├── __init__.py
│   ├── detector.py
│   ├── lane_counter.py
│   ├── signal_controller.py
│   ├── utils.py
│   └── config.py
└── logs/
    └── traffic_log.csv
```

Notes:
- `models/yolov8n.pt`: auto-copied locally on first run if not already present.
- `videos/lane*.mp4`: auto-generated from the sidebar button or first simulation start if missing/invalid.

## Tech Stack

### Languages
- Python (application logic, UI, CV, scheduling)
- Markdown (documentation)
- CSV (runtime logs)

### Frontend
- Streamlit UI (`app.py`)
- Embedded HTML/CSS (custom traffic light cards/theme via `st.markdown` in `app.py`)

### Backend
- Streamlit app server (single Python process; no separate REST backend)
- Core backend modules:
  - Detection: `src/detector.py`
  - Lane counting: `src/lane_counter.py`
  - Signal control logic: `src/signal_controller.py`
  - Utilities/logging/video I/O: `src/utils.py`

### ML / Computer Vision
- Ultralytics YOLOv8 (`src/detector.py`)
- OpenCV (`app.py`, `src/detector.py`, `src/utils.py`)

### Data / Analytics
- Pandas (`app.py`) for dashboard tables and trend data handling
- Matplotlib (`app.py`) for vehicle-count-over-time graph
- CSV file logging (`logs/traffic_log.csv` via `src/utils.py`)

### Database and ORM
- Database: None
- ORM: None
- Persistence is file-based (CSV logs)

### Tooling
- Package manager: `pip`
- Environment management: `venv`
- Dependency spec: `requirements.txt`
- Build tool: None
- Test framework: None configured in this repository

## Setup & Run
1. Open terminal in `/Users/manjeetkumar/Documents/New project/smart_traffic_ai`.
2. Create and activate virtual environment (recommended):
   - macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   streamlit run app.py
   ```
5. Open in browser:
   - `http://127.0.0.1:8501`
6. Demo flow:
   - Select **Simulation** mode
   - Click **Generate Dummy Videos** (if needed)
   - Click **Start System**

## Demo Instructions
1. Start app with `streamlit run app.py`.
2. In sidebar, keep **Input Mode = Simulation**.
3. Click **Generate Dummy Videos** (if lane videos do not exist).
4. Click **Start System**.
5. Observe:
   - YOLO bounding boxes on each lane feed.
   - Live counts and priority scores.
   - Dynamic lane switching and countdown.
   - Graph updates over time.
6. Optional:
   - Upload your own video per lane.
   - Switch to webcam mode.

## Explanation of Algorithm

### 1) How YOLO detects vehicles
- Each lane frame is passed to YOLOv8 inference.
- YOLO predicts bounding boxes and classes.
- Predictions are filtered to vehicle classes:
  `car`, `motorcycle`, `bicycle`, `bus`, `truck`.
- Motorcycle and bicycle are shown as **bike**.

### 2) How lane counting works
- Vehicle count per lane is the number of filtered YOLO boxes in that frame.
- A short smoothing window is applied to reduce frame-to-frame jitter.
- Count is overlaid directly on lane frame and dashboard.

### 3) How priority score is calculated
- For each lane:
  - `priority_score = (vehicle_count * 0.6) + (waiting_time * 0.4)`
- Vehicle count captures density pressure.
- Waiting time ensures lanes not served recently become more urgent.

### 4) How fairness is ensured
- The controller maintains a per-cycle pending lane set.
- In each 120-second cycle, each lane is selected at least once.
- Once all lanes are served, a new cycle starts.
- This guarantees **no starvation**.

### 5) Why min/max green time is necessary
- `MIN_GREEN_TIME` prevents too-frequent switching and gives vehicles enough time to clear.
- `MAX_GREEN_TIME` prevents one lane from monopolizing the signal.
- Combined with `TOTAL_CYCLE_TIME`, all lanes remain serviceable.

### 6) How waiting time prevents starvation
- Waiting time grows for red lanes every second.
- Even with lower vehicle count, a lane’s priority rises as it waits longer.
- Over time, delayed lanes become competitive and must be selected.

## Screenshots (What You Should See)
Add screenshots in this section after running locally.

### Screenshot 1: Main Dashboard
- 2x2 lane video grid.
- Bounding boxes around vehicles.
- Green border on active lane, red border on others.

### Screenshot 2: Signal Panel
- Four light cards (one green, three red).
- Countdown shown for current green lane.
- Waiting timers for red lanes.

### Screenshot 3: Analytics
- Lane analytics table with count, waiting time, and priority score.
- Line chart showing vehicle count trend per lane over time.

## Optional Enhancements You Can Add
- Emergency vehicle class override for immediate priority.
- Pedestrian crossing phase integration.
- Accident/stopped-vehicle detection with alert banner.
