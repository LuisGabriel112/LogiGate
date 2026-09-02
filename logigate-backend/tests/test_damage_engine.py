import numpy as np

from conftest import FakeResult
from damage_engine import (
    DAMAGE_INFER_SIZE,
    DamageDetectionEngine,
    resolve_damage_model,
)


def make_image(h, w):
    return np.full((h, w, 3), 200, dtype=np.uint8)


class FakeYoloModel:
    def __init__(self, results):
        self._results = results
        self.names = {0: "scratch"}
        self.calls = []

    def __call__(self, image, **kwargs):
        self.calls.append(kwargs)
        return self._results


def make_engine(results=None):
    return DamageDetectionEngine(model_path="unused.pt", yolo_model=FakeYoloModel(results or []))


def test_preprocess_resizes_larger_side_to_damage_infer_size():
    engine = make_engine()
    img = make_image(h=800, w=1200)

    out = engine.preprocess(img)

    assert max(out.shape[:2]) == DAMAGE_INFER_SIZE


def test_preprocess_does_not_upscale_smaller_images():
    engine = make_engine()
    img = make_image(h=100, w=150)

    out = engine.preprocess(img)

    assert out.shape[:2] == (100, 150)


def test_analyze_calls_model_with_damage_infer_size():
    fake_yolo = FakeYoloModel(results=[FakeResult(boxes=[])])
    engine = DamageDetectionEngine(model_path="unused.pt", yolo_model=fake_yolo)
    img = make_image(h=DAMAGE_INFER_SIZE, w=DAMAGE_INFER_SIZE)

    engine.analyze(img)

    assert fake_yolo.calls[0]["imgsz"] == DAMAGE_INFER_SIZE


def test_resolve_damage_model_prefers_openvino_dir_when_present(tmp_path):
    pt_path = tmp_path / "best.pt"
    pt_path.write_bytes(b"fake")
    openvino_dir = tmp_path / "best_openvino_model"
    openvino_dir.mkdir()

    resolved = resolve_damage_model(str(pt_path))

    assert resolved == str(openvino_dir)


def test_resolve_damage_model_falls_back_to_pt_when_no_openvino_dir(tmp_path):
    pt_path = tmp_path / "best.pt"
    pt_path.write_bytes(b"fake")

    resolved = resolve_damage_model(str(pt_path))

    assert resolved == str(pt_path)
