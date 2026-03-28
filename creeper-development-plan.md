# 🤖 Creeper — Complete Development Plan

## Confirmed Stack

| Concern | Choice | Rationale |
|---|---|---|
| Language | Python 3.11 | NudeNet requires Python 3.8+; 3.11 is well-supported on Apple Silicon |
| ML Model | NudeNet v3 (ONNX) | No TensorFlow dependency, lightweight, runs CPU-only fine on M-series, has `BELLY_EXPOSED`, face, and explicit classes with bounding boxes |
| Video | OpenCV (`cv2`) | Industry standard for webcam capture + frame rendering + drawing |
| Audio | `pygame.mixer` | Best cross-platform MP3 playback from Python; works on macOS without system dependencies |
| Environment | `venv` + `pip` | Simple, no conda required |
| Platform | macOS Apple Silicon (M1/M2/M3/M4) | |
| Packaging | Terminal script (`run.sh`) | |
| Audio files | 4 placeholder MP3s, swap-ready | |
| HUD | Scan line effect included | |

---

## Project Structure

```
creeper/
├── main.py
├── detector.py
├── overlay.py
├── audio.py
├── pixelate.py
├── config.py
├── assets/
│   ├── startup.mp3
│   ├── human_detected.mp3
│   ├── target_acquired.mp3
│   └── alert.mp3
├── tests/
│   ├── test_detector.py
│   ├── test_audio.py
│   ├── test_pixelate.py
│   └── test_integration.py
├── requirements.txt
├── run.sh
└── README.md
```

---

## NudeNet Class Map

| NudeNet Class | Creeper Behavior |
|---|---|
| `FACE_FEMALE`, `FACE_MALE` | Human present → `human_detected.mp3` (on entry) |
| `BELLY_EXPOSED` | Target → red targeting box + `target_acquired.mp3` |
| `BUTTOCKS_EXPOSED`, `FEMALE_BREAST_EXPOSED`, `MALE_BREAST_EXPOSED`, `PENIS_EXPOSED`, `VAGINA_EXPOSED`, `ANUS_EXPOSED` | Pixelate region + `alert.mp3` |
| `ARMPITS_EXPOSED`, `FEET_EXPOSED`, all `*_COVERED` variants | Ignored entirely |

---

## Phase 1 — Environment Setup

**Goal:** Working Python environment with all dependencies confirmed on Apple Silicon.

1. Confirm Python 3.11: `python3.11 --version`. If missing: `brew install python@3.11`
2. Create and activate venv:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
3. Install all dependencies:
   ```bash
   pip install nudenet opencv-python pygame numpy
   ```
4. Smoke-test NudeNet:
   ```bash
   python -c "from nudenet import NudeDetector; NudeDetector(); print('NudeNet OK')"
   ```
   > NudeNet will download its ~7MB ONNX model on first run — expected.
5. Smoke-test webcam:
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   assert cap.isOpened(), "Webcam failed to open"
   cap.release()
   print("Webcam OK")
   ```
   > macOS will prompt for camera permission on first run — must grant it.
6. Generate 4 silent placeholder MP3s using a short Python script with `wave` + `ffmpeg` (or copy a 1-second silent MP3 four times). Named exactly as the asset paths above.

**✅ Checkpoint:** All 4 smoke tests pass, `assets/` folder has 4 valid (silent) MP3s.

---

## Phase 2 — `config.py`

**Goal:** Single source of truth for all tunable constants. Written first so all other modules import from it.

```python
# Detection
SNAPSHOT_INTERVAL_FRAMES = 15     # run NudeNet every N frames (~2x/sec at 30fps)
MIN_DETECTION_SCORE = 0.45        # confidence threshold

# Audio
AUDIO_COOLDOWN_SECONDS = 3.0      # min gap before re-triggering same sound

# Pixelation
PIXELATE_BLOCK_SIZE = 20

# HUD
HUD_COLOR_BGR = (0, 0, 200)       # red
HUD_DIM_BGR = (0, 0, 120)         # darker red for secondary elements
SCAN_LINE_ALPHA = 0.08            # scan line opacity (0.0–1.0)
SCAN_LINE_SPEED = 3               # pixels per frame the line descends
WINDOW_TITLE = "CREEPER v1.0"

