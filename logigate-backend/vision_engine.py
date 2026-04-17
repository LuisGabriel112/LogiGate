import cv2
import re
import os
import numpy as np
import easyocr
from ultralytics import YOLO

class LicensePlateEngine:
    def __init__(self, model_path="logigate_v4.pt"):
        """
        Motor LogiGate v4.9 - Edición de Limpieza Agresiva (Restaurado).
        Optimizado con patrones SCT y filtros de caracteres fantasma.
        """
        print(f"--- Cargando YOLOv11: {model_path} ---")
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"Error al cargar YOLO: {e}")
            self.model = YOLO("yolo11n.pt") if os.path.exists("yolo11n.pt") else None
        
        print("--- Inicializando EasyOCR (Filtros Anti-Fantasmas Activados) ---")
        self.reader = easyocr.Reader(['en'], gpu=False) 
        
        self.whitelist_pattern = re.compile(r'[A-Z0-9]')
        self.patron_sct = re.compile(r'[A-Z0-9]{6,8}') 
        self.patrones_borde = ['MGB', 'MGF', 'MGC', 'W', 'M', 'B']

    def process_image(self, image):
        if image is None or self.model is None:
            return []
        
        results = self.model(image, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                conf_yolo = box.conf[0].item()
                
                if conf_yolo > 0.30: 
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    
                    # Recorte con padding de seguridad
                    h_img, w_img = image.shape[:2]
                    px1, py1 = max(0, x1-5), max(0, y1-5)
                    px2, py2 = min(w_img, x2+5), min(h_img, y2+5)
                    plate_crop = image[py1:py2, px1:px2]
                    
                    if plate_crop.size == 0: continue

                    try:
                        # detail=1 para obtener coordenadas y procesar por geometría
                        ocr_results = self.reader.readtext(
                            plate_crop, 
                            detail=1,
                            allowlist='0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'
                        )
                        
                        final_plate = ""
                        max_ocr_prob = 0
                        h_crop = plate_crop.shape[0]
                        centro_y_crop = h_crop / 2
                        
                        # Ordenar bloques de izquierda a derecha
                        ocr_results = sorted(ocr_results, key=lambda x: x[0][0][0])

                        for (bbox, text, prob) in ocr_results:
                            clean_block = "".join(re.findall(self.whitelist_pattern, text.upper()))
                            
                            # REGLA DE ORO: Solo texto en el centro vertical del recorte
                            y_texto_centro = (bbox[0][1] + bbox[2][1]) / 2 
                            distancia_al_centro = abs(y_texto_centro - centro_y_crop)
                            
                            if distancia_al_centro < (h_crop * 0.35):
                                if len(clean_block) >= 1:
                                    final_plate += clean_block
                                    max_ocr_prob = max(max_ocr_prob, prob)

                        # --- PARCHE SCT Y LIMPIEZA AGRESIVA ---
                        # 1. Buscar la sub-cadena que parezca una placa real (6-8 caracteres)
                        match = self.patron_sct.search(final_plate)
                        if match:
                            final_plate = match.group()
                        
                        # 2. Quitar caracteres que EasyOCR inventa por reflejos o guiones
                        # "F" suele ser un guion mal leído, "Q" suele ser un borde de perno
                        final_plate = final_plate.replace('F', '').replace('Q', '')

                        # 3. Quitar patrones de bordes metálicos conocidos
                        for patron in self.patrones_borde:
                            if final_plate.startswith(patron):
                                final_plate = final_plate.replace(patron, "", 1)
                                break

                        # 4. Filtro estándar SCT (Quitar I, O, Ñ)
                        for char in "IOÑ":
                            final_plate = final_plate.replace(char, "")

                        print(f"DEBUG LOGIGATE - Placa Final Procesada: {final_plate} (YOLO: {conf_yolo:.2f})")

                        # Validación de longitud (Aceptamos 4 a 9 por si hay placas antiguas/motos)
                        if 4 <= len(final_plate) <= 9:
                            detections.append({
                                "plate": final_plate,
                                "confidence": conf_yolo,
                                "box": [x1, y1, x2, y2],
                                "crop": plate_crop
                            })
                            
                    except Exception as e:
                        print(f"Error en lectura EasyOCR: {e}")

        return detections
