from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import cv2
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.config import (
    CONFIDENCE_THRESHOLD,
    DISPLAY_FPS,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    IOU_THRESHOLD,
    LANE_IDS,
    LANE_NAMES,
    LOG_FILE,
    MODEL_PATH,
    VIDEOS_DIR,
)
from src.detector import VehicleDetector
from src.lane_counter import LaneCounter
from src.signal_controller import AdaptiveSignalController
from src.utils import (
    append_traffic_log,
    build_junction_canvas,
    ensure_project_directories,
    generate_dummy_traffic_videos,
    open_video_captures,
    read_simulation_frames,
    release_captures,
    save_uploaded_video,
    split_webcam_into_lanes,
)

DEFAULT_VIDEO_PATHS = {lane_id: VIDEOS_DIR / f"lane{lane_id}.mp4" for lane_id in LANE_IDS}
FRAME_SIZE = (FRAME_WIDTH, FRAME_HEIGHT)


def init_session_state() -> None:
    defaults = {
        "running": False,
        "needs_reinit": False,
        "config_signature": None,
        "detector": None,
        "lane_counter": None,
        "controller": None,
        "captures": {},
        "webcam_capture": None,
        "history": [],
        "last_tick": None,
        "last_log_time": 0.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def release_runtime_resources() -> None:
    release_captures(st.session_state.get("captures", {}))
    st.session_state.captures = {}

    webcam_capture = st.session_state.get("webcam_capture")
    if webcam_capture is not None:
        webcam_capture.release()
    st.session_state.webcam_capture = None


def prepare_simulation_sources(uploaded_files: Dict[int, object]) -> Dict[int, Path]:
    sources: Dict[int, Path] = {}
    for lane_id in LANE_IDS:
        uploaded_file = uploaded_files.get(lane_id)
        if uploaded_file is None:
            sources[lane_id] = DEFAULT_VIDEO_PATHS[lane_id]
            continue

        destination = VIDEOS_DIR / f"uploaded_lane{lane_id}.mp4"
        save_uploaded_video(uploaded_file, destination)
        sources[lane_id] = destination
    return sources


def initialize_runtime(
    mode: str,
    confidence_threshold: float,
    iou_threshold: float,
    uploaded_files: Dict[int, object],
    webcam_index: int,
) -> None:
    release_runtime_resources()
    ensure_project_directories()

    st.session_state.detector = VehicleDetector(
        model_path=MODEL_PATH,
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
    )
    st.session_state.lane_counter = LaneCounter(lane_ids=LANE_IDS, smoothing_window=4)
    st.session_state.controller = AdaptiveSignalController(lane_ids=LANE_IDS)
    st.session_state.controller.bootstrap({lane_id: 0 for lane_id in LANE_IDS})
    st.session_state.history = []
    st.session_state.last_tick = time.time()
    st.session_state.last_log_time = 0.0

    if mode == "Simulation":
        sources = prepare_simulation_sources(uploaded_files)
        try:
            st.session_state.captures = open_video_captures(sources)
        except RuntimeError as error:
            using_default_sources = all(uploaded_files.get(lane_id) is None for lane_id in LANE_IDS)
            if not using_default_sources:
                raise RuntimeError(
                    f"Could not read one or more uploaded lane videos: {error}"
                ) from error

            generate_dummy_traffic_videos(video_dir=VIDEOS_DIR, lane_ids=LANE_IDS)
            fallback_sources = {
                lane_id: DEFAULT_VIDEO_PATHS[lane_id] for lane_id in LANE_IDS
            }
            st.session_state.captures = open_video_captures(fallback_sources)
    else:
        webcam_capture = cv2.VideoCapture(webcam_index)
        if not webcam_capture.isOpened():
            raise RuntimeError(f"Unable to open webcam index {webcam_index}.")
        st.session_state.webcam_capture = webcam_capture


def read_input_frames(mode: str) -> Dict[int, object]:
    if mode == "Simulation":
        captures = st.session_state.get("captures", {})
        return read_simulation_frames(captures, frame_size=FRAME_SIZE)

    webcam_capture = st.session_state.get("webcam_capture")
    if webcam_capture is None:
        raise RuntimeError("Webcam capture is not initialized.")

    success, frame = webcam_capture.read()
    if not success:
        raise RuntimeError("Could not read frame from webcam.")
    return split_webcam_into_lanes(frame, lane_ids=LANE_IDS, frame_size=FRAME_SIZE)


def build_traffic_light_html(signal_state: dict) -> str:
    current_green_lane = signal_state["current_green_lane"]
    countdown = signal_state["countdown"]
    waiting_times = signal_state["waiting_times"]

    cards = []
    for lane_id in LANE_IDS:
        is_green = lane_id == current_green_lane
        color = "#2FBF71" if is_green else "#E74C3C"
        status = "GREEN" if is_green else "RED"
        timer_text = f"{countdown}s remaining" if is_green else f"{waiting_times[lane_id]:.1f}s wait"

        cards.append(
            f"""
            <div class="signal-card">
                <div class="signal-light" style="background:{color};"></div>
                <div class="signal-title">Lane {lane_id} ({LANE_NAMES[lane_id]})</div>
                <div class="signal-status">{status}</div>
                <div class="signal-timer">{timer_text}</div>
            </div>
            """
        )

    return f'<div class="signal-grid">{"".join(cards)}</div>'


def render_dashboard(canvas: object, lane_counts: Dict[int, int], signal_state: dict) -> None:
    st.image(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)

    metrics_row = st.columns(4)
    metrics_row[0].metric("Current Green Lane", f"Lane {signal_state['current_green_lane']}")
    metrics_row[1].metric("Countdown", f"{signal_state['countdown']} sec")
    metrics_row[2].metric("Cycle Elapsed", f"{signal_state['cycle_elapsed']} sec")
    metrics_row[3].metric("Total Vehicles", sum(lane_counts.values()))

    lane_metrics = st.columns(4)
    for index, lane_id in enumerate(LANE_IDS):
        lane_metrics[index].metric(f"Lane {lane_id} Count", lane_counts[lane_id])

    st.markdown("### Traffic Light State")
    st.markdown(build_traffic_light_html(signal_state), unsafe_allow_html=True)

    table_rows = []
    for lane_id in LANE_IDS:
        table_rows.append(
            {
                "Lane": f"Lane {lane_id} ({LANE_NAMES[lane_id]})",
                "Vehicle Count": lane_counts[lane_id],
                "Waiting Time (s)": round(signal_state["waiting_times"][lane_id], 2),
                "Priority Score": round(signal_state["priority_scores"][lane_id], 2),
                "Signal": "GREEN" if lane_id == signal_state["current_green_lane"] else "RED",
            }
        )

    st.markdown("### Lane Analytics")
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


def render_history_graph() -> None:
    history = st.session_state.get("history", [])
    st.markdown("### Vehicle Count Over Time")

    if len(history) < 2:
        st.info("Graph will appear after a few frames are processed.")
        return

    data = pd.DataFrame(history)
    figure, axis = plt.subplots(figsize=(12, 4))

    for lane_id in LANE_IDS:
        axis.plot(
            data["step"],
            data[f"lane_{lane_id}"],
            linewidth=2.0,
            label=f"Lane {lane_id}",
        )

    axis.set_xlabel("Time Step")
    axis.set_ylabel("Detected Vehicles")
    axis.set_title("Real-Time Lane Density Trend")
    axis.grid(alpha=0.25)
    axis.legend(ncol=2, loc="upper right")
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)


