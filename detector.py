import threading
import tempfile
import os
from dataclasses import dataclass, field
from typing import List, Dict

import cv2
import numpy as np
from nudenet import NudeDetector

import config


@dataclass
class DetectionResult:
    faces: List[Dict] = field(default_factory=list)
    belly: List[Dict] = field(default_factory=list)
    sensitive: List[Dict] = field(default_factory=list)


FACE_CLASSES = {"FACE_FEMALE", "FACE_MALE"}
BELLY_CLASSES = {"BELLY_EXPOSED"}
SENSITIVE_CLASSES = {
    "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "MALE_BREAST_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
}


def classify(detections: List[Dict]) -> DetectionResult:
    result = DetectionResult()
    for det in detections:
        class_name = det.get("class")
        if class_name in FACE_CLASSES:
            result.faces.append(det)
        elif class_name in BELLY_CLASSES:
            result.belly.append(det)
        elif class_name in SENSITIVE_CLASSES:
            result.sensitive.append(det)
    return result


class Detector:
    def __init__(self):
        self._detector = NudeDetector()
        self._lock = threading.Lock()

    def analyze_frame(self, frame: np.ndarray):
        with self._lock:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                cv2.imwrite(tmp_path, frame)
                detections = self._detector.detect(tmp_path)
                raw_classes = [d.get("class") for d in detections]
                filtered = [
                    d
                    for d in detections
                    if d.get("score", 0) >= config.MIN_DETECTION_SCORE
                ]
                return classify(filtered), raw_classes
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
