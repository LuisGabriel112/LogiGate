import os
# --- PARCHE CRÍTICO DE ESTABILIDAD LOGIGATE ---
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_mkldnn'] = '0'
os.environ['FLAGS_on_ednn'] = '0'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# ----------------------------------------------

from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text, func, cast, Date
from database import get_db, init_db
from models import Registro, RegistroDanos
import numpy as np
import cv2
import os
import shutil
from datetime import datetime, date, timedelta
import re
import uuid
import time
import json
from vision_engine import LicensePlateEngine
from damage_engine import DamageDetectionEngine
from security_utils import encrypt_data, decrypt_data

UPLOAD_DIR = os.path.join("static", "plates")
DAMAGE_DIR = os.path.join("static", "damages")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DAMAGE_DIR, exist_ok=True)

CAPACIDAD_TOTAL = 100

class ScanResponse(BaseModel):
    scan_id: str
    plate: str
    confidence: float
    image_url: str
    status: str

engine_ia = None
damage_engine_ia = None

def validar_formato_mexicano(texto):
    texto = texto.upper().replace(" ", "").replace("-", "")
    patrones = [
        r'^[A-Z]{3}\d{3}[A-Z]?$', # 6-7 caracteres (CDMX, Edomex)
        r'^[A-Z]{2}\d{5}$',        # 7 caracteres
        r'^[A-Z]{3}\d{4}$',        # 7 caracteres
        r'^[A-Z]{3}\d{2}\d{2}$',   # 7 caracteres
        r'^[A-Z]\d{2}[A-Z]{3}$',   # 6 caracteres
        r'^\d{2}[A-Z]{3}\d{2}$',   # 7 caracteres
        r'^[A-Z]{3}\d{3}[A-Z]{2}$' # 8 caracteres (Nuevas)
    ]
    return any(re.match(p, texto) for p in patrones)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_ia, damage_engine_ia
    init_db()
    print("--- Inicializando LogiGate Vision Engine (YOLOv11 v4 + EasyOCR) ---")
    try:
        engine_ia = LicensePlateEngine(model_path="logigate_v4.pt")
    except Exception as e:
        print(f"Error crítico al iniciar el motor de placas: {e}")
        engine_ia = LicensePlateEngine(model_path="yolo11n.pt")

    print("--- Inicializando Motor de Detección de Daños ---")
    try:
        from huggingface_hub import hf_hub_download
        dmg_path = hf_hub_download(
            repo_id="scythe410/vehicle-damage-detection-yolo",
            filename="v2.pt"
        )
        damage_engine_ia = DamageDetectionEngine(model_path=dmg_path)
    except Exception as e:
        print(f"Error al cargar modelo de daños: {e}")
        damage_engine_ia = None

    yield
    del engine_ia

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Root ─────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "LogiGate AI v4 — Operativo"}

# ── Scan (entrada principal) ──────────────────────────────────────────────────

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
            raise Exception("No se pudo leer la imagen.")

        detections = engine_ia.process_image(img)

        detected_plate = "NO_DETECTADA"
        max_conf = 0.0

        if detections:
            best = max(detections, key=lambda x: x["confidence"])
            detected_plate = best["plate"]
            max_conf = best["confidence"]

        display_plate = detected_plate
        if len(detected_plate) >= 6 and "-" not in detected_plate:
            display_plate = f"{detected_plate[:3]}-{detected_plate[3:]}"

        es_valida = detected_plate != "NO_DETECTADA"
        es_mexicana = validar_formato_mexicano(detected_plate) if es_valida else False

        if es_valida:
            estado = "entrada" if es_mexicana else "entrada"
            status_msg = f"Acceso Concedido: {display_plate}" if es_mexicana else f"Revisión Manual: {display_plate}"
        else:
            estado = "denegado"
            status_msg = "Rechazada: Placa no válida o no visible"

        # Guardar en tabla registros (modelo SQLAlchemy) - DATOS ENCRIPTADOS PARA CIBERSEGURIDAD
        registro = Registro(
            placa=encrypt_data(display_plate),
            estado=estado,
            confianza=round(max_conf * 100),
            autorizado_por="IA-LogiGate",
        )
        db.add(registro)
        db.commit()

        return {
            "scan_id": scan_id,
            "plate": display_plate,
            "confidence": float(max_conf),
            "image_url": f"/static/plates/{filename}?v={time.time()}",
            "status": status_msg,
        }

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        print(f"ERROR EN SCAN: {e}")
        return {
            "scan_id": "ERROR",
            "plate": "ERROR",
            "confidence": 0.0,
            "image_url": "",
            "status": f"Error: {str(e)}",
        }

