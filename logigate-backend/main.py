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
from roboflow import Roboflow
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
    print("Conectando con Roboflow Cloud...")
    try:
        # Configuración de Roboflow Hosted
        rf = Roboflow(api_key="nFwszjsA0FpvEr9GMKqD")
        project = rf.workspace().project("placas-bpbge-yoebh")
        models["yolo"] = project.version(1).model
        print("Conexión con Roboflow exitosa.")
    except Exception as e:
        print(f"Error conectando a Roboflow: {e}")
        
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
    return {"Hello": "LogiGate API", "IA_Status": "Connected to Roboflow" if "yolo" in models else "Disconnected"}

# --- HISTORIAL ---
@app.get("/api/v1/history")
async def get_history(db: Session = Depends(get_db)):
    try:
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
                "foto_url": f"http://{row[3]}" if row[3] and row[3].startswith("http") else (f"http://192.168.100.64:8000/static/plates/{row[3]}" if row[3] else None),
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

        # 2. Procesar con Roboflow Hosted Inference
        img = cv2.imread(filepath)
        
        # Enviar imagen a Roboflow
        prediction = models["yolo"].predict(filepath, confidence=30, overlap=30).json()
        
        # LOG DE DEPURACIÓN
        print(f"DEBUG: Predicciones de Roboflow: {prediction}")
        
        detected_plate = "NO_DETECTADA"
        max_conf = 0.0

        if "predictions" in prediction and len(prediction["predictions"]) > 0:
            best_pred = None
            for p in prediction["predictions"]:
                class_name = p.get("class", "").lower()
                if "placa" in class_name or "plate" in class_name or "license" in class_name:
                    best_pred = p
                    break
            
            if not best_pred:
                best_pred = prediction["predictions"][0]
            
            x_center, y_center = best_pred["x"], best_pred["y"]
            width, height = best_pred["width"], best_pred["height"]
            
            x1 = int(x_center - (width / 2))
            y1 = int(y_center - (height / 2))
            x2 = int(x_center + (width / 2))
            y2 = int(y_center + (height / 2))
            
            h_img, w_img, _ = img.shape
            x1, y1 = max(0, x1-20), max(0, y1-20)
            x2, y2 = min(w_img, x2+20), min(h_img, y2+20)
            
            crop = img[y1:y2, x1:x2]
            
            # --- PROCESAMIENTO OCR ---
            crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            ocr_result = models["reader"].readtext(
                gray, 
                detail=1, 
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            
            if ocr_result:
                ocr_result.sort(key=lambda x: x[0][0][0])
                max_h = max([res[0][2][1] - res[0][0][1] for res in ocr_result])
                valid_parts = [res[1].upper() for res in ocr_result if (res[0][2][1] - res[0][0][1]) > (max_h * 0.4)]
                
                full_raw = "".join(valid_parts)
                detected_plate = full_raw if len(full_raw) >= 3 else "NO_DETECTADA"
                max_conf = best_pred["confidence"]

        # --- LÓGICA DE BASE DE DATOS ---
        status = ""
        if detected_plate != "NO_DETECTADA" and len(detected_plate) >= 3:
            check_vehiculo = db.execute(
                text('SELECT 1 FROM public."Vehiculos" WHERE "Vehiculo_Placa" = :placa'), 
                {"placa": detected_plate}
            ).fetchone()
            
            if not check_vehiculo:
                db.execute(text("""
                    INSERT INTO public."Vehiculos" ("Vehiculo_Placa", "Marca", "Modelo", "Color", "Empresa", "Id_Propietario")
                    VALUES (:placa, 'Desconocido', 'Auto-Registrado', 'N/A', 'Visitante Puerto', 1)
                """), {"placa": detected_plate})
                status = "Nuevo vehículo registrado. "
            
            db.execute(text("""
                INSERT INTO public."Registros_Accesos" ("Vehiculo_Placa", "Fecha_Entrada", "Foto_Placa")
                VALUES (:placa, NOW(), :foto)
            """), {"placa": detected_plate, "foto": filename})
            db.commit()
            status += "Acceso concedido."
        else:
            status = "No se detectó una placa legible."
            detected_plate = "NO_DETECTADA"

        return {
            "plate": detected_plate,
            "confidence": max_conf,
            "image_url": f"http://192.168.100.64:8000/static/plates/{filename}",
            "status": status
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error crítico: {str(e)}")
