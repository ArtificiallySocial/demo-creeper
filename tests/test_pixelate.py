import sys

sys.path.insert(0, ".")

import numpy as np
import cv2
from pixelate import pixelate_region


def test_pixelate_changes_pixels():
    frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    original = frame.copy()

    pixelate_region(frame, [10, 10, 30, 30])

    assert not np.array_equal(frame, original)


def test_pixelate_out_of_bounds():
    frame = np.full((100, 100, 3), 128, dtype=np.uint8)
    original = frame.copy()

    pixelate_region(frame, [90, 90, 50, 50])

    assert np.array_equal(frame, original)


def test_pixelate_partial_bounds():
    frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    original = frame.copy()

    pixelate_region(frame, [-5, -5, 30, 30])

    assert not np.array_equal(frame, original)


if __name__ == "__main__":
    test_pixelate_changes_pixels()
    test_pixelate_out_of_bounds()
    test_pixelate_partial_bounds()
    print("All pixelate tests passed!")
