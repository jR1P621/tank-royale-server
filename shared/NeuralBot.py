import json
import math
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import onnxruntime as ort
from robocode_tank_royale.bot_api import Bot, BotInfo
from robocode_tank_royale.bot_api.events import (
    BulletFiredEvent,
    BulletHitBulletEvent,
    BulletHitBotEvent,
    HitByBulletEvent,
    HitWallEvent,
    ScannedBotEvent,
)
from robocode_tank_royale.bot_api.graphics import Color


@dataclass
class BulletInfo:
    x: float
    y: float
    direction: float
    power: float
    is_enemy: bool
    tick: int


class NeuralBot(Bot):
    def __init__(self) -> None:
        super().__init__(BotInfo.from_file("NeuralBot.json"))
        self.session = ort.InferenceSession("model.onnx")
        self.active_bullets: Dict[int, BulletInfo] = {}
        self.last_enemy_data: List[float] = [
            0.0
        ] * 6  # x, y, dir, energy, distance, speed
        self.input_tensor_info: Dict[str, bool] = {
            "includeEnemy": True,
            "includeBullets": False,
            "includeRadar": False,
        }
        self.expected_input_size = self._get_expected_input_size()
        self.inference_times: List[float] = []
        self.skipped_turn_count = 0

    def run(self) -> None:
        config = self._load_config()
        self.input_tensor_info = {
            "includeEnemy": bool(
                config.get("inputTensorInfo", {}).get("includeEnemy", True)
            ),
            "includeBullets": bool(
                config.get("inputTensorInfo", {}).get("includeBullets", False)
            ),
            "includeRadar": bool(
                config.get("inputTensorInfo", {}).get("includeRadar", False)
            ),
        }

        self._apply_colors(config)

        input_info = config.get("inputInfo", {})
        input_type = str(input_info.get("inputType", "neural-network"))
        if input_type != "neural-network":
            print("Skipping neural network-specific steps.")
            return

        while self.running:
            state = self._get_state_vector()

            # Time the neural network inference
            inference_start = time.perf_counter()
            actions = self._infer_actions(state)
            inference_elapsed = (
                time.perf_counter() - inference_start
            ) * 1000  # Convert to ms
            self.inference_times.append(inference_elapsed)

            self._execute_actions(actions)
            self.set_turn_radar_right(360)
            self.go()

        self._print_stats()

    def _print_stats(self) -> None:
        """Called when the game ends. Print timing statistics."""
        if len(self.inference_times) == 0:
            return

        # Calculate statistics
        min_time = min(self.inference_times)
        max_time = max(self.inference_times)
        mean_time = statistics.mean(self.inference_times)
        median_time = statistics.median(self.inference_times)

        # Calculate percentiles
        p95_time = None
        p99_time = None
        try:
            p95_time = statistics.quantiles(self.inference_times, n=20)[
                18
            ]  # 95th percentile
            p99_time = statistics.quantiles(self.inference_times, n=100)[
                98
            ]  # 99th percentile
        except (statistics.StatisticsError, IndexError):
            pass  # Not enough data points for percentiles

        # Count slow inferences
        slow_threshold_ms = 1000  # 1 second
        slow_inferences = sum(1 for t in self.inference_times if t > slow_threshold_ms)

        # Print summary
        print(
            f"\r=== Timing Summary ===\r"
            + f"Total inferences: {len(self.inference_times)}\r"
            + f"Skipped turns: {self.skipped_turn_count}\r"
            + f"Inference time (ms):\r"
            + f"  Min:    {min_time:.2f}\r"
            + f"  Max:    {max_time:.2f}\r"
            + f"  Mean:   {mean_time:.2f}\r"
            + f"  Median: {median_time:.2f}\r"
            + (f"  P95:    {p95_time:.2f}\r" if p95_time is not None else "")
            + (f"  P99:    {p99_time:.2f}\r" if p99_time is not None else "")
            + f"Slow inferences (>{slow_threshold_ms}ms): {slow_inferences}\r"
            + f"==================================\r",
            flush=True,
        )

    def _load_config(self) -> dict:
        config_path = Path("config.json")
        if not config_path.exists():
            return {
                "inputTensorInfo": self.input_tensor_info,
                "colors": {},
                "inputInfo": {"inputType": "neural-network"},
            }

        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        if "inputInfo" not in config:
            config["inputInfo"] = {"inputType": "neural-network"}

        if "inputTensorInfo" not in config:
            config["inputTensorInfo"] = self.input_tensor_info

        return config

    def _apply_colors(self, config: dict) -> None:
        colors = config.get("colors", {})

        def rgb(key: str, fallback: List[int]) -> Color:
            value = colors.get(key, fallback)
            if not isinstance(value, list) or len(value) != 3:
                value = fallback
            return Color.from_rgb(int(value[0]), int(value[1]), int(value[2]))

        self.body_color = rgb("bodyColor", [80, 120, 200])
        self.turret_color = rgb("turretColor", [80, 120, 200])
        self.radar_color = rgb("radarColor", [120, 180, 255])
        self.bullet_color = rgb("bulletColor", [255, 200, 80])
        if "scanColor" in colors:
            self.scan_color = rgb("scanColor", [140, 220, 140])

    def _get_state_vector(self) -> np.ndarray:
        arena_width = max(float(self.arena_width), 1.0)
        arena_height = max(float(self.arena_height), 1.0)
        arena_scale = max(arena_width, arena_height)

        state: List[float] = [
            float(self.x) / arena_width,
            float(self.y) / arena_height,
            float(self.direction) / 360.0,
            float(self.energy) / 100.0,
            float(self.gun_heat) / 3.0,
            float(self.gun_direction) / 360.0,
            float(self.radar_direction) / 360.0,
            1.0,
            1.0,
        ]

        if self.input_tensor_info.get("includeEnemy", True):
            state.extend(
                [
                    self.last_enemy_data[0] / arena_width,
                    self.last_enemy_data[1] / arena_height,
                    self.last_enemy_data[2] / 360.0,
                    self.last_enemy_data[3] / 100.0,
                    self.last_enemy_data[4] / arena_scale,
                    self.last_enemy_data[5] / 8.0,
                ]
            )

        if self.input_tensor_info.get("includeBullets", False):
            enemy_bullets = sorted(
                (b for b in self.active_bullets.values() if b.is_enemy),
                key=lambda b: self.distance_to(b.x, b.y),
            )[:5]

            for bullet in enemy_bullets:
                rel_angle = (
                    (
                        math.degrees(math.atan2(bullet.y - self.y, bullet.x - self.x))
                        - self.direction
                        + 360.0
                    )
                    % 360.0
                ) / 360.0
                dist = float(self.distance_to(bullet.x, bullet.y)) / arena_scale
                state.extend([rel_angle, dist, 1.0])

            while len(state) < 27:
                state.append(0.0)

        return np.asarray(state, dtype=np.float32)

    def _infer_actions(self, state: np.ndarray) -> np.ndarray:
        if self.expected_input_size > 0:
            if state.size > self.expected_input_size:
                state = state[: self.expected_input_size]
            elif state.size < self.expected_input_size:
                pad = np.zeros(self.expected_input_size - state.size, dtype=np.float32)
                state = np.concatenate((state, pad), axis=0)

        input_name = self.session.get_inputs()[0].name
        result = self.session.run(None, {input_name: state.reshape(1, -1)})
        output = np.asarray(result[0], dtype=np.float32).reshape(-1)
        if output.size < 4:
            padded = np.zeros(4, dtype=np.float32)
            padded[: output.size] = output
            return padded
        return output[:4]

    def _get_expected_input_size(self) -> int:
        shape = self.session.get_inputs()[0].shape
        if len(shape) < 2:
            return 0
        size = shape[1]
        return int(size) if isinstance(size, int) else 0

    def _execute_actions(self, actions: np.ndarray) -> None:
        body_turn = float(actions[0]) * 180.0
        move_dist = float(actions[1]) * 100.0
        gun_turn = float(actions[2]) * 180.0
        fire_power = max(0.0, min(float(actions[3]) * 3.0, 3.0))

        self.set_turn_left(body_turn)
        if move_dist > 0:
            self.set_forward(move_dist)
        elif move_dist < 0:
            self.set_back(-move_dist)

        self.set_turn_gun_left(gun_turn)
        if fire_power > 0.0 and self.gun_heat <= 0.0:
            self.set_fire(fire_power)

    def on_scanned_bot(self, evt: ScannedBotEvent) -> None:
        self.last_enemy_data[0] = float(evt.x)
        self.last_enemy_data[1] = float(evt.y)
        self.last_enemy_data[2] = float(evt.direction)
        self.last_enemy_data[3] = float(evt.energy)
        self.last_enemy_data[4] = float(self.distance_to(evt.x, evt.y))
        self.last_enemy_data[5] = float(evt.speed)

    def on_bullet_fired(self, evt: BulletFiredEvent) -> None:
        bullet = evt.bullet
        self.active_bullets[int(bullet.bullet_id)] = BulletInfo(
            x=float(bullet.x),
            y=float(bullet.y),
            direction=float(bullet.direction),
            power=float(bullet.power),
            is_enemy=int(bullet.owner_id) != int(self.my_id),
            tick=int(self.turn_number),
        )

    def on_bullet_hit(self, evt: BulletHitBotEvent) -> None:
        self.active_bullets.pop(int(evt.bullet.bullet_id), None)

    def on_bullet_hit_bullet(self, evt: BulletHitBulletEvent) -> None:
        self.active_bullets.pop(int(evt.bullet.bullet_id), None)
        self.active_bullets.pop(int(evt.hit_bullet.bullet_id), None)

    def on_hit_by_bullet(self, evt: HitByBulletEvent) -> None:
        pass

    def on_hit_wall(self, evt: HitWallEvent) -> None:
        pass

    def on_skipped_turn(self, evt) -> None:
        """Called when a turn is skipped due to timeout or other server-side issues."""
        self.skipped_turn_count += 1

    def on_game_ended(self, evt) -> None:
        """Called when the game ends. Print timing statistics."""
        # self._print_stats()
        pass


if __name__ == "__main__":
    NeuralBot().start()
