import cv2
import numpy as np
from ultralytics import YOLO

CLASS_NAMES_ES = {
    "dents":     "abolladuras",
    "scratches": "rayones",
}

SEVERITY_COLORS_BGR = {
    "sin_danos": (74, 222, 128),   # green
    "leve":      (50, 205, 234),   # yellow
    "moderado":  (37, 115, 249),   # orange
    "grave":     (68,  68, 239),   # red
}

SEVERIDAD_LABELS = {
    "sin_danos": "Sin Daños",
    "leve":      "Daño Leve",
    "moderado":  "Daño Moderado",
    "grave":     "Daño Grave",
}


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

    def analyze(self, img: np.ndarray) -> dict:
        if img is None or self.model is None:
            return {"danos_detectados": 0, "severidad": "error", "detecciones": [], "damage_ratio": 0.0}

        results = self.model(img, conf=0.25, iou=0.45, verbose=False)
        detecciones = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                raw = self.class_names.get(cls, f"damage_{cls}")
                label = CLASS_NAMES_ES.get(raw, raw)
                area = (x2 - x1) * (y2 - y1)
                detecciones.append({
                    "tipo": label,
                    "confianza": round(conf, 3),
                    "bbox": [x1, y1, x2, y2],
                    "area": area,
                })

        img_area = (img.shape[0] * img.shape[1]) or 1
        total_damage_area = sum(d["area"] for d in detecciones)
        damage_ratio = total_damage_area / img_area

        if not detecciones:
            severidad = "sin_danos"
        elif damage_ratio > 0.25 or len(detecciones) >= 4:
            severidad = "grave"
        elif damage_ratio > 0.08 or len(detecciones) >= 2:
            severidad = "moderado"
        else:
            severidad = "leve"

        return {
            "danos_detectados": len(detecciones),
            "severidad": severidad,
            "detecciones": detecciones,
            "damage_ratio": round(damage_ratio * 100, 1),
        }

    def annotate(self, img: np.ndarray, analysis: dict) -> np.ndarray:
        annotated = img.copy()
        severidad = analysis.get("severidad", "sin_danos")
        color = SEVERITY_COLORS_BGR.get(severidad, (255, 255, 255))

        for det in analysis.get("detecciones", []):
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confianza"]
            label = f"{det['tipo']} {conf:.0%}"

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 8, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 4, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 1, cv2.LINE_AA)

        label_sev = SEVERIDAD_LABELS.get(severidad, severidad)
        cv2.putText(annotated, label_sev, (12, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

        return annotated
