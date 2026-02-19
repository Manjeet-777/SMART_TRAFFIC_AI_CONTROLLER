<<<<<<< HEAD
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
=======
# SMART_TRAFFIC_AI_CONTROLLER
AI-powered adaptive traffic signal control system using YOLOv8, OpenCV, and Streamlit. Real-time vehicle detection with dynamic green signal allocation and fairness-based priority scheduling.

# 🚦 Smart Traffic AI — Adaptive Traffic Signal Control System

An AI-powered intelligent traffic signal management system that uses **YOLOv8 (Ultralytics) + OpenCV + Streamlit** to dynamically allocate green signal time based on real-time vehicle detection and lane priority scoring.

> 💡 Designed for Smart Cities, AI/ML Projects, and Computer Vision Applications.

---

## 🌟 Project Overview

Traditional traffic signals operate on fixed timers, causing:

- ❌ Unnecessary waiting
- ❌ Traffic congestion in high-density lanes
- ❌ Inefficient signal switching
- ❌ No fairness mechanism

This project solves these problems using:

✅ Real-time vehicle detection  
✅ Density-based adaptive signal timing  
✅ Waiting-time based fairness scheduling  
✅ Live dashboard with analytics  
✅ Simulation + Webcam mode  

---

# 🖥️ Ap<img width="1280" height="832" alt="dashboard" src="https://github.com/user-attachments/assets/79e6e6c6-fa35-4604-b3ce-0bdc518833ea" />
plication Interface

---

## ⚙️ System Controls Panel<img width="296" height="326" alt="System controls" src="https://github.com/user-attachments/assets/9f0dedbf-c2f1-4cad-9a21-03a73c2c5c1b" />

<img width="1280" height="832" alt="real time lane density analysis " src="https://github.com/user-attachments/assets/772e4909-563a-4419-8006-0e9bee814447" />

The sidebar allows users to:

- Select input mode (Simulation / Webcam)
- Adjust YOLO confidence threshold
- Adjust IoU threshold
- Upload lane videos
- Generate demo videos
- Start / Stop system

### 📸 System Controls UI
![System Controls]<img width="296" height="326" alt="System controls" src="https://github.com/user-attachments/assets/1b776cfb-ada2-486f-b473-7189346245ca" />


---

## 🎬 Video Upload / Demo Tray

Users can upload lane videos or generate dummy simulation videos.

### 📸 Video Source Tray

https://github.com/user-attachments/assets/49ba7594-93ff-405e-ada9-6c35fe39a212


![Video Tray]

---

## ▶️ Start & Stop Controls

The system can be started or stopped dynamically.

### 📸 Start & Stop Buttons
![Start Stop]

---<img width="1280" height="832" alt="start and stop button" src="https://github.com/user-attachments/assets/ba904ac9-840a-49eb-904f-971ce0cc159c" />


# 🚘 Vehicle Tracking (Computer Vision Module)
<img width="1280" height="832" alt="vechicle tracking" src="https://github.com/user-attachments/assets/7c8c9c66-0693-4d41-847a-97854e24a622" />

Each lane frame is processed using **YOLOv8**.

### ✔ Detected Vehicle Classes:
- Car
- Bus
- Truck
- Motorcycle
- Bicycle

Bounding boxes are drawn live on video streams.

### 📸 Vehicle Detection in Action
![Vehicle Tracking]
<img width="1280" height="832" alt="vechicle tracking" src="https://github.com/user-attachments/assets/d51eb672-664e-4d14-8f75-2a9b9d5f2fef" />

---

# 📊 Traffic Analysis Dashboard
<img width="1280" height="832" alt="traffic analysis" src="https://github.com/user-attachments/assets/4eda5c2e-c31a-44bb-8a5b-8ba42c4e1932" />

The system calculates for each lane:

- Vehicle count
- Waiting time
- Priority score
- Signal status (RED / GREEN)

Priority formula:


🚦 Smart AI-Based Traffic Management System

An intelligent traffic control system that uses **YOLOv8 + Computer Vision + Adaptive Signal Logic** to dynamically optimize traffic flow and reduce congestion.

---

## 🎯 Core Objectives

This system ensures:

- 🚛 Heavy lanes get priority
- ⏳ Long-waiting lanes are not ignored
- ⚖️ Balanced and fair signal scheduling
- 📊 Real-time analytics and visualization
- 🚦 Smooth adaptive signal switching

---

# 📈 Real-Time Lane Density Trend

Live vehicle count visualization over time using **Matplotlib**.

### Features:
- Displays dynamic vehicle count per lane
- Shows congestion growth trends
- Assists in adaptive signal decision-making
- Updates automatically during simulation

---

# 📋 Traffic Analytics Table

The system displays real-time lane statistics:

| Lane Name | Vehicle Count | Waiting Time | Priority Score | Current Signal |
|-----------|--------------|-------------|---------------|---------------|
| Lane 1    | 24           | 18 sec      | 0.72          | 🟢 Green      |
| Lane 2    | 8            | 30 sec      | 0.65          | 🔴 Red        |
| Lane 3    | 40           | 12 sec      | 0.81          | 🔴 Red        |
| Lane 4    | 5            | 45 sec      | 0.60          | 🔴 Red        |

### Displays:
- Lane Name
- Vehicle Count
- Waiting Time
- Priority Score
- Current Signal Status

---

# 🟢 Adaptive Signal Logic

Green time allocation based on vehicle density:

| Vehicles | Green Time |
|----------|-----------|
| 0–10     | 15 sec    |
| 11–25    | 25 sec    |
| 26–50    | 40 sec    |
| 50+      | 60 sec    |

### Benefits:
- Automatically adjusts green duration
- Reduces unnecessary waiting
- Optimizes traffic throughput
- Handles varying traffic conditions dynamically

---

# ⚖️ Fairness Constraints

MIN_GREEN_TIME = 15  # seconds
MAX_GREEN_TIME = 60  # seconds
TOTAL_CYCLE_TIME = 120  # seconds

## Web-page url;

--http://localhost:8501/

# 🚀 Setup & Run

## 1️⃣ Clone Repository

git clone <your-repo-link>
cd smart_traffic_ai

2️⃣ Create Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Run Application
streamlit run app.py

Open in browser:(chrome suggested)
http://localhost:8501/

🎥 Demo Flow
Select Simulation Mode
Generate Dummy Traffic Videos
Click Start System
System Performs:
🚗 Vehicle detection using YOLOv8
🚦 Adaptive green time allocation
📊 Live analytics updating
📈 Real-time density visualization
📁 CSV logging of traffic data
🌍 Real-World Applications
Smart city infrastructure
Traffic congestion optimization
AI-based surveillance systems
Urban mobility research
Transportation analytics platforms
Intelligent traffic automation
🔮 Future Improvements
🚑 Emergency vehicle detection override
🚶 Pedestrian crossing integration
☁️ Cloud deployment
📡 IoT sensor integration
🧠 Reinforcement learning-based optimization
📱 Mobile monitoring dashboard
>>>>>>> ca176e843187502b22bf48a8cfbc8bbf7a576b58
