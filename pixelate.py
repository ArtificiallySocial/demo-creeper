import numpy as np
import cv2

import config


def pixelate_region(
    frame: np.ndarray, box: list, block_size: int = config.PIXELATE_BLOCK_SIZE
) -> None:
    x, y, w, h = box

    h_frame, w_frame = frame.shape[:2]

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w_frame, x + w)
    y2 = min(h_frame, y + h)

    if x2 <= x1 or y2 <= y1:
        return

    roi = frame[y1:y2, x1:x2]

    reduced_h = max(1, (y2 - y1) // block_size)
    reduced_w = max(1, (x2 - x1) // block_size)

    small = cv2.resize(roi, (reduced_w, reduced_h), interpolation=cv2.INTER_NEAREST)
    pixelated = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)

    frame[y1:y2, x1:x2] = pixelated
