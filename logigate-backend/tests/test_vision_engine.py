import numpy as np

from conftest import FakeBox, FakeResult
from vision_engine import (
    LicensePlateEngine,
    PLATE_CONF_THRESHOLD,
    clean_ocr_block,
    crop_plate_region,
    filter_centered_blocks,
    format_plate,
)


def make_image(h=10, w=100):
    return np.zeros((h, w, 3), dtype=np.uint8)


class FakeYoloModel:
    def __init__(self, boxes):
        self._boxes = boxes
        self.calls = []

    def __call__(self, image, conf=0.0, verbose=False):
        self.calls.append(conf)
        kept = [b for b in self._boxes if b.conf[0].item() >= conf]
        return [FakeResult(kept)]


class FakeReader:
    def __init__(self, ocr_results):
        self.calls = []
        self._ocr_results = ocr_results

    def readtext(self, crop, detail=1):
        self.calls.append(crop)
        return self._ocr_results


def make_engine(boxes, ocr_results):
    return LicensePlateEngine(
        model_path="unused.pt",
        yolo_model=FakeYoloModel(boxes),
        ocr_reader=FakeReader(ocr_results),
    )


def test_process_image_uses_plate_conf_threshold():
    yolo = FakeYoloModel(boxes=[])
    engine = LicensePlateEngine(model_path="x", yolo_model=yolo, ocr_reader=FakeReader([]))

    engine.process_image(make_image())

    assert yolo.calls == [PLATE_CONF_THRESHOLD]


def test_process_image_returns_empty_when_no_boxes_detected():
    engine = make_engine(boxes=[], ocr_results=[])

    result = engine.process_image(make_image())

    assert result == []


def test_process_image_calls_ocr_only_once_with_multiple_boxes():
    boxes = [
        FakeBox(0.31, [0, 0, 20, 10]),
        FakeBox(0.90, [30, 0, 60, 10]),
        FakeBox(0.40, [70, 0, 90, 10]),
    ]
    ocr_results = [([[0, 0], [10, 0], [10, 10], [0, 10]], "ABC1234", 0.9)]
    fake_yolo = FakeYoloModel(boxes)
    fake_reader = FakeReader(ocr_results)
    engine = LicensePlateEngine(model_path="x", yolo_model=fake_yolo, ocr_reader=fake_reader)

    result = engine.process_image(make_image())

    assert len(fake_reader.calls) == 1
    assert result[0]["confidence"] == 0.90


def test_process_image_selects_highest_confidence_box_for_ocr():
    boxes = [FakeBox(0.35, [0, 0, 10, 10]), FakeBox(0.95, [50, 0, 70, 10])]
    fake_reader = FakeReader(ocr_results=[])
    engine = LicensePlateEngine(
        model_path="x", yolo_model=FakeYoloModel(boxes), ocr_reader=fake_reader
    )

    engine.process_image(make_image())

    used_crop = fake_reader.calls[0]
    assert used_crop.shape[1] <= 30


def test_process_image_discards_plate_shorter_than_minimum_length():
    boxes = [FakeBox(0.5, [0, 0, 20, 10])]
    ocr_results = [([[0, 0], [5, 0], [5, 10], [0, 10]], "AB", 0.9)]
    engine = make_engine(boxes, ocr_results)

    result = engine.process_image(make_image())

    assert result == []


def test_format_plate_adds_dash_for_six_or_more_chars():
    assert format_plate("ABC1234") == "ABC-1234"


def test_format_plate_keeps_short_plate_unchanged():
    assert format_plate("AB12") == "AB12"


def test_format_plate_keeps_existing_dash():
    assert format_plate("ABC-1234") == "ABC-1234"


def test_clean_ocr_block_strips_noise_words_and_symbols():
    assert clean_ocr_block("mexico abc-123!") == "ABC123"


def test_filter_centered_blocks_keeps_only_center_band():
    ocr_results = [
        ([[10, 45], [50, 45], [50, 55], [10, 55]], "CENTRO", 0.9),
        ([[10, 5], [50, 5], [50, 15], [10, 15]], "BORDE", 0.9),
    ]

    kept = filter_centered_blocks(ocr_results, crop_height=100)

    assert [text for _, text in kept] == ["CENTRO"]


def test_filter_centered_blocks_discards_short_caption_near_center():
    ocr_results = [
        ([[10, 30], [60, 30], [60, 70], [10, 70]], "ZBN902E", 0.9),
        ([[10, 60], [90, 60], [90, 75], [10, 75]], "TRANSPORTEPRIVADOAUTOMOVIL", 0.85),
    ]

    kept = filter_centered_blocks(ocr_results, crop_height=100)

    assert [text for _, text in kept] == ["ZBN902E"]


def test_crop_plate_region_applies_padding_and_clamps_to_bounds():
    image = make_image(h=50, w=50)
    box = {"xyxy": [0, 0, 10, 10]}

    crop = crop_plate_region(image, box, padding=5)

    assert crop.shape[:2] == (15, 15)