# ── Registros ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/registros")
def get_registros(
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Registro)
        .order_by(Registro.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "placa": decrypt_data(r.placa),
            "empresa": r.empresa,
            "tipo_unidad": r.tipo_unidad,
            "conductor": decrypt_data(r.conductor),
            "estado": r.estado,
            "confianza": r.confianza,
            "autorizado_por": r.autorizado_por,
            "notas": decrypt_data(r.notas),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

# ── Stats (para mapa y panel) ─────────────────────────────────────────────────

@app.get("/api/v1/stats")
def get_stats(db: Session = Depends(get_db)):
    hoy = date.today()

    total_entradas = db.query(func.count(Registro.id)).filter(Registro.estado == "entrada").scalar() or 0
    total_salidas  = db.query(func.count(Registro.id)).filter(Registro.estado == "salida").scalar() or 0
    en_patio       = max(0, total_entradas - total_salidas)

    salidas_hoy = (
        db.query(func.count(Registro.id))
        .filter(Registro.estado == "salida", cast(Registro.created_at, Date) == hoy)
        .scalar() or 0
    )
    denegados = db.query(func.count(Registro.id)).filter(Registro.estado == "denegado").scalar() or 0

    ocupacion_pct = round((en_patio / CAPACIDAD_TOTAL) * 100) if CAPACIDAD_TOTAL > 0 else 0

    return {
        "en_patio": en_patio,
        "salidas_hoy": salidas_hoy,
        "denegados": denegados,
        "capacidad_total": CAPACIDAD_TOTAL,
        "ocupacion_pct": min(ocupacion_pct, 100),
    }

# ── Flujo por día (últimos N días) ────────────────────────────────────────────

@app.get("/api/v1/flujo")
def get_flujo(dias: int = Query(default=7, le=30), db: Session = Depends(get_db)):
    hoy = date.today()
    resultado = []

    for i in range(dias - 1, -1, -1):
        dia = hoy - timedelta(days=i)
        count = (
            db.query(func.count(Registro.id))
            .filter(cast(Registro.created_at, Date) == dia)
            .scalar() or 0
        )
        resultado.append({
            "fecha": dia.isoformat(),
            "label": dia.strftime("%a %d") if i > 0 else "Hoy",
            "count": count,
        })

    return resultado

# ── Actividad reciente ────────────────────────────────────────────────────────

@app.get("/api/v1/actividad")
def get_actividad(limit: int = Query(default=5, le=50), db: Session = Depends(get_db)):
    rows = (
        db.query(Registro)
        .order_by(Registro.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "placa": decrypt_data(r.placa),
            "empresa": r.empresa or "—",
            "estado": r.estado,
            "hora": r.created_at.strftime("%H:%M") if r.created_at else "—",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

# ── Historial legacy ──────────────────────────────────────────────────────────

@app.get("/api/v1/history")
async def get_history(db: Session = Depends(get_db)):
    try:
        query = text(
            'SELECT ra."Id_Acceso", ra."Vehiculo_Placa", ra."Fecha_Entrada", ra."Foto_Placa",'
            ' v."Marca", v."Modelo", u."Nombre(s)", u."Apellido_Paterno"'
            ' FROM public."Registros_Accesos" ra'
            ' LEFT JOIN public."Vehiculos" v ON ra."Vehiculo_Placa" = v."Vehiculo_Placa"'
            ' LEFT JOIN public."Usuarios" u ON v."Id_Propietario" = u."Id_Propietario"'
            ' ORDER BY ra."Fecha_Entrada" DESC'
        )
        result = db.execute(query)
        return [
            {
                "id_acceso": r[0],
                "placa": str(r[1]),
                "fecha": r[2].strftime("%Y-%m-%d %H:%M:%S") if r[2] else None,
                "foto_url": f"/static/plates/{r[3]}" if r[3] else None,
                "marca": str(r[4] or "Desconocido"),
                "modelo": str(r[5] or "Desconocido"),
                "propietario": f"{r[6]} {r[7]}" if r[6] else "Visitante",
            }
            for r in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Detección de Daños ────────────────────────────────────────────────────────

@app.post("/api/v1/damage-scan")
async def damage_scan(
    image: UploadFile = File(...),
    placa: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if damage_engine_ia is None:
        raise HTTPException(status_code=503, detail="Motor de daños no disponible.")
    try:
        scan_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dmg_{timestamp}_{image.filename}"
        filepath = os.path.join(DAMAGE_DIR, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        img = cv2.imread(filepath)
        if img is None:
            raise Exception("No se pudo leer la imagen.")

        analysis = damage_engine_ia.analyze(img)
        annotated = damage_engine_ia.annotate(img, analysis)

        ann_filename = f"ann_{filename}"
        cv2.imwrite(os.path.join(DAMAGE_DIR, ann_filename), annotated)

        registro = RegistroDanos(
            placa=encrypt_data(placa) if placa else "",
            imagen_url=f"/static/damages/{ann_filename}",
            danos_detectados=analysis["danos_detectados"],
            severidad=analysis["severidad"],
            damage_ratio=analysis["damage_ratio"],
            detecciones_json=json.dumps(analysis["detecciones"]),
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)

        return {
            "scan_id": scan_id,
            "registro_id": registro.id,
            "placa": placa,
            "danos_detectados": analysis["danos_detectados"],
            "severidad": analysis["severidad"],
            "damage_ratio": analysis["damage_ratio"],
            "detecciones": analysis["detecciones"],
            "image_url": f"/static/damages/{ann_filename}?v={time.time()}",
        }
    except HTTPException:
        raise
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        print(f"ERROR EN DAMAGE-SCAN: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/damage-history")
def get_damage_history(limit: int = Query(default=50, le=200), db: Session = Depends(get_db)):
    rows = (
        db.query(RegistroDanos)
        .order_by(RegistroDanos.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "placa": decrypt_data(r.placa) if r.placa else "",
            "imagen_url": r.imagen_url,
            "danos_detectados": r.danos_detectados,
            "severidad": r.severidad,
            "damage_ratio": r.damage_ratio,
            "detecciones": json.loads(r.detecciones_json) if r.detecciones_json else [],
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
