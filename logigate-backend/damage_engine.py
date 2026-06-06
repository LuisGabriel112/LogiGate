import cv2
import numpy as np
from ultralytics import YOLO

CLASS_NAMES_ES = {
    "car-part-crack":      "grieta en carrocería",
    "flat-tire":           "llanta ponchada",
    "glass-crack":         "vidrio roto",
    "lamp-broken":         "faro roto",
    "minor-deformation":   "deformación leve",
    "moderate-deformation":"deformación moderada",
    "scratch":             "rayón",
    "severe-deformation":  "deformación severa",
    "side-mirror-crack":   "espejo roto",
}

DAMAGE_TYPE_WEIGHT = {
    "grieta en carrocería": 1.6,
    "llanta ponchada":      2.0,
    "vidrio roto":          1.8,
    "faro roto":            1.4,
    "deformación leve":     1.1,
    "deformación moderada": 1.5,
    "rayón":                1.0,
    "deformación severa":   2.0,
    "espejo roto":          1.3,
}

SEVERITY_COLORS_BGR = {
    "sin_danos": (74, 222, 128),
    "leve":      (50, 205, 234),
    "moderado":  (37, 115, 249),
    "grave":     (68,  68, 239),
}

SEVERIDAD_LABELS = {
    "sin_danos": "Sin Daños",
    "leve":      "Daño Leve",
    "moderado":  "Daño Moderado",
    "grave":     "Daño Grave",
}

BLUR_THRESHOLD  = 50    # varianza Laplacian mínima
DARK_THRESHOLD  = 30    # brillo promedio mínimo (0-255)
CLAHE_THRESHOLD = 80    # por debajo de esto se aplica CLAHE


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class DamageDetectionEngine:
    def __init__(self, model_path: str):
        print(f"--- Cargando motor de daños: {model_path} ---")
        try:
            self.model = YOLO(model_path)
            self.class_names = self.model.names
            print(f"--- Clases detectables: {list(self.class_names.values())} ---")
        except Exception as e:
            print(f"Error cargando modelo de daños: {e}")
            self.model = None
            self.class_names = {}

    def validate(self, img: np.ndarray) -> None:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if lap_var < BLUR_THRESHOLD:
            raise ImageValidationError(
                "imagen_borrosa",
                f"Imagen demasiado borrosa (nitidez: {lap_var:.0f}). Tome la foto con mejor enfoque.",
            )

        brightness = gray.mean()
        if brightness < DARK_THRESHOLD:
            raise ImageValidationError(
                "imagen_oscura",
                f"Imagen demasiado oscura (brillo: {brightness:.0f}). Mejore la iluminación.",
            )

    def preprocess(self, img: np.ndarray) -> np.ndarray:
        # Resize al tamaño nativo del modelo (640) sin distorsión
        h, w = img.shape[:2]
        scale = 640 / max(h, w)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        # CLAHE solo si la imagen es oscura
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if gray.mean() < CLAHE_THRESHOLD:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

        return img

    def analyze(self, img: np.ndarray) -> dict:
        if img is None or self.model is None:
            return {
                "danos_detectados": 0, "severidad": "error",
                "detecciones": [], "damage_ratio": 0.0, "confianza_promedio": 0.0,
            }

        results = self.model(img, conf=0.35, iou=0.45, verbose=False)
        img_area = float(img.shape[0] * img.shape[1]) or 1.0
        detecciones = []

        for r in results:
            masks_data = r.masks
            for i, box in enumerate(r.boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf  = float(box.conf[0])
                cls   = int(box.cls[0])
                raw   = self.class_names.get(cls, f"damage_{cls}")
                label = CLASS_NAMES_ES.get(raw, raw)

                mask_contour = None
                if masks_data is not None and i < len(masks_data.xy):
                    contour = np.array(masks_data.xy[i])
                    if len(contour) >= 3:
                        area = float(cv2.contourArea(contour.astype(np.float32)))
                        mask_contour = contour.tolist()
                    else:
                        area = float((x2 - x1) * (y2 - y1))
                else:
                    area = float((x2 - x1) * (y2 - y1))

                detecciones.append({
                    "tipo":         label,
                    "confianza":    round(conf, 3),
                    "bbox":         [x1, y1, x2, y2],
                    "area":         area,
                    "mask_contour": mask_contour,
                })

        def weighted_score(d):
            type_w = DAMAGE_TYPE_WEIGHT.get(d["tipo"], 1.0)
            return (d["area"] / img_area) * d["confianza"] * type_w

        total_weighted = sum(weighted_score(d) for d in detecciones)
        damage_ratio   = sum(d["area"] for d in detecciones) / img_area
        avg_conf       = (sum(d["confianza"] for d in detecciones) / len(detecciones)) if detecciones else 0.0

        if not detecciones:
            severidad = "sin_danos"
        elif total_weighted > 0.20 or (avg_conf > 0.70 and damage_ratio > 0.15):
            severidad = "grave"
        elif total_weighted > 0.06 or (damage_ratio > 0.05 and avg_conf > 0.50):
            severidad = "moderado"
        else:
            severidad = "leve"

        return {
            "danos_detectados":   len(detecciones),
            "severidad":          severidad,
            "detecciones":        detecciones,
            "damage_ratio":       round(damage_ratio * 100, 1),
            "confianza_promedio": round(avg_conf * 100, 1),
        }

    def annotate(self, img: np.ndarray, analysis: dict) -> np.ndarray:
        annotated = img.copy()
        overlay   = annotated.copy()
        severidad = analysis.get("severidad", "sin_danos")
        color     = SEVERITY_COLORS_BGR.get(severidad, (255, 255, 255))

        # 1. Rellenar máscaras semitransparentes
        for det in analysis.get("detecciones", []):
            contour = det.get("mask_contour")
            if contour is not None and len(contour) >= 3:
                pts = np.array(contour, dtype=np.int32).reshape((-1, 1, 2))
                cv2.fillPoly(overlay, [pts], color)

        cv2.addWeighted(overlay, 0.35, annotated, 0.65, 0, annotated)

        # 2. Contornos + etiquetas encima del blend
        for det in analysis.get("detecciones", []):
            x1, y1, x2, y2 = det["bbox"]
            conf    = det["confianza"]
            label   = f"{det['tipo']} {conf:.0%}"
            contour = det.get("mask_contour")

            if contour is not None and len(contour) >= 3:
                pts = np.array(contour, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated, [pts], True, color, 2)
            else:
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 8, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 4, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 1, cv2.LINE_AA)

        label_sev = SEVERIDAD_LABELS.get(severidad, severidad)
        cv2.putText(annotated, label_sev, (12, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

        return annotated
