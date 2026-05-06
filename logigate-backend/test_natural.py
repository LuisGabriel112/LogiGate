import os
import cv2
import sys

# Añadir el path del backend para importar LicensePlateEngine
sys.path.append(r'C:\Users\USER\Desktop\LOGIGATE\LogiGate\logigate-backend')

from vision_engine import LicensePlateEngine

def natural_test():
    img_dir = r'C:\Users\USER\Desktop\imagenesautos'
    model_path = r'C:\Users\USER\Desktop\LOGIGATE\LogiGate\logigate-backend\logigate_v4.pt'
    
    engine = LicensePlateEngine(model_path=model_path)
    
    target_files = ['auto001.jpg', 'placaauto1.jpg', 'placaauto2.jpg', 'placasauto3.jpg', 'placasauto4.png']
    
    print("\n--- TEST IA NATURAL (SIN TRUCOS) ---")
    
    for filename in target_files:
        filepath = os.path.join(img_dir, filename)
        if not os.path.exists(filepath): continue
        img = cv2.imread(filepath)
        if img is None: continue
            
        detections = engine.process_image(img)
        
        if not detections:
            print(f"[{filename}] -> NADA DETECTADO")
        else:
            print(f"[{filename}] -> IA LEYÓ: {detections[0]['plate']} (Conf: {detections[0]['confidence']:.2f})")

if __name__ == "__main__":
    natural_test()
