import re
import easyocr
from ultralytics import YOLO

PLATE_CONF_THRESHOLD = 0.30
CENTER_BAND_RATIO = 0.25
MIN_BLOCK_HEIGHT_RATIO = 0.5
CROP_PADDING = 5
MIN_PLATE_LENGTH = 4
NOISE_WORDS = ["MEXICO", "VERACRUZ", "ESTADO", "TRANSPORTE", "PRIVADO", "PUEBLA"]


def clean_ocr_block(text: str) -> str:
    clean = "".join(re.findall(r'[A-Z0-9]', text.upper()))
    for noise in NOISE_WORDS:
        clean = clean.replace(noise, "")
    return clean


def _block_height(bbox):
    return bbox[2][1] - bbox[0][1]


def _discard_short_blocks(blocks):
    if not blocks:
        return []
    max_height = max(_block_height(bbox) for bbox, _text in blocks)
    min_height = max_height * MIN_BLOCK_HEIGHT_RATIO
    return [(bbox, text) for bbox, text in blocks if _block_height(bbox) >= min_height]


def filter_centered_blocks(ocr_results, crop_height):
    centro_y_crop = crop_height / 2
    band = crop_height * CENTER_BAND_RATIO
    ordered = sorted(ocr_results, key=lambda r: r[0][0][0])
    centered = [
        (bbox, text) for bbox, text, _prob in ordered
        if abs((bbox[0][1] + bbox[2][1]) / 2 - centro_y_crop) < band
    ]
    return _discard_short_blocks(centered)


def format_plate(plate_text: str) -> str:
    if len(plate_text) >= 6 and "-" not in plate_text:
        return f"{plate_text[:3]}-{plate_text[3:]}"
    return plate_text


def crop_plate_region(image, box, padding=CROP_PADDING):
    x1, y1, x2, y2 = box["xyxy"]
    h_img, w_img = image.shape[:2]
    px1, py1 = max(0, x1 - padding), max(0, y1 - padding)
    px2, py2 = min(w_img, x2 + padding), min(h_img, y2 + padding)
    return image[py1:py2, px1:px2]


class LicensePlateEngine:
    """
    Motor LogiGate v10.0 - Geometric AI
    Usa la 'Regla de Oro' para ignorar marcos y letreros mediante coordenadas.
    Solo hace OCR sobre la caja de mayor confianza detectada por YOLO.
    """

    def __init__(self, model_path="logigate_v4.pt", yolo_model=None, ocr_reader=None):
        self.model = yolo_model if yolo_model is not None else self._load_yolo(model_path)
        self.reader = ocr_reader if ocr_reader is not None else easyocr.Reader(['en'], gpu=False)

    def _load_yolo(self, model_path):
        print(f"--- Cargando YOLOv11: {model_path} ---")
        try:
            return YOLO(model_path)
        except Exception as e:
            print(f"Error YOLO: {e}")
            return None

    def process_image(self, image):
        if image is None or self.model is None:
            return []
        boxes = self._detect_boxes(image)
        if not boxes:
            return []
        best_box = max(boxes, key=lambda b: b["confidence"])
        crop = crop_plate_region(image, best_box)
        if crop is None or crop.size == 0:
            return []
        plate_text = self._read_plate_text(crop)
        if len(plate_text) < MIN_PLATE_LENGTH:
            return []
        return [{
            "plate": format_plate(plate_text),
            "confidence": best_box["confidence"],
            "box": best_box["xyxy"],
            "crop": crop,
        }]

    def _detect_boxes(self, image):
        results = self.model(image, conf=PLATE_CONF_THRESHOLD, verbose=False)
        boxes = []
        for result in results:
            for box in result.boxes:
                boxes.append({
                    "confidence": box.conf[0].item(),
                    "xyxy": list(map(int, box.xyxy[0].tolist())),
                })
        return boxes

    def _read_plate_text(self, crop):
        try:
            ocr_results = self.reader.readtext(crop, detail=1)
        except Exception as e:
            print(f"Error OCR: {e}")
            return ""
        centered_blocks = filter_centered_blocks(ocr_results, crop.shape[0])
        return "".join(clean_ocr_block(text) for _, text in centered_blocks)
