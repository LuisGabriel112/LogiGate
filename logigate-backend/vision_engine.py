import cv2
import re
import os
import numpy as np
import easyocr
from ultralytics import YOLO

class LicensePlateEngine:
    def __init__(self, model_path="logigate_v4.pt"):
        """
        Motor LogiGate v9.0 - Geometric AI (Restaurado)
        Usa la 'Regla de Oro' para ignorar marcos y letreros mediante coordenadas.
        """
        print(f"--- Cargando YOLOv11: {model_path} ---")
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"Error YOLO: {e}")
            self.model = None
        
        print("--- Inicializando EasyOCR (Modo Geométrico) ---")
        self.reader = easyocr.Reader(['en'], gpu=False) 

    def process_image(self, image):
        if image is None or self.model is None:
            return []
        
        # Umbral bajo para capturar todas las placas posibles
        results = self.model(image, conf=0.10, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                conf_yolo = box.conf[0].item()
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                
                # Recorte quirúrgico
                h_img, w_img = image.shape[:2]
                px1, py1 = max(0, x1-5), max(0, y1-5)
                px2, py2 = min(w_img, x2+5), min(h_img, y2+5)
                plate_crop = image[py1:py2, px1:px2]
                
                if plate_crop.size == 0: continue

                try:
                    # detail=1 nos da las coordenadas de cada bloque de texto
                    ocr_results = self.reader.readtext(plate_crop, detail=1)
                    
                    final_plate = ""
                    h_crop = plate_crop.shape[0]
                    centro_y_crop = h_crop / 2
                    
                    # Ordenar bloques de izquierda a derecha
                    ocr_results = sorted(ocr_results, key=lambda x: x[0][0][0])

                    for (bbox, text, prob) in ocr_results:
                        # REGLA DE ORO: Solo texto en el centro vertical del recorte
                        # Esto ignora letreros de "Díaz Mirón" o "Transporte" arriba/abajo
                        y_texto_centro = (bbox[0][1] + bbox[2][1]) / 2 
                        distancia_al_centro = abs(y_texto_centro - centro_y_crop)
                        
                        # Si el texto está muy lejos del centro vertical, lo ignoramos
                        if distancia_al_centro < (h_crop * 0.25):
                            clean_block = "".join(re.findall(r'[A-Z0-9]', text.upper()))
                            
                            # Filtro de palabras de entorno (opcional pero ayuda)
                            for noise in ["MEXICO", "VERACRUZ", "ESTADO", "TRANSPORTE", "PRIVADO", "PUEBLA"]:
                                clean_block = clean_block.replace(noise, "")
                                
                            final_plate += clean_block

                    if len(final_plate) >= 4:
                        # Formateo visual
                        if len(final_plate) >= 6 and "-" not in final_plate:
                            final_plate = f"{final_plate[:3]}-{final_plate[3:]}"

                        detections.append({
                            "plate": final_plate,
                            "confidence": conf_yolo,
                            "box": [x1, y1, x2, y2],
                            "crop": plate_crop
                        })
                except Exception as e:
                    print(f"Error OCR: {e}")

        # Ordenar por confianza
        return sorted(detections, key=lambda x: x["confidence"], reverse=True)
