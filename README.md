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

# 🖥️ Application Interface

---

## ⚙️ System Controls Panel

The sidebar allows users to:

- Select input mode (Simulation / Webcam)
- Adjust YOLO confidence threshold
- Adjust IoU threshold
- Upload lane videos
- Generate demo videos
- Start / Stop system

### 📸 System Controls UI
![System Controls](assets/system-controls.png)

---

## 🎬 Video Upload / Demo Tray

Users can upload lane videos or generate dummy simulation videos.

### 📸 Video Source Tray
![Video Tray](assets/video-tray.png)

---

## ▶️ Start & Stop Controls

The system can be started or stopped dynamically.

### 📸 Start & Stop Buttons
![Start Stop](assets/start-stop.png)

---

# 🚘 Vehicle Tracking (Computer Vision Module)

Each lane frame is processed using **YOLOv8**.

### ✔ Detected Vehicle Classes:
- Car
- Bus
- Truck
- Motorcycle
- Bicycle

Bounding boxes are drawn live on video streams.

### 📸 Vehicle Detection in Action
![Vehicle Tracking](assets/vehicle-tracking.png)

---

# 📊 Traffic Analysis Dashboard

The system calculates for each lane:

- Vehicle count
- Waiting time
- Priority score
- Signal status (RED / GREEN)

Priority formula:

```python
priority_score = (vehicle_count * 0.6) + (waiting_time * 0.4)