# Assets
ASSET_DIR = "assets"
```

No test needed — pure constants.

---

## Phase 3 — `detector.py`

**Goal:** Thread-safe NudeNet wrapper that classifies results into the 3 buckets.

**Implementation details:**

1. `DetectionResult` dataclass: `faces: list[dict]`, `belly: list[dict]`, `sensitive: list[dict]`
2. `Detector` class:
   - `__init__`: instantiates `NudeDetector`, creates a `threading.Lock`
   - `analyze_frame(frame: np.ndarray) -> DetectionResult`: saves frame to `tempfile`, calls `detector.detect(path, min_score=MIN_DETECTION_SCORE)`, classifies results, deletes temp file, returns result
   - `classify(detections: list) -> DetectionResult`: pure function, maps class strings to buckets per the class map above
3. Background thread management lives in `main.py` — this module is stateless and thread-safe by virtue of the lock around detect calls.

**✅ Checkpoint (`tests/test_detector.py`):**
- Mock NudeNet output with known classes → assert correct bucket assignment for all 3 categories
- Assert ignored classes produce no output
- Assert empty detection list returns empty `DetectionResult`

---

## Phase 4 — `audio.py`

**Goal:** Non-blocking MP3 playback with per-event cooldown and priority.

**Implementation details:**

1. `AudioManager` class:
   - `__init__`: `pygame.mixer.init()`, loads all 4 MP3s as `pygame.mixer.Sound` objects, plays `startup.mp3` immediately
   - `trigger(event: str)`: events are `"HUMAN_DETECTED"`, `"TARGET_ACQUIRED"`, `"ALERT"`
   - Per-event `last_played` timestamp dict — skip trigger if `time.time() - last_played[event] < AUDIO_COOLDOWN_SECONDS`
   - Priority order: `ALERT` (3) > `TARGET_ACQUIRED` (2) > `HUMAN_DETECTED` (1). A higher-priority event stops current playback before playing. Lower-priority events don't interrupt.
   - `stop_all()`: for clean shutdown

**✅ Checkpoint (`tests/test_audio.py`):**
- Mock `pygame.mixer` — assert `trigger("HUMAN_DETECTED")` called twice rapidly only plays once
- Assert cooldown resets after `AUDIO_COOLDOWN_SECONDS`
- Assert `ALERT` interrupts `HUMAN_DETECTED` but not vice versa

---

## Phase 5 — `pixelate.py`

**Goal:** In-place pixelation of a bounding box region on a frame.

**Implementation details:**

1. `pixelate_region(frame: np.ndarray, box: list[int], block_size: int = PIXELATE_BLOCK_SIZE) -> None`
   - `box` is `[x, y, w, h]` (NudeNet format)
   - Clamp box to frame bounds to prevent index errors
   - Extract ROI → resize down by `block_size` factor → resize back up with `INTER_NEAREST` → write back
   - Mutates frame in-place, returns nothing

**✅ Checkpoint (`tests/test_pixelate.py`):**
- Create a solid-color test frame, apply pixelation to a known box
- Assert pixels inside box changed (blocky), pixels outside box unchanged
- Assert no crash when box is partially out of frame bounds

---

## Phase 6 — `overlay.py`

**Goal:** All HUD drawing logic. Pure functions — take a frame + state, draw on it, return nothing.

**`DetectionState` dataclass:**

```python
@dataclass
class DetectionState:
    human_present: bool = False
    belly_boxes: list = field(default_factory=list)
    sensitive_boxes: list = field(default_factory=list)
    status_text: str = "SCANNING..."
```

**Functions to implement:**

| Function | What it draws |
|---|---|
| `draw_corner_brackets(frame)` | Red L-shaped brackets in all 4 corners |
| `draw_timestamp(frame)` | Top-left: current time in red monospace |
| `draw_scrolling_hex(frame, tick)` | Top-right block of random-updating hex values; `tick` controls refresh rate |
| `draw_status_bar(frame, state)` | Bottom-left status text; color: gray=scanning, green=human, yellow=target, red=alert |
| `draw_scan_line(frame, position)` | Semi-transparent horizontal band at `position` y-coord; caller increments position each frame |
| `draw_belly_target(frame, box, tick)` | Animated red rectangle with corner brackets + center crosshair; `tick` drives subtle bracket pulse animation |
| `draw_sensitive_box(frame, box)` | Thin red border around already-pixelated region |
| `draw_hud(frame, state, tick, scan_y)` | Master function — calls all of the above in correct order |

**Scan line implementation:** Use `cv2.addWeighted` to blend a bright horizontal stripe onto the frame at `scan_y`. Wrap `scan_y` back to 0 when it reaches frame height.

**✅ Checkpoint:** Render `draw_hud` onto a black 640×480 frame with a mock state containing one belly box and one sensitive box. Save to `test_hud_output.jpg`. Visually verify all elements present and correctly positioned.

---

## Phase 7 — `main.py`

**Goal:** Tie everything together. The main loop.

**Structure:**

```
init()
  → AudioManager()        # plays startup sound
  → Detector()
  → cv2.VideoCapture(0)
  → DetectionState()

