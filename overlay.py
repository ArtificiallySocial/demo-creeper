import datetime
import random
from dataclasses import dataclass, field
from typing import List

import numpy as np
import cv2

import config


@dataclass
class DetectionState:
    human_present: bool = False
    belly_boxes: List = field(default_factory=list)
    sensitive_boxes: List = field(default_factory=list)
    status_text: str = "SCANNING..."


def draw_corner_brackets(frame):
    h, w = frame.shape[:2]
    bracket_size = 40
    thickness = 2

    # Each entry: (corner_vertex, arm1_end, arm2_end)
    pts = [
        [(0, 0), (bracket_size, 0), (0, bracket_size)],
        [(w, 0), (w - bracket_size, 0), (w, bracket_size)],
        [(0, h), (bracket_size, h), (0, h - bracket_size)],
        [(w, h), (w - bracket_size, h), (w, h - bracket_size)],
    ]

    for corner, arm1, arm2 in pts:
        cv2.line(frame, corner, arm1, config.HUD_COLOR_BGR, thickness)
        cv2.line(frame, corner, arm2, config.HUD_COLOR_BGR, thickness)


def draw_timestamp(frame):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    cv2.putText(
        frame, now, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.HUD_COLOR_BGR, 2
    )


_last_hex_values = ["00"] * 8


def draw_scrolling_hex(frame, tick):
    global _last_hex_values
    h, w = frame.shape[:2]
    if tick % 10 == 0:
        _last_hex_values = [format(random.randint(0, 255), "02X") for _ in range(8)]
    frame[10:35, w - 180 : w - 10] = (0, 0, 0)
    cv2.putText(
        frame,
        " ".join(_last_hex_values),
        (w - 175, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        config.HUD_DIM_BGR,
        1,
    )


def draw_status_bar(frame, state):
    h, w = frame.shape[:2]
    colors = {
        "SCANNING...": (128, 128, 128),
        "HUMAN DETECTED": (0, 255, 0),
        "TARGET ACQUIRED": (0, 255, 255),
        "ALERT": (0, 0, 255),
    }
    color = colors.get(state.status_text, (128, 128, 128))
    cv2.putText(
        frame, state.status_text, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
    )


def draw_scan_line(frame, position):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    # soft glow band
    for offset, thickness in [(-4, 8), (-2, 4), (0, 2)]:
        y = position + offset
        if 0 <= y < h:
            cv2.line(overlay, (0, y), (w, y), (200, 200, 255), thickness)
    # bright core
    cv2.line(overlay, (0, position), (w, position), (255, 255, 255), 1)
    cv2.addWeighted(
        overlay, config.SCAN_LINE_ALPHA, frame, 1 - config.SCAN_LINE_ALPHA, 0, frame
    )


def draw_belly_target(frame, box, tick):
    x, y, w, h = [int(v) for v in box]
    h_frame, w_frame = frame.shape[:2]
    x = max(0, min(x, w_frame - 1))
    y = max(0, min(y, h_frame - 1))
    w = min(w, w_frame - x)
    h = min(h, h_frame - y)

    pulse = int(5 + 5 * np.sin(tick * 0.1))

    cv2.rectangle(frame, (x, y), (x + w, y + h), config.HUD_COLOR_BGR, 4)
    cv2.rectangle(
        frame,
        (x - pulse, y - pulse),
        (x + w + pulse, y + h + pulse),
        config.HUD_DIM_BGR,
        2,
    )

    cx, cy = x + w // 2, y + h // 2
    cv2.line(frame, (cx - 10, cy), (cx + 10, cy), config.HUD_COLOR_BGR, 1)
    cv2.line(frame, (cx, cy - 10), (cx, cy + 10), config.HUD_COLOR_BGR, 1)


def draw_sensitive_box(frame, box):
    x, y, w, h = [int(v) for v in box]
    h_frame, w_frame = frame.shape[:2]
    x = max(0, min(x, w_frame - 1))
    y = max(0, min(y, h_frame - 1))
    w = min(w, w_frame - x)
    h = min(h, h_frame - y)
    cv2.rectangle(frame, (x, y), (x + w, y + h), config.HUD_DIM_BGR, 1)


def draw_hud(frame, state, tick, scan_y):
    draw_corner_brackets(frame)
    draw_timestamp(frame)
    draw_scrolling_hex(frame, tick)
    draw_status_bar(frame, state)

    for box in state.belly_boxes:
        draw_belly_target(frame, box, tick)

    for box in state.sensitive_boxes:
        draw_sensitive_box(frame, box)

    h = frame.shape[0]
    if 0 <= scan_y < h:
        draw_scan_line(frame, scan_y)