def process_one_frame(mode: str) -> None:
    frames = read_input_frames(mode)
    detector = st.session_state.detector
    lane_counter = st.session_state.lane_counter
    controller = st.session_state.controller

    detected_frames = {}
    for lane_id in LANE_IDS:
        frame = frames[lane_id]
        detections = detector.detect(frame)
        lane_counter.update(lane_id, len(detections))
        detected_frames[lane_id] = detector.draw_detections(frame.copy(), detections)

    lane_counts = lane_counter.get_counts()

    now = time.time()
    delta_seconds = max(now - st.session_state.last_tick, 1e-3)
    st.session_state.last_tick = now

    controller.update_vehicle_counts(lane_counts)
    controller.tick(delta_seconds)
    signal_state = controller.get_state()

    canvas = build_junction_canvas(
        lane_frames=detected_frames,
        lane_counts=lane_counts,
        signal_state=signal_state,
        lane_names=LANE_NAMES,
    )
    render_dashboard(canvas=canvas, lane_counts=lane_counts, signal_state=signal_state)

    next_step = st.session_state.history[-1]["step"] + 1 if st.session_state.history else 0
    history_entry = {
        "step": next_step,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    for lane_id in LANE_IDS:
        history_entry[f"lane_{lane_id}"] = lane_counts[lane_id]
    st.session_state.history.append(history_entry)
    st.session_state.history = st.session_state.history[-500:]

    if now - st.session_state.last_log_time >= 1.0:
        append_traffic_log(
            log_file=LOG_FILE,
            timestamp=history_entry["timestamp"],
            lane_counts=lane_counts,
            signal_state=signal_state,
        )
        st.session_state.last_log_time = now

    render_history_graph()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(120deg, #f6fbff 0%, #eef3f8 55%, #ffffff 100%);
            }
            .signal-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(180px, 1fr));
                gap: 12px;
                margin-top: 8px;
                margin-bottom: 8px;
            }
            .signal-card {
                border: 1px solid #d4dde8;
                border-radius: 14px;
                background: #ffffff;
                padding: 14px;
                box-shadow: 0 6px 16px rgba(33, 58, 89, 0.08);
                text-align: center;
                animation: fadeIn 0.35s ease-out;
            }
            .signal-light {
                width: 26px;
                height: 26px;
                border-radius: 50%;
                margin: 0 auto 8px auto;
                box-shadow: 0 0 12px rgba(46, 204, 113, 0.35);
            }
            .signal-title {
                color: #183b56;
                font-size: 0.95rem;
                font-weight: 600;
            }
            .signal-status {
                color: #334e68;
                font-size: 0.85rem;
                margin-top: 4px;
                font-weight: 600;
            }
            .signal-timer {
                color: #486581;
                font-size: 0.82rem;
                margin-top: 3px;
            }
            @keyframes fadeIn {
                from { transform: translateY(3px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Smart Traffic AI Controller",
        page_icon="🚦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()
    ensure_project_directories()
    apply_theme()

    st.title("Smart Traffic AI")
    st.caption("YOLOv8-based lane detection, adaptive signal timing, and fairness-aware scheduling.")

    with st.sidebar:
        st.header("System Controls")
        mode = st.radio("Input Mode", ["Simulation", "Webcam"], index=0)
        confidence_threshold = st.slider(
            "YOLO Confidence Threshold",
            min_value=0.1,
            max_value=0.9,
            value=float(CONFIDENCE_THRESHOLD),
            step=0.05,
        )
        iou_threshold = st.slider(
            "YOLO IoU Threshold",
            min_value=0.1,
            max_value=0.9,
            value=float(IOU_THRESHOLD),
            step=0.05,
        )

        uploaded_files: Dict[int, object] = {}
        webcam_index = 0

        if mode == "Simulation":
            st.subheader("Lane Video Sources")
            for lane_id in LANE_IDS:
                uploaded_files[lane_id] = st.file_uploader(
                    f"Lane {lane_id} video",
                    type=["mp4", "avi", "mov"],
                    key=f"lane_{lane_id}_uploader",
                )
            if st.button("Generate Dummy Videos", use_container_width=True):
                generate_dummy_traffic_videos(video_dir=VIDEOS_DIR, lane_ids=LANE_IDS)
                st.success("Dummy lane videos generated in /videos.")
        else:
            webcam_index = int(
                st.number_input("Webcam Index", min_value=0, max_value=10, value=0, step=1)
            )

        start_clicked = st.button("Start System", type="primary", use_container_width=True)
        stop_clicked = st.button("Stop System", use_container_width=True)

        if st.session_state.running:
            st.success("System running")
        else:
            st.warning("System stopped")

    if start_clicked:
        st.session_state.running = True
        st.session_state.needs_reinit = True
    if stop_clicked:
        st.session_state.running = False
        st.session_state.needs_reinit = False
        release_runtime_resources()

    if mode == "Simulation":
        source_signature = tuple(
            uploaded_files[lane_id].name if uploaded_files[lane_id] is not None else str(DEFAULT_VIDEO_PATHS[lane_id])
            for lane_id in LANE_IDS
        )
    else:
        source_signature = (webcam_index,)

    config_signature = (
        mode,
        round(confidence_threshold, 2),
        round(iou_threshold, 2),
        source_signature,
    )

    if st.session_state.running and st.session_state.config_signature != config_signature:
        st.session_state.needs_reinit = True

    if not st.session_state.running:
        st.info("Press **Start System** to begin processing traffic input.")
        if st.session_state.history:
            render_history_graph()
        return

    try:
        if st.session_state.needs_reinit:
            initialize_runtime(
                mode=mode,
                confidence_threshold=confidence_threshold,
                iou_threshold=iou_threshold,
                uploaded_files=uploaded_files,
                webcam_index=webcam_index,
            )
            st.session_state.config_signature = config_signature
            st.session_state.needs_reinit = False

        process_one_frame(mode=mode)
        time.sleep(1.0 / DISPLAY_FPS)
        st.rerun()
    except Exception as error:
        st.session_state.running = False
        st.session_state.needs_reinit = False
        release_runtime_resources()
        st.error(f"Runtime error: {error}")


if __name__ == "__main__":
    main()