loop:
  frame ← cap.read()
  frame_count += 1

  if frame_count % SNAPSHOT_INTERVAL_FRAMES == 0:
    submit frame to detector thread (non-blocking)

  if detector thread has new result:
    update DetectionState
    fire audio triggers based on state transitions (edge-triggered, not level-triggered)

  apply pixelate_region() for each sensitive_box
  draw_hud(frame, state, tick, scan_y)
  scan_y = (scan_y + SCAN_LINE_SPEED) % frame_height
  tick += 1

  cv2.imshow(WINDOW_TITLE, frame)
  if cv2.waitKey(1) == ord('q'): break

cleanup:
  cap.release()
  cv2.destroyAllWindows()
  audio.stop_all()
```

**Edge-triggered audio:** Audio fires on *state transitions*, not every frame:
- `human_present` flips `False → True` → trigger `HUMAN_DETECTED`
- `belly_visible` flips `False → True` → trigger `TARGET_ACQUIRED`
- `sensitive_visible` flips `False → True` → trigger `ALERT`

**Threading pattern:** Use `concurrent.futures.ThreadPoolExecutor(max_workers=1)`. Submit detection job; check `future.done()` each frame; collect result if ready.

**✅ Checkpoint (`tests/test_integration.py`):**
- Load a static JPEG, run it through the full pipeline (detector → overlay → pixelate) without webcam
- Assert output frame has been modified (HUD drawn)
- Assert no exceptions thrown
- Assert runtime for one frame < 500ms

---

## Phase 8 — End-to-End Manual Test Protocol

Run through this checklist with the app live before calling it done:

| # | Test | Expected |
|---|---|---|
| 1 | Launch app | Startup MP3 plays, HUD appears, `SCANNING...` status |
| 2 | Enter frame (show face) | `HUMAN DETECTED` status, `human_detected.mp3` plays |
| 3 | Leave frame, re-enter | Audio re-triggers after cooldown |
| 4 | Lift shirt to expose stomach | Red targeting box appears, `target_acquired.mp3` plays |
| 5 | Remove stomach exposure | Box disappears |
| 6 | Re-expose stomach immediately | No audio re-trigger (cooldown active) |
| 7 | Wait cooldown, re-expose | Audio plays again |
| 8 | Trigger alert class (if testable) | Pixelation appears, `alert.mp3` plays |
| 9 | Press `q` | App exits cleanly, no crash |
| 10 | Run 5 minutes continuous | No memory growth, stable frame rate |

---

## Phase 9 — Tuning Pass

After manual testing:

- If **false positives** on belly: raise `MIN_DETECTION_SCORE` toward 0.55–0.65
- If **misses too frequent**: lower toward 0.35
- If **detection feels laggy**: lower `SNAPSHOT_INTERVAL_FRAMES` to 10
- If **CPU is pegged**: raise `SNAPSHOT_INTERVAL_FRAMES` to 20–30
- **Swap in your real MP3 files** — no code changes required, just drop them in `assets/`

---

## Phase 10 — `run.sh` + `README.md`

**`run.sh`:**
```bash
#!/bin/bash
source .venv/bin/activate
python main.py
```

**`README.md` covers:**
- One-time setup steps (Phase 1)
- How to swap in real MP3 files
- Config tuning reference
- How to run (`./run.sh`)
- Key shortcuts (`q` to quit)

---

## Dependency Summary

**`requirements.txt`:**
```
nudenet>=3.4.2
opencv-python>=4.9.0
pygame>=2.5.0
numpy>=1.26.0
```

---

## Quick Reference — Audio Event Logic

| Event | Trigger condition | Priority | Interrupts lower? |
|---|---|---|---|
| `HUMAN_DETECTED` | Face class appears in frame (edge) | 1 (lowest) | No |
| `TARGET_ACQUIRED` | `BELLY_EXPOSED` appears in frame (edge) | 2 | No |
| `ALERT` | Any sensitive class appears in frame (edge) | 3 (highest) | Yes |

All events subject to `AUDIO_COOLDOWN_SECONDS` (default 3.0s) per event independently.

---

## Quick Reference — HUD Status Colors

| State | Status Text | Color |
|---|---|---|
| No detection | `SCANNING...` | Gray |
| Face detected | `HUMAN DETECTED` | Green |
| Belly detected | `TARGET ACQUIRED` | Yellow |
| Sensitive content | `⚠ ALERT` | Red |
