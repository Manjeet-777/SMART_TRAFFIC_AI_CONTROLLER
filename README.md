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
