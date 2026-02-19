from __future__ import annotations

from collections import deque
from typing import Dict, Iterable


class LaneCounter:
    def __init__(self, lane_ids: Iterable[int], smoothing_window: int = 4) -> None:
        self.lane_ids = list(lane_ids)
        self.smoothing_window = max(1, smoothing_window)
        self._history = {
            lane_id: deque(maxlen=self.smoothing_window) for lane_id in self.lane_ids
        }

    def update(self, lane_id: int, detected_count: int) -> None:
        self._history[lane_id].append(int(detected_count))

    def get_count(self, lane_id: int) -> int:
        history = self._history[lane_id]
        if not history:
            return 0
        return int(round(sum(history) / len(history)))

    def get_counts(self) -> Dict[int, int]:
        return {lane_id: self.get_count(lane_id) for lane_id in self.lane_ids}

    @staticmethod
    def density_band(vehicle_count: int) -> str:
        if vehicle_count <= 10:
            return "Low"
        if vehicle_count <= 25:
            return "Medium"
        if vehicle_count <= 50:
            return "High"
        return "Critical"
