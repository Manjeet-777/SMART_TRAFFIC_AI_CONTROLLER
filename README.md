# Smart Traffic AI

Smart Traffic AI is a Streamlit application that uses YOLOv8, OpenCV, and an adaptive signal controller to simulate lane-aware traffic management for a four-way junction.

## What The Project Does

- Detects vehicles in each lane using YOLOv8.
- Counts vehicles per lane with smoothing to reduce frame jitter.
- Computes a priority score for each lane using vehicle count and waiting time.
- Allocates green-signal time dynamically with fairness constraints.
- Shows a live dashboard with lane feeds, traffic light status, analytics, and CSV logging.

## Tech Stack

- Python
- Streamlit
- Ultralytics YOLOv8
- OpenCV
- Pandas
- Matplotlib

## Project Structure

```text
smart_traffic_ai/
├── app.py
├── assets/
│   └── demo/
│       ├── lane1.mp4
│       ├── lane2.mp4
│       ├── lane3.mp4
│       └── lane4.mp4
├── Dockerfile
├── LICENSE
├── README.md
├── requirements.txt
├── .dockerignore
├── logs/
│   └── .gitkeep
├── models/
│   └── yolov8n.pt
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── detector.py
│   ├── lane_counter.py
│   ├── signal_controller.py
│   └── utils.py
└── videos/
    └── README.md
```

Notes:

- `models/yolov8n.pt` is the primary model path used by the app.
- `assets/demo/lane*.mp4` are the built-in traffic demo clips used by default in Simulation mode.
- `videos/uploaded_lane*` are created only when a user uploads replacement footage.
- `logs/traffic_log.csv` is created automatically at runtime and is not stored in Git.

## Local Run

1. Open a terminal in the project directory.
2. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Start the app:

```bash
streamlit run app.py
```

5. Open the Streamlit URL shown in the terminal, usually:

```text
http://127.0.0.1:8501
```

## How To Use

### Simulation Mode

Use this mode for local demos, GitHub deployments, Docker deployments, and hosted environments.

1. Start the app.
2. Keep `Input Mode` set to `Simulation`. The built-in four-lane demo clips load automatically.
3. Optionally upload one video per lane.
4. If you want a fallback set instead, click `Generate Synthetic Backup Videos`.
5. Click `Start System`.

### Webcam Mode

Use this only when the Streamlit server is running on your local machine and has access to a physical webcam. Hosted deployments should use Simulation mode instead.

## Adaptive Signal Logic

- Priority score:

```text
priority_score = (vehicle_count * 0.6) + (waiting_time * 0.4)
```

- Green time allocation:
  - `0-10` vehicles -> `15 sec`
  - `11-25` vehicles -> `25 sec`
  - `26-50` vehicles -> `40 sec`
  - `51+` vehicles -> `60 sec`

- Fairness constraints:
  - `MIN_GREEN_TIME = 15 sec`
  - `MAX_GREEN_TIME = 60 sec`
  - `TOTAL_CYCLE_TIME = 120 sec`

## Docker Deployment

This repository now includes a Dockerfile, so you can deploy it on any platform that supports Docker.

### Build Locally

```bash
docker build -t smart-traffic-ai .
```

### Run Locally With Docker

```bash
docker run --rm -p 8501:8501 smart-traffic-ai
```

Then open:

```text
http://127.0.0.1:8501
```

### Deploy To A Host

1. Push this repository to GitHub.
2. Create a new service on your deployment platform.
3. Choose the repository.
4. Use the included `Dockerfile` as the build source.
5. Expose port `8501` or map the platform `PORT` environment variable.

## GitHub Push Steps

If your repository is already connected to GitHub:

```bash
git add .
git commit -m "Prepare Smart Traffic AI for deployment"
git push origin main
```

If your default branch is not `main`, replace it with your branch name.

## Important Repo Notes

- Do not commit `.venv`, `__pycache__`, generated logs, or uploaded videos.
- The repository is set up to ignore generated upload videos and runtime CSV logs.
- Keep `models/yolov8n.pt` in the repo so deployments can start without downloading the model at runtime.

## Troubleshooting

- `Unable to open webcam index 0`
  - Use `Simulation` mode unless the app is running locally on a machine with a webcam.
- YOLO model not found
  - Confirm that `models/yolov8n.pt` exists.
- No lane videos available
  - Click `Generate Dummy Videos` in the sidebar.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
