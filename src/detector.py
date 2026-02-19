from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import cv2
from ultralytics import YOLO

from .config import CONFIDENCE_THRESHOLD, DETECTION_CLASSES, IOU_THRESHOLD, MODEL_PATH


@dataclass
class Detection:
    bbox: Tuple[int, int, int, int]
    confidence: float
    label: str


class VehicleDetector:
    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        iou_threshold: float = IOU_THRESHOLD,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.target_classes = set(DETECTION_CLASSES)
        self.model = self._load_model(model_path)

    def _load_model(self, model_path: Path) -> YOLO:
        model_path = Path(model_path)
        should_use_local = model_path.exists() and model_path.stat().st_size > 1_000_000
        model_source = str(model_path) if should_use_local else "yolov8n.pt"

        try:
            model = YOLO(model_source)
        except Exception:
            model = YOLO("yolov8n.pt")

        # Keep a local copy in /models when possible for predictable project layout.
        if not should_use_local:
            try:
                checkpoint_path = Path(model.ckpt_path)
                model_path.parent.mkdir(parents=True, exist_ok=True)
                if checkpoint_path.exists() and checkpoint_path != model_path:
                    shutil.copy(checkpoint_path, model_path)
            except Exception:
                pass

        return model

    @staticmethod
    def _normalize_label(label: str) -> str:
        if label in {"motorcycle", "bicycle"}:
            return "bike"
        return label

    def detect(self, frame) -> List[Detection]:
        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )
        if not results:
            return []

        result = results[0]
        detections: List[Detection] = []

        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            if class_name not in self.target_classes:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            detections.append(
                Detection(
                    bbox=(x1, y1, x2, y2),
                    confidence=confidence,
                    label=self._normalize_label(class_name),
                )
            )

        return detections

    @staticmethod
    def draw_detections(frame, detections: List[Detection]):
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 205, 50), 2)
            cv2.putText(
                frame,
                f"{detection.label} {detection.confidence:.2f}",
                (x1, max(y1 - 8, 12)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
        return frame
