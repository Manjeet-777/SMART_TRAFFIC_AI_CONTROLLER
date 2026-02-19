from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable

import cv2
import numpy as np

from .config import FRAME_HEIGHT, FRAME_WIDTH, LOG_FILE, LOGS_DIR, MODELS_DIR, VIDEOS_DIR


def ensure_project_directories() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if not LOG_FILE.exists():
        LOG_FILE.touch()


def save_uploaded_video(uploaded_file, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(uploaded_file.getbuffer())


def open_video_captures(video_paths: Dict[int, Path]) -> Dict[int, cv2.VideoCapture]:
    captures: Dict[int, cv2.VideoCapture] = {}
    for lane_id, video_path in video_paths.items():
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open video for lane {lane_id}: {video_path}")
        captures[lane_id] = capture
    return captures


def read_simulation_frames(
    captures: Dict[int, cv2.VideoCapture],
    frame_size: tuple[int, int] = (FRAME_WIDTH, FRAME_HEIGHT),
) -> Dict[int, np.ndarray]:
    lane_frames: Dict[int, np.ndarray] = {}
    for lane_id, capture in captures.items():
        success, frame = capture.read()
        if not success:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = capture.read()

        if not success:
            frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
            cv2.putText(
                frame,
                f"Lane {lane_id} feed unavailable",
                (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )
        else:
            frame = cv2.resize(frame, frame_size)

        lane_frames[lane_id] = frame
    return lane_frames


def split_webcam_into_lanes(
    frame: np.ndarray,
    lane_ids: Iterable[int],
    frame_size: tuple[int, int] = (FRAME_WIDTH, FRAME_HEIGHT),
) -> Dict[int, np.ndarray]:
    height, width = frame.shape[:2]
    half_h, half_w = height // 2, width // 2

    quadrants = [
        frame[0:half_h, 0:half_w],
        frame[0:half_h, half_w:width],
        frame[half_h:height, 0:half_w],
        frame[half_h:height, half_w:width],
    ]

    lane_frames: Dict[int, np.ndarray] = {}
    for lane_id, region in zip(lane_ids, quadrants):
        lane_frames[lane_id] = cv2.resize(region, frame_size)
    return lane_frames


def build_junction_canvas(
    lane_frames: Dict[int, np.ndarray],
    lane_counts: Dict[int, int],
    signal_state: dict,
    lane_names: Dict[int, str],
) -> np.ndarray:
    current_green_lane = signal_state["current_green_lane"]
    waiting_times = signal_state["waiting_times"]
    priority_scores = signal_state["priority_scores"]

    annotated_frames = []
    for lane_id in sorted(lane_frames.keys()):
        frame = lane_frames[lane_id].copy()
        frame_h, frame_w = frame.shape[:2]

        border_color = (70, 200, 70) if lane_id == current_green_lane else (70, 70, 220)
        cv2.rectangle(frame, (0, 0), (frame_w - 1, frame_h - 1), border_color, 5)

        overlay_lines = [
            f"Lane {lane_id} ({lane_names[lane_id]})",
            f"Count: {lane_counts[lane_id]}",
            f"Waiting: {waiting_times[lane_id]:.1f}s",
            f"Priority: {priority_scores[lane_id]:.2f}",
        ]

        for idx, text in enumerate(overlay_lines):
            cv2.putText(
                frame,
                text,
                (14, 30 + idx * 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        if lane_id == current_green_lane:
            cv2.putText(
                frame,
                f"GREEN: {signal_state['countdown']}s",
                (14, frame_h - 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (60, 220, 60),
                2,
                cv2.LINE_AA,
            )
        else:
            cv2.putText(
                frame,
                "RED",
                (14, frame_h - 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (80, 80, 255),
                2,
                cv2.LINE_AA,
            )

        annotated_frames.append(frame)

    top_row = np.hstack(annotated_frames[0:2])
    bottom_row = np.hstack(annotated_frames[2:4])
    grid = np.vstack([top_row, bottom_row])

    cv2.rectangle(grid, (0, 0), (grid.shape[1] - 1, 56), (15, 25, 35), -1)
    cv2.putText(
        grid,
        f"Smart Traffic AI | Current Green Lane: {current_green_lane} | Countdown: {signal_state['countdown']}s",
        (15, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return grid


def append_traffic_log(
    log_file: Path,
    timestamp: str,
    lane_counts: Dict[int, int],
    signal_state: dict,
) -> None:
    fieldnames = [
        "timestamp",
        "current_green_lane",
        "countdown",
        "cycle_elapsed",
        "lane1_count",
        "lane2_count",
        "lane3_count",
        "lane4_count",
        "lane1_waiting",
        "lane2_waiting",
        "lane3_waiting",
        "lane4_waiting",
        "lane1_priority",
        "lane2_priority",
        "lane3_priority",
        "lane4_priority",
    ]

    row = {
        "timestamp": timestamp,
        "current_green_lane": signal_state["current_green_lane"],
        "countdown": signal_state["countdown"],
        "cycle_elapsed": signal_state["cycle_elapsed"],
        "lane1_count": lane_counts[1],
        "lane2_count": lane_counts[2],
        "lane3_count": lane_counts[3],
        "lane4_count": lane_counts[4],
        "lane1_waiting": signal_state["waiting_times"][1],
        "lane2_waiting": signal_state["waiting_times"][2],
        "lane3_waiting": signal_state["waiting_times"][3],
        "lane4_waiting": signal_state["waiting_times"][4],
        "lane1_priority": signal_state["priority_scores"][1],
        "lane2_priority": signal_state["priority_scores"][2],
        "lane3_priority": signal_state["priority_scores"][3],
        "lane4_priority": signal_state["priority_scores"][4],
    }

    write_header = (not log_file.exists()) or log_file.stat().st_size == 0
    with log_file.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def release_captures(captures: Dict[int, cv2.VideoCapture]) -> None:
    for capture in captures.values():
        if capture is not None:
            capture.release()


def generate_dummy_traffic_videos(
    video_dir: Path,
    lane_ids: Iterable[int],
    duration_seconds: int = 25,
    fps: int = 20,
    frame_size: tuple[int, int] = (FRAME_WIDTH, FRAME_HEIGHT),
) -> None:
    video_dir.mkdir(parents=True, exist_ok=True)
    width, height = frame_size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    total_frames = duration_seconds * fps

    lane_density = {
        1: {"vehicles": 10, "speed": 2.3},
        2: {"vehicles": 14, "speed": 2.8},
        3: {"vehicles": 20, "speed": 3.2},
        4: {"vehicles": 30, "speed": 3.8},
    }

    for lane_id in lane_ids:
        output_path = video_dir / f"lane{lane_id}.mp4"
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, frame_size)
        if not writer.isOpened():
            raise RuntimeError(f"Could not create video file: {output_path}")

        spec = lane_density.get(lane_id, {"vehicles": 12, "speed": 2.5})
        vehicle_count = spec["vehicles"]
        speed = spec["speed"]
        lane_x_positions = [int(width * 0.30), int(width * 0.47), int(width * 0.64)]

        for frame_idx in range(total_frames):
            frame = np.full((height, width, 3), (40, 40, 40), dtype=np.uint8)
            cv2.rectangle(frame, (0, 0), (width - 1, height - 1), (80, 80, 80), 4)

            for divider_x in [int(width * 0.40), int(width * 0.56)]:
                cv2.line(frame, (divider_x, 0), (divider_x, height), (180, 180, 180), 2)

            for vehicle_idx in range(vehicle_count):
                lane_channel = vehicle_idx % 3
                x = lane_x_positions[lane_channel] + (vehicle_idx % 2) * 8 - 4
                y_offset = (frame_idx * speed + vehicle_idx * 48) % (height + 120)
                y = int(height - y_offset)

                if -60 <= y <= height + 20:
                    vehicle_color = (
                        int(60 + (vehicle_idx * 23) % 170),
                        int(90 + (vehicle_idx * 17) % 150),
                        int(120 + (vehicle_idx * 11) % 120),
                    )
                    cv2.rectangle(frame, (x, y), (x + 34, y + 58), vehicle_color, -1)
                    cv2.rectangle(frame, (x, y), (x + 34, y + 58), (25, 25, 25), 2)

            cv2.putText(
                frame,
                f"Dummy Traffic Lane {lane_id}",
                (14, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (240, 240, 240),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Density profile: {vehicle_count} vehicles",
                (14, 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (225, 225, 225),
                2,
                cv2.LINE_AA,
            )
            writer.write(frame)

        writer.release()
