import sys

sys.path.insert(0, ".")

import numpy as np
import cv2
from unittest.mock import patch, Mock

from detector import Detector, DetectionResult
from overlay import draw_hud, DetectionState
from pixelate import pixelate_region


def test_pipeline_no_webcam():
    frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    original = frame.copy()

    mock_result = DetectionResult(
        faces=[{"class": "FACE_FEMALE", "score": 0.9, "box": [100, 100, 80, 80]}],
        belly=[{"class": "BELLY_EXPOSED", "score": 0.8, "box": [200, 200, 100, 100]}],
        sensitive=[
            {"class": "PENIS_EXPOSED", "score": 0.85, "box": [300, 300, 50, 50]}
        ],
    )

    state = DetectionState(
        human_present=True,
        belly_boxes=[mock_result.belly[0]["box"]],
        sensitive_boxes=[mock_result.sensitive[0]["box"]],
        status_text="HUMAN DETECTED",
    )

    for box in state.sensitive_boxes:
        pixelate_region(frame, box)

    draw_hud(frame, state, tick=0, scan_y=50)

    assert not np.array_equal(frame, original)

    import time

    start = time.time()
    for _ in range(10):
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        pixelate_region(frame, [100, 100, 80, 80])
        draw_hud(frame, state, 0, 50)
    elapsed = time.time() - start

    assert elapsed < 5.0


if __name__ == "__main__":
    test_pipeline_no_webcam()
    print("Integration test passed!")
