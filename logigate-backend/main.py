import os
# --- PARCHE CRÍTICO DE ESTABILIDAD LOGIGATE ---
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_mkldnn'] = '0'
os.environ['FLAGS_on_ednn'] = '0'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# ----------------------------------------------

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
import shutil
from datetime import datetime
import re
import uuid
import time
from vision_engine import LicensePlateEngine

# --- CONFIGURACIÓN ---
UPLOAD_DIR = os.path.join("static", "plates")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ScanResponse(BaseModel):
    scan_id: str
    plate: str
    confidence: float
    image_url: str
    status: str

# Variable global para el motor de visión
engine = None
lecturas_recientes = []  # Para Votación Temporal (Redundancia)

# --- FUNCIONES DE VALIDACIÓN MÉXICO ---
def validar_formato_mexicano(texto):
    """
    Verifica si el texto cumple con los patrones de la SCT de México.
    Incluye formatos comunes en Veracruz y otros estados.
    """
    texto = texto.upper().replace(" ", "").replace("-", "")
    # Patrones: Particular (AAA000A), Camioneta/Carga (AA00000), Otros (AAA0000)
    patrones = [
        r'^[A-Z]{3}\d{3}[A-Z]$',  # AAA-000-A (Nuevas)
        r'^[A-Z]{2}\d{5}$',       # AA-00-000 (Carga)
        r'^[A-Z]{3}\d{4}$',       # AAA-0000 (Frontera/Antiguas)
        r'^[A-Z]{3}\d{2}\d{2}$',  # AAA-00-00
        r'^[A-Z]\d{2}[A-Z]{3}$',  # Formato antiguo
        r'^\d{2}[A-Z]{3}\d{2}$'   # Algunos formatos estatales
    ]
    for p in patrones:
        if re.match(p, texto): return True
    return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    print("--- Inicializando LogiGate Vision Engine (YOLOv11 v4 + EasyOCR) ---")
    try:
        engine = LicensePlateEngine(model_path="logigate_v4.pt")
    except Exception as e:
        print(f"Error crítico al iniciar el motor: {e}")
        # Intentar con un modelo genérico si falla el v4
        engine = LicensePlateEngine(model_path="yolo11n.pt")
    yield
    # Limpieza si es necesaria
    del engine

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def read_root():
    return {"IA_Status": "Connected via LogiGate Mexico Engine V4 (Veracruz Optimized)"}

@app.get("/api/v1/history")
async def get_history(db: Session = Depends(get_db)):
    try:
        # Nota: He mantenido la query original pero asegúrate de que los nombres de tablas coincidan
        query = text('SELECT ra."Id_Acceso", ra."Vehiculo_Placa", ra."Fecha_Entrada", ra."Foto_Placa", v."Marca", v."Modelo", u."Nombre(s)", u."Apellido_Paterno" FROM public."Registros_Accesos" ra LEFT JOIN public."Vehiculos" v ON ra."Vehiculo_Placa" = v."Vehiculo_Placa" LEFT JOIN public."Usuarios" u ON v."Id_Propietario" = u."Id_Propietario" ORDER BY ra."Fecha_Entrada" DESC')
        result = db.execute(query)
        return [{"id_acceso": r[0], "placa": str(r[1]), "fecha": r[2].strftime("%Y-%m-%d %H:%M:%S") if r[2] else None, "foto_url": f"http://localhost:8000/static/plates/{r[3]}" if r[3] else None, "marca": str(r[4] or "Desconocido"), "modelo": str(r[5] or "Desconocido"), "propietario": f"{r[6]} {r[7]}" if r[6] else "Visitante"} for r in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/scan", response_model=ScanResponse)
async def create_scan(image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        scan_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as buffer: 
            shutil.copyfileobj(image.file, buffer)

        img = cv2.imread(filepath)
        if img is None:
            raise Exception("No se pudo leer la imagen cargada.")

        # Procesar con el motor mejorado
        detections = engine.process_image(img)
        
        detected_plate = "NO_DETECTADA"
        max_conf = 0.0

        if detections:
            # Tomamos la detección con mayor confianza de YOLO
            best_det = max(detections, key=lambda x: x["confidence"])
            detected_plate = best_det["plate"]
            max_conf = best_det["confidence"]
        
        # Formato visual (ej: ABC-1234)
        display_plate = detected_plate
        if len(detected_plate) >= 6 and "-" not in detected_plate:
             display_plate = f"{detected_plate[:3]}-{detected_plate[3:]}"

        # --- DB LÓGICA ---
        if detected_plate != "NO_DETECTADA":
            plate_db = detected_plate
            # Verificar si la placa existe
            check = db.execute(text('SELECT 1 FROM public."Vehiculos" WHERE "Vehiculo_Placa" = :p'), {"p": plate_db}).fetchone()
            if not check:
                db.execute(text('INSERT INTO public."Vehiculos" ("Vehiculo_Placa", "Marca", "Modelo", "Color", "Empresa", "Id_Propietario") VALUES (:p, \'Desconocido\', \'Auto-Reg\', \'N/A\', \'Visitante\', 1)'), {"p": plate_db})
                db.commit()
            
            # Registrar el acceso
            db.execute(text('INSERT INTO public."Registros_Accesos" ("Vehiculo_Placa", "Fecha_Entrada", "Foto_Placa") VALUES (:p, NOW(), :f)'), {"p": plate_db, "f": filename})
            db.commit()
            
            # Validamos formato para el mensaje de status
            es_mexicana = validar_formato_mexicano(detected_plate)
            status_msg = f"Acceso Concedido: {display_plate}" if es_mexicana else f"Revisión Manual: {display_plate}"
        else:
            status_msg = "Rechazada: Placa no válida o no visible"

        return {
            "scan_id": scan_id,
            "plate": display_plate, 
            "confidence": float(max_conf), 
            "image_url": f"http://localhost:8000/static/plates/{filename}?v={time.time()}", 
            "status": status_msg
        }

    except Exception as e:
        if 'db' in locals(): db.rollback()
        print(f"ERROR EN SCAN: {e}")
        return {
            "scan_id": "ERROR",
            "plate": "ERROR", 
            "confidence": 0.0, 
            "image_url": "", 
            "status": f"Error: {str(e)}"
        }
