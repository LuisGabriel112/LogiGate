from ultralytics import YOLO
import os

# Cargar un modelo base de YOLOv11
model = YOLO('yolo11n.pt')

# Usar barras normales (/) para evitar problemas con YOLO y Windows
data_path = "C:/Users/USER/Desktop/LOGIGATE/LogiGate/logigate-backend/Placasdetect-1/data.yaml"

print(f"Buscando archivo de configuración en: {data_path}")

# Verificar si el archivo existe
if not os.path.exists(data_path):
    print("¡ERROR! El archivo data.yaml no existe en esa ruta.")
else:
    # Entrenar el modelo
    results = model.train(data=data_path, epochs=15, imgsz=640)