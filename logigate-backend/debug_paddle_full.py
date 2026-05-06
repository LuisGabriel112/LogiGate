import os
# --- PARCHES DE ESTABILIDAD ---
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_mkldnn'] = '0'
os.environ['FLAGS_on_ednn'] = '0'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import cv2
import sys
from ultralytics import YOLO
from paddleocr import PaddleOCR

def debug_detection():
    img_dir = r'C:\Users\USER\Desktop\imagenesautos'
    model_path = r'C:\Users\USER\Desktop\LOGIGATE\LogiGate\logigate-backend\logigate_v4.pt'
    
    print("--- Cargando YOLO ---")
    model = YOLO(model_path)
    
    print("--- Cargando PaddleOCR ---")
    try:
        ocr = PaddleOCR(lang='en')
    except Exception as e:
        print(f"Error al cargar PaddleOCR: {e}")
        return

    target_files = ['auto001.jpg', 'placaauto1.jpg', 'placaauto2.jpg', 'placasauto3.jpg', 'placasauto4.png']
    
    for filename in target_files:
        filepath = os.path.join(img_dir, filename)
        if not os.path.exists(filepath): continue
        
        img = cv2.imread(filepath)
        if img is None: continue
        
        print(f"\n[{filename}]")
        results = model(img, conf=0.01, verbose=False) # Umbral muy bajo para ver todo
        
        found = False
        for result in results:
            for box in result.boxes:
                conf = box.conf[0].item()
                print(f"  - YOLO Det: {conf:.4f}")
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                crop = img[y1:y2, x1:x2]
                if crop.size > 0:
                    try:
                        ocr_res = ocr.ocr(crop)
                        print(f"    - PaddleOCR: {ocr_res}")
                    except Exception as e:
                        print(f"    - Error PaddleOCR: {e}")
                found = True
        
        if not found:
            print("  - YOLO no detectó nada")

if __name__ == "__main__":
    debug_detection()
