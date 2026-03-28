import sys

sys.path.insert(0, ".")

import numpy as np
from overlay import draw_hud, DetectionState


def test_hud_renders():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    state = DetectionState(
        human_present=True,
        belly_boxes=[[100, 100, 80, 80]],
        sensitive_boxes=[[200, 200, 60, 60]],
        status_text="HUMAN DETECTED",
    )

    draw_hud(frame, state, tick=0, scan_y=50)

    assert frame.sum() > 0


if __name__ == "__main__":
    test_hud_renders()
    print("Overlay test passed!")
