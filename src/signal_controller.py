from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List

from .config import (
    MAX_GREEN_TIME,
    MIN_GREEN_TIME,
    TOTAL_CYCLE_TIME,
    VEHICLE_WEIGHT,
    WAITING_WEIGHT,
)


@dataclass
class LaneState:
    lane_id: int
    vehicle_count: int = 0
    waiting_time: float = 0.0
    priority_score: float = 0.0


class AdaptiveSignalController:
    def __init__(self, lane_ids: Iterable[int]) -> None:
        self.lane_ids: List[int] = list(lane_ids)
        self.lanes: Dict[int, LaneState] = {lane_id: LaneState(lane_id) for lane_id in self.lane_ids}

        self.pending_cycle_lanes = set(self.lane_ids)
        self.current_green_lane: int | None = None
        self.current_green_time: int = MIN_GREEN_TIME
        self.current_countdown: float = float(MIN_GREEN_TIME)
        self.cycle_elapsed: int = 0

    def bootstrap(self, lane_counts: Dict[int, int]) -> None:
        self.update_vehicle_counts(lane_counts)
        self._switch_to_next_lane()

    def update_vehicle_counts(self, lane_counts: Dict[int, int]) -> None:
        for lane_id, count in lane_counts.items():
            self.lanes[lane_id].vehicle_count = int(count)
        self._recompute_priorities()

    def tick(self, delta_seconds: float) -> None:
        if self.current_green_lane is None:
            self._switch_to_next_lane()
            return

        for lane_id, lane_state in self.lanes.items():
            if lane_id != self.current_green_lane:
                lane_state.waiting_time += delta_seconds

        self.current_countdown -= delta_seconds
        self._recompute_priorities()

        if self.current_countdown <= 0:
            self._switch_to_next_lane()

    def _recompute_priorities(self) -> None:
        for lane_state in self.lanes.values():
            lane_state.priority_score = (
                lane_state.vehicle_count * VEHICLE_WEIGHT
                + lane_state.waiting_time * WAITING_WEIGHT
            )

    @staticmethod
    def density_based_green_time(vehicle_count: int) -> int:
        if vehicle_count <= 10:
            return 15
        if vehicle_count <= 25:
            return 25
        if vehicle_count <= 50:
            return 40
        return 60

    def _allocate_green_time(self, lane_id: int) -> int:
        desired_time = self.density_based_green_time(self.lanes[lane_id].vehicle_count)
        desired_time = max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, desired_time))

        remaining_lanes_after_this = len(self.pending_cycle_lanes) - 1
        reserve_for_remaining_lanes = remaining_lanes_after_this * MIN_GREEN_TIME
        available_budget = TOTAL_CYCLE_TIME - self.cycle_elapsed - reserve_for_remaining_lanes

        bounded_time = min(desired_time, max(MIN_GREEN_TIME, available_budget), MAX_GREEN_TIME)
        return int(max(MIN_GREEN_TIME, bounded_time))

    def _select_next_lane(self) -> int:
        if not self.pending_cycle_lanes:
            self.pending_cycle_lanes = set(self.lane_ids)
            self.cycle_elapsed = 0

        return max(
            self.pending_cycle_lanes,
            key=lambda lane_id: (
                self.lanes[lane_id].priority_score,
                self.lanes[lane_id].waiting_time,
                self.lanes[lane_id].vehicle_count,
                -lane_id,
            ),
        )

    def _switch_to_next_lane(self) -> None:
        next_lane = self._select_next_lane()
        allocated_green_time = self._allocate_green_time(next_lane)

        self.current_green_lane = next_lane
        self.current_green_time = allocated_green_time
        self.current_countdown = float(allocated_green_time)
        self.cycle_elapsed += allocated_green_time

        self.pending_cycle_lanes.remove(next_lane)
        self.lanes[next_lane].waiting_time = 0.0
        self._recompute_priorities()

    def get_state(self) -> dict:
        return {
            "current_green_lane": self.current_green_lane,
            "allocated_green_time": self.current_green_time,
            "countdown": int(math.ceil(max(self.current_countdown, 0))),
            "cycle_elapsed": int(self.cycle_elapsed),
            "waiting_times": {
                lane_id: round(self.lanes[lane_id].waiting_time, 2) for lane_id in self.lane_ids
            },
            "priority_scores": {
                lane_id: round(self.lanes[lane_id].priority_score, 2) for lane_id in self.lane_ids
            },
        }
