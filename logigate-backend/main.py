from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import numpy as np
import cv2
import os
import easyocr
from ultralytics import YOLO
import shutil
from datetime import datetime

# --- CONFIGURACIÓN ---
UPLOAD_DIR = os.path.join("static", "plates")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Estructura para las respuestas
class ScanResponse(BaseModel):
    plate: str
    confidence: float
    image_url: str
    status: str

models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Cargando modelo YOLO y OCR...")
    try:
        # Cargamos el modelo (asegurate que el archivo .pt esté en la carpeta)
        models["yolo"] = YOLO("yolo11n.pt") 
    except Exception as e:
        print(f"Error cargando YOLO: {e}")
        models["yolo"] = YOLO("yolo11n.pt")
        
    models["reader"] = easyocr.Reader(['es']) 
    yield
    models.clear()
    print("Limpiando recursos...")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "LogiGate API", "IA_Status": "Ready" if "yolo" in models else "Off"}

# --- HISTORIAL ---
@app.get("/api/v1/history")
async def get_history(db: Session = Depends(get_db)):
    try:
        # Query ajustada a tus nombres reales de columnas en pgAdmin
        query = text("""
            SELECT 
                ra."Id_Acceso", 
                ra."Vehiculo_Placa", 
                ra."Fecha_Entrada", 
                ra."Foto_Placa",
                v."Marca", 
                v."Modelo", 
                u."Nombre(s)", 
                u."Apellido_Paterno"
            FROM public."Registros_Accesos" ra
            LEFT JOIN public."Vehiculos" v ON ra."Vehiculo_Placa" = v."Vehiculo_Placa"
            LEFT JOIN public."Usuarios" u ON v."Id_Propietario" = u."Id_Propietario"
            ORDER BY ra."Fecha_Entrada" DESC
        """)
        
        result = db.execute(query)
        
        history = []
        for row in result:
            history.append({
                "id_acceso": row[0],
                "placa": row[1],
                "fecha": row[2].strftime("%Y-%m-%d %H:%M:%S") if row[2] else None,
                "foto_url": f"http://localhost:8000/static/plates/{row[3]}" if row[3] else None,
                "marca": row[4] or "Desconocido",
                "modelo": row[5] or "Desconocido",
                "propietario": f"{row[6]} {row[7]}" if row[6] else "Visitante/Nuevo"
            })
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en historial: {str(e)}")

# --- ESCANEO Y AUTO-REGISTRO ---
@app.post("/api/v1/scan", response_model=ScanResponse)
async def create_scan(image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # 1. Guardar archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # 2. Procesar con IA
        img = cv2.imread(filepath)
        results = models["yolo"](img, conf=0.20)[0]
        detected_plate = "NO_DETECTADA"
        max_conf = 0.0

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = img[y1:y2, x1:x2]
            
            ocr_result = models["reader"].readtext(crop)
            if ocr_result:
                # Limpieza de placa: Mayúsculas y sin espacios
                detected_plate = ocr_result[0][1].upper().replace(" ", "").strip()
                max_conf = float(box.conf[0])
                break

        # --- LÓGICA DE BASE DE DATOS ---
        status = ""
        
        # A. Verificar si la placa existe en la tabla Vehiculos
        check_vehiculo = db.execute(
            text('SELECT 1 FROM public."Vehiculos" WHERE "Vehiculo_Placa" = :placa'), 
            {"placa": detected_plate}
        ).fetchone()
        
        if not check_vehiculo and detected_plate != "NO_DETECTADA":
            # B. AUTO-REGISTRO: Si es nueva, la creamos primero
            # Usamos Id_Propietario = 1 como usuario genérico "Sistema"
            db.execute(text("""
                INSERT INTO public."Vehiculos" ("Vehiculo_Placa", "Marca", "Modelo", "Color", "Empresa", "Id_Propietario")
                VALUES (:placa, 'Desconocido', 'Auto-Registrado', 'N/A', 'Visitante Puerto', 1)
            """), {"placa": detected_plate})
            status = "Nuevo vehículo registrado. "
        
        # C. Insertar el acceso (Esto siempre se ejecuta si hay placa)
        if detected_plate != "NO_DETECTADA":
            db.execute(text("""
                INSERT INTO public."Registros_Accesos" ("Vehiculo_Placa", "Fecha_Entrada", "Foto_Placa")
                VALUES (:placa, NOW(), :foto)
            """), {"placa": detected_plate, "foto": filename})
            db.commit()
            status += "Acceso concedido y guardado."
        else:
            status = "No se detectó ninguna placa para registrar."

        return {
            "plate": detected_plate,
            "confidence": max_conf,
            "image_url": f"http://localhost:8000/static/plates/{filename}",
            "status": status
        }

    except Exception as e:
        db.rollback()
        return {
            "plate": "Error",
            "confidence": 0.0,
            "image_url": "",
            "status": f"Error crítico: {str(e)}"
        }