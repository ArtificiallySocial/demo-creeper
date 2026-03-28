import time
import cv2
from concurrent.futures import ThreadPoolExecutor

import config
from audio import AudioManager
from detector import Detector
from overlay import DetectionState, draw_hud
from pixelate import pixelate_region


def main():
    audio = AudioManager()
    detector = Detector()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    cv2.namedWindow(config.WINDOW_TITLE)

    state = DetectionState()
    frame_count = 0
    tick = 0
    scan_y = 0
    executor = ThreadPoolExecutor(max_workers=1)
    future = None
    last_result = None
    last_raw_classes = []

    prev_belly_present = False
    prev_sensitive_present = False
    belly_last_seen = 0.0
    last_belly_boxes = []

    human_present = False
    human_gone_time = 0
    HUMAN_DEBOUNCE_SECONDS = 3.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % config.SNAPSHOT_INTERVAL_FRAMES == 0:
            future = executor.submit(detector.analyze_frame, frame.copy())

        if future and future.done():
            last_result, last_raw_classes = future.result()
            future = None

            if last_result:
                fresh_belly = [d["box"] for d in last_result.belly]
                if fresh_belly:
                    last_belly_boxes = fresh_belly
                    belly_last_seen = time.time()
                state.sensitive_boxes = [d["box"] for d in last_result.sensitive]

            if belly_last_seen > 0 and (time.time() - belly_last_seen) < config.BELLY_PERSIST_SECONDS:
                state.belly_boxes = last_belly_boxes
            else:
                state.belly_boxes = []

            if last_raw_classes:
                print(f"Detections: {last_raw_classes}")
            last_raw_classes = []

        face_detected = last_result and len(last_result.faces) > 0
        belly_now = len(state.belly_boxes) > 0
        sensitive_now = len(state.sensitive_boxes) > 0

        if face_detected and human_present:
            human_gone_time = 0

        if face_detected and not human_present:
            never_seen = human_gone_time == 0
            was_gone_long_enough = (
                human_gone_time > 0
                and (time.time() - human_gone_time) > HUMAN_DEBOUNCE_SECONDS
            )
            if never_seen or was_gone_long_enough:
                audio.trigger("HUMAN_DETECTED")
                print("Sound: HUMAN_DETECTED")
            state.status_text = "HUMAN DETECTED"
            human_present = True
            human_gone_time = 0

        if not face_detected and human_present and human_gone_time == 0:
            human_gone_time = time.time()

        if (
            human_gone_time > 0
            and (time.time() - human_gone_time) > HUMAN_DEBOUNCE_SECONDS
        ):
            human_present = False
            human_gone_time = 0
            state.status_text = "SCANNING..."
            audio.reset_priority()

        state.human_present = human_present

        if belly_now and not prev_belly_present:
            audio.trigger("TARGET_ACQUIRED")
            state.status_text = "TARGET ACQUIRED"
            print("Sound: TARGET_ACQUIRED")

        if sensitive_now and not prev_sensitive_present:
            audio.trigger("ALERT")
            state.status_text = "ALERT"
            print("Sound: ALERT")

        if not human_present and not belly_now and not sensitive_now:
            state.status_text = "SCANNING..."
            audio.reset_priority()

        prev_belly_present = belly_now
        prev_sensitive_present = sensitive_now

        for box in state.sensitive_boxes:
            pixelate_region(frame, box)

        h, w = frame.shape[:2]
        scan_y = (scan_y + config.SCAN_LINE_SPEED) % h

        draw_hud(frame, state, tick, scan_y)

        cv2.imshow(config.WINDOW_TITLE, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        tick += 1

    cap.release()
    cv2.destroyAllWindows()
    audio.stop_all()
    executor.shutdown(wait=False)


if __name__ == "__main__":
    main()
