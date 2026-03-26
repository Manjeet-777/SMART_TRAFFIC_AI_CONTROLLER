from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"
VIDEOS_DIR = BASE_DIR / "videos"
DEMO_VIDEOS_DIR = BASE_DIR / "assets" / "demo"
LOGS_DIR = BASE_DIR / "logs"

MODEL_FILENAME = "yolov8n.pt"
MODEL_PATH = MODELS_DIR / MODEL_FILENAME
FALLBACK_MODEL_PATHS = (
    MODEL_PATH,
    BASE_DIR / MODEL_FILENAME,
)
LOG_FILE = LOGS_DIR / "traffic_log.csv"

LANE_IDS = [1, 2, 3, 4]
LANE_NAMES = {
    1: "North",
    2: "East",
    3: "South",
    4: "West",
}

DETECTION_CLASSES = {"car", "motorcycle", "bus", "truck", "bicycle"}
CONFIDENCE_THRESHOLD = 0.30
IOU_THRESHOLD = 0.50

VEHICLE_WEIGHT = 0.78
WAITING_WEIGHT = 0.22

MIN_GREEN_TIME = 15
MAX_GREEN_TIME = 60
TOTAL_CYCLE_TIME = 120

FRAME_WIDTH = 640
FRAME_HEIGHT = 360
DISPLAY_FPS = 8
