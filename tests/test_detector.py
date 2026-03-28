import sys

sys.path.insert(0, ".")

from detector import (
    classify,
    DetectionResult,
    FACE_CLASSES,
    BELLY_CLASSES,
    SENSITIVE_CLASSES,
)


def test_classify_face():
    detections = [{"class": "FACE_FEMALE", "score": 0.9, "box": [0, 0, 100, 100]}]
    result = classify(detections)
    assert len(result.faces) == 1
    assert len(result.belly) == 0
    assert len(result.sensitive) == 0


def test_classify_belly():
    detections = [{"class": "BELLY_EXPOSED", "score": 0.8, "box": [0, 0, 100, 100]}]
    result = classify(detections)
    assert len(result.faces) == 0
    assert len(result.belly) == 1
    assert len(result.sensitive) == 0


def test_classify_sensitive():
    detections = [
        {"class": "MALE_GENITALIA_EXPOSED", "score": 0.85, "box": [0, 0, 100, 100]}
    ]
    result = classify(detections)
    assert len(result.faces) == 0
    assert len(result.belly) == 0
    assert len(result.sensitive) == 1


def test_classify_ignored():
    detections = [
        {"class": "ARMPITS_EXPOSED", "score": 0.8, "box": [0, 0, 100, 100]},
        {"class": "FEET_EXPOSED", "score": 0.8, "box": [0, 0, 100, 100]},
        {"class": "BELLY_COVERED", "score": 0.8, "box": [0, 0, 100, 100]},
    ]
    result = classify(detections)
    assert len(result.faces) == 0
    assert len(result.belly) == 0
    assert len(result.sensitive) == 0


def test_classify_empty():
    result = classify([])
    assert isinstance(result, DetectionResult)
    assert len(result.faces) == 0
    assert len(result.belly) == 0
    assert len(result.sensitive) == 0


def test_classify_multiple():
    detections = [
        {"class": "FACE_FEMALE", "score": 0.9, "box": [0, 0, 100, 100]},
        {"class": "BELLY_EXPOSED", "score": 0.8, "box": [10, 10, 50, 50]},
        {"class": "MALE_GENITALIA_EXPOSED", "score": 0.85, "box": [20, 20, 30, 30]},
    ]
    result = classify(detections)
    assert len(result.faces) == 1
    assert len(result.belly) == 1
    assert len(result.sensitive) == 1


if __name__ == "__main__":
    test_classify_face()
    test_classify_belly()
    test_classify_sensitive()
    test_classify_ignored()
    test_classify_empty()
    test_classify_multiple()
    print("All detector tests passed!")
