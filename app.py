from __future__ import annotations

import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Dict

import cv2

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "smart_traffic_ai_matplotlib"),
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.config import (
    CONFIDENCE_THRESHOLD,
    DEMO_VIDEOS_DIR,
    DISPLAY_FPS,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    IOU_THRESHOLD,
    LANE_IDS,
    LANE_NAMES,
    LOG_FILE,
    VEHICLE_WEIGHT,
    WAITING_WEIGHT,
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

DEFAULT_VIDEO_PATHS = {lane_id: DEMO_VIDEOS_DIR / f"lane{lane_id}.mp4" for lane_id in LANE_IDS}
DEFAULT_VIDEO_LABELS = {
    1: "City junction overview",
    2: "Bangkok downtown flow",
    3: "Highway traffic stream",
    4: "Dense urban multilane feed",
}
PREVIEW_LANE_COUNTS = {
    1: 14,
    2: 16,
    3: 21,
    4: 27,
}
PREVIEW_WAIT_TIMES = {
    1: 18.0,
    2: 10.0,
    3: 24.0,
    4: 0.0,
}
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

        suffix = Path(uploaded_file.name).suffix.lower() or ".mp4"
        destination = VIDEOS_DIR / f"uploaded_lane{lane_id}{suffix}"
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

            generate_dummy_traffic_videos(video_dir=DEMO_VIDEOS_DIR, lane_ids=LANE_IDS)
            fallback_sources = {
                lane_id: DEFAULT_VIDEO_PATHS[lane_id] for lane_id in LANE_IDS
            }
            st.session_state.captures = open_video_captures(fallback_sources)
    else:
        webcam_capture = cv2.VideoCapture(webcam_index)
        if not webcam_capture.isOpened():
            raise RuntimeError(
                "Unable to open webcam index "
                f"{webcam_index}. Webcam mode only works when the app server "
                "has access to a physical camera."
            )
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
        status = "GREEN" if is_green else "RED"
        timer_text = f"{countdown}s remaining" if is_green else f"{waiting_times[lane_id]:.1f}s wait"
        state_class = "signal-card active" if is_green else "signal-card inactive"

        cards.append(
            (
                f'<div class="{state_class}">'
                f'<div class="signal-light"></div>'
                f'<div class="signal-title">Lane {lane_id} ({LANE_NAMES[lane_id]})</div>'
                f'<div class="signal-status">{status}</div>'
                f'<div class="signal-timer">{timer_text}</div>'
                "</div>"
            )
        )

    return f'<div class="signal-grid">{"".join(cards)}</div>'


def build_default_preview_canvas() -> object:
    ensure_project_directories()
    if not all(DEFAULT_VIDEO_PATHS[lane_id].exists() for lane_id in LANE_IDS):
        generate_dummy_traffic_videos(video_dir=DEMO_VIDEOS_DIR, lane_ids=LANE_IDS)

    captures = open_video_captures(DEFAULT_VIDEO_PATHS)
    try:
        frames = read_simulation_frames(captures, frame_size=FRAME_SIZE)
    finally:
        release_captures(captures)

    current_green_lane = max(PREVIEW_LANE_COUNTS, key=PREVIEW_LANE_COUNTS.get)
    preview_signal_state = {
        "current_green_lane": current_green_lane,
        "allocated_green_time": 38,
        "countdown": 38,
        "cycle_elapsed": 38,
        "waiting_times": PREVIEW_WAIT_TIMES,
        "priority_scores": {
            lane_id: round(
                PREVIEW_LANE_COUNTS[lane_id] * VEHICLE_WEIGHT
                + PREVIEW_WAIT_TIMES[lane_id] * WAITING_WEIGHT
                + min(PREVIEW_LANE_COUNTS[lane_id], 30) * 0.12,
                2,
            )
            for lane_id in LANE_IDS
        },
    }
    return build_junction_canvas(
        lane_frames=frames,
        lane_counts=PREVIEW_LANE_COUNTS,
        signal_state=preview_signal_state,
        lane_names=LANE_NAMES,
    )


def render_app_header(mode: str) -> None:
    state_text = "Built-in demo traffic clips ready" if mode == "Simulation" else "Local camera mode"
    st.markdown(
        dedent(
            f"""
            <section class="hero-panel">
                <div class="hero-badge">Adaptive Traffic Control</div>
                <h1 class="hero-title">Smart <span>Traffic AI</span></h1>
                <p class="hero-subtitle">
                    Real-time vehicle detection, busier-lane prioritization, and optimized signal timing
                    that keeps traffic moving efficiently without starving lighter lanes.
                </p>
                <div class="hero-meta">
                    <span>{mode} mode</span>
                    <span>{state_text}</span>
                    <span>YOLOv8 + optimized countdown logic</span>
                </div>
            </section>
            """
        ),
        unsafe_allow_html=True,
    )


def render_welcome_state(mode: str) -> None:
    demo_ready = all(DEFAULT_VIDEO_PATHS[lane_id].exists() for lane_id in LANE_IDS)
    status_line = (
        "Built-in traffic demo clips are ready for all four lanes."
        if demo_ready
        else "Built-in demo clips are missing. The app will auto-generate synthetic fallback footage."
    )

    preview_canvas = build_default_preview_canvas()
    st.markdown("### Default Simulation Preview")
    st.image(
        cv2.cvtColor(preview_canvas, cv2.COLOR_BGR2RGB),
        channels="RGB",
        use_container_width=True,
    )

    st.markdown(
        dedent(
            f"""
            <div class="ambient-panel">
                <div class="panel-header-row">
                    <div>
                        <div class="panel-kicker">Quick Start</div>
                        <h3>Launch the controller in one click</h3>
                    </div>
                    <div class="status-pill">{mode}</div>
                </div>
                <p class="panel-copy">{status_line} Press <strong>Start System</strong> to begin the live simulation from these default lanes.</p>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    quick_cols = st.columns(3)
    quick_cols[0].markdown(
        dedent(
            """
            <div class="info-card">
                <div class="info-card-title">1. Choose a source</div>
                <div class="info-card-copy">Use the built-in traffic clips or replace any lane with your own video from the sidebar.</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
    quick_cols[1].markdown(
        dedent(
            """
            <div class="info-card">
                <div class="info-card-title">2. Start monitoring</div>
                <div class="info-card-copy">Press <strong>Start System</strong> to switch from preview mode into the live four-lane simulation.</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
    quick_cols[2].markdown(
        dedent(
            """
            <div class="info-card">
                <div class="info-card-title">3. Review signals</div>
                <div class="info-card-copy">Busier lanes receive longer green countdowns, while lighter lanes still get fair access to keep traffic optimized.</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    st.markdown("### Default Demo Sources")
    source_cols = st.columns(4)
    for index, lane_id in enumerate(LANE_IDS):
        default_path = DEFAULT_VIDEO_PATHS[lane_id]
        source_cols[index].markdown(
            dedent(
                f"""
                <div class="source-card">
                    <div class="source-lane">Lane {lane_id}</div>
                    <div class="source-title">{DEFAULT_VIDEO_LABELS[lane_id]}</div>
                    <div class="source-file">{default_path.name}</div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )


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
    figure, axis = plt.subplots(figsize=(12, 4), facecolor="#0c1727")
    axis.set_facecolor("#102038")
    palette = {
        1: "#6fdcff",
        2: "#74f2ce",
        3: "#f5c86d",
        4: "#ff8b8b",
    }

    for lane_id in LANE_IDS:
        axis.plot(
            data["step"],
            data[f"lane_{lane_id}"],
            linewidth=2.0,
            label=f"Lane {lane_id}",
            color=palette[lane_id],
        )

    axis.set_xlabel("Time Step", color="#eef4ff")
    axis.set_ylabel("Detected Vehicles", color="#eef4ff")
    axis.set_title("Real-Time Lane Density Trend", color="#f6fbff")
    axis.grid(alpha=0.22, color="#7aa2f7")
    axis.tick_params(colors="#d7e6ff")
    for spine in axis.spines.values():
        spine.set_color("#2f4666")
    legend = axis.legend(ncol=2, loc="upper right", facecolor="#102038", edgecolor="#2f4666")
    for text in legend.get_texts():
        text.set_color("#eef4ff")
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
        dedent(
            """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at 18% 12%, rgba(41, 118, 255, 0.22), transparent 24%),
                    radial-gradient(circle at 82% 14%, rgba(39, 214, 170, 0.16), transparent 24%),
                    radial-gradient(circle at 78% 84%, rgba(255, 170, 64, 0.12), transparent 20%),
                    linear-gradient(135deg, #07111d 0%, #0b1626 48%, #111e31 100%);
                color: #eef4ff;
                font-family: "Avenir Next", "Segoe UI", sans-serif;
            }
            [data-testid="stAppViewContainer"] > .main {
                background: transparent;
            }
            [data-testid="stHeader"] {
                background: rgba(0, 0, 0, 0);
            }
            [data-testid="stSidebar"] {
                background: rgba(8, 16, 28, 0.92);
                border-right: 1px solid rgba(122, 162, 247, 0.10);
                backdrop-filter: blur(18px);
            }
            [data-testid="stSidebar"] * {
                color: #eef4ff;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1220px;
            }
            .hero-panel,
            .ambient-panel,
            .info-card,
            .source-card {
                border: 1px solid rgba(122, 162, 247, 0.10);
                box-shadow: 0 24px 54px rgba(0, 0, 0, 0.28);
                backdrop-filter: blur(14px);
            }
            .hero-panel {
                padding: 1.6rem 1.7rem;
                border-radius: 28px;
                margin-bottom: 1.2rem;
                background: linear-gradient(145deg, rgba(10, 21, 36, 0.92), rgba(18, 33, 52, 0.82));
            }
            .hero-badge,
            .panel-kicker,
            .status-pill {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            .hero-badge {
                padding: 0.45rem 0.8rem;
                color: #9ae7dc;
                background: rgba(25, 178, 142, 0.16);
                border: 1px solid rgba(25, 178, 142, 0.24);
            }
            .hero-title {
                margin: 0.85rem 0 0.45rem;
                font-size: clamp(2.3rem, 4vw, 3.8rem);
                line-height: 1;
                font-weight: 800;
                letter-spacing: -0.04em;
                color: #f6fbff;
            }
            .hero-title span {
                color: transparent;
                background: linear-gradient(120deg, #6fdcff 0%, #74f2ce 34%, #f5c86d 68%, #ff7f7f 100%);
                -webkit-background-clip: text;
                background-clip: text;
                text-shadow: 0 8px 28px rgba(111, 220, 255, 0.12);
            }
            .hero-subtitle,
            .panel-copy {
                max-width: 850px;
                color: #b9cae5;
                font-size: 1rem;
                line-height: 1.65;
                margin-bottom: 0;
            }
            .hero-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 0.65rem;
                margin-top: 1rem;
            }
            .hero-meta span,
            .status-pill {
                padding: 0.45rem 0.75rem;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(122, 162, 247, 0.12);
                color: #eef4ff;
            }
            .ambient-panel {
                padding: 1.1rem 1.2rem;
                border-radius: 22px;
                margin: 0.5rem 0 1rem;
                background: rgba(11, 20, 34, 0.84);
            }
            .panel-header-row {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
                margin-bottom: 0.35rem;
            }
            .panel-header-row h3 {
                margin: 0.15rem 0 0;
                color: #f6fbff;
                font-size: 1.3rem;
            }
            .panel-kicker {
                color: #f7c774;
            }
            .info-card,
            .source-card {
                background: rgba(12, 22, 38, 0.86);
                border-radius: 20px;
                padding: 1rem 1.05rem;
                min-height: 134px;
                margin-bottom: 0.65rem;
            }
            .info-card-title,
            .source-lane {
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #f7c774;
                margin-bottom: 0.45rem;
            }
            .info-card-copy,
            .source-file {
                color: #b9cae5;
                line-height: 1.6;
                font-size: 0.95rem;
            }
            .source-title {
                font-size: 1rem;
                font-weight: 700;
                color: #f4f8ff;
                margin-bottom: 0.35rem;
            }
            .signal-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 14px;
                margin-top: 0.5rem;
                margin-bottom: 0.8rem;
            }
            .signal-card {
                border-radius: 22px;
                padding: 1rem 0.9rem;
                background: rgba(12, 22, 38, 0.88);
                border: 1px solid rgba(122, 162, 247, 0.10);
                box-shadow: 0 12px 26px rgba(0, 0, 0, 0.22);
                text-align: center;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .signal-card.active {
                background: linear-gradient(145deg, rgba(11, 46, 36, 0.96), rgba(13, 27, 23, 0.92));
                border-color: rgba(47, 191, 113, 0.24);
                box-shadow: 0 16px 30px rgba(47, 191, 113, 0.14);
            }
            .signal-card.inactive {
                background: linear-gradient(145deg, rgba(48, 18, 18, 0.94), rgba(20, 12, 17, 0.90));
                border-color: rgba(231, 76, 60, 0.16);
            }
            .signal-light {
                width: 28px;
                height: 28px;
                border-radius: 50%;
                margin: 0 auto 0.65rem auto;
            }
            .signal-card.active .signal-light {
                background: #2fbf71;
                box-shadow: 0 0 0 8px rgba(47, 191, 113, 0.12), 0 0 22px rgba(47, 191, 113, 0.28);
            }
            .signal-card.inactive .signal-light {
                background: #e74c3c;
                box-shadow: 0 0 0 8px rgba(231, 76, 60, 0.10), 0 0 18px rgba(231, 76, 60, 0.18);
            }
            .signal-title {
                color: #f4f8ff;
                font-size: 0.95rem;
                font-weight: 700;
            }
            .signal-status {
                color: #eef4ff;
                font-size: 0.88rem;
                margin-top: 0.35rem;
                font-weight: 800;
                letter-spacing: 0.08em;
            }
            .signal-timer {
                color: #b9cae5;
                font-size: 0.9rem;
                margin-top: 0.28rem;
            }
            [data-testid="stMetric"] {
                background: rgba(12, 22, 38, 0.82);
                border: 1px solid rgba(122, 162, 247, 0.10);
                border-radius: 18px;
                padding: 0.75rem 0.85rem;
                box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
            }
            [data-testid="stMetricLabel"],
            [data-testid="stMetricValue"] {
                color: #f6fbff;
            }
            [data-testid="stDataFrame"] {
                background: rgba(12, 22, 38, 0.82);
                border-radius: 18px;
                padding: 0.35rem;
            }
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            .stSlider,
            .stRadio,
            .stFileUploader,
            .stNumberInput,
            .stMarkdown,
            .stCaption,
            .stText {
                color: #eef4ff;
            }
            .stAlert {
                background: rgba(12, 22, 38, 0.82);
                color: #eef4ff;
                border: 1px solid rgba(122, 162, 247, 0.10);
            }
            @media (max-width: 900px) {
                .panel-header-row {
                    flex-direction: column;
                }
            }
        </style>
        """
        ),
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
            st.caption("Built-in demo videos are selected by default. Upload a file below to replace any lane.")
            for lane_id in LANE_IDS:
                uploaded_files[lane_id] = st.file_uploader(
                    f"Lane {lane_id} video",
                    type=["mp4", "avi", "mov"],
                    key=f"lane_{lane_id}_uploader",
                )
            if st.button("Generate Synthetic Backup Videos", use_container_width=True):
                generate_dummy_traffic_videos(video_dir=DEMO_VIDEOS_DIR, lane_ids=LANE_IDS)
                st.success("Synthetic backup demo videos generated.")
        else:
            st.caption(
                "Webcam mode is intended for local desktop runs. "
                "Use Simulation mode for GitHub, Docker, or cloud deployments."
            )
            webcam_index = int(
                st.number_input("Webcam Index", min_value=0, max_value=10, value=0, step=1)
            )

        start_clicked = st.button("Start System", type="primary", use_container_width=True)
        stop_clicked = st.button("Stop System", use_container_width=True)

        if st.session_state.running:
            st.success("System running")
        else:
            st.warning("System stopped")

    render_app_header(mode=mode)

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
        render_welcome_state(mode=mode)
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
