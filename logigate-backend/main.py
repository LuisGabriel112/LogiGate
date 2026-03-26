import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from typing import Optional
import numpy as np
import cv2

from database import engine, get_db, SessionLocal, Base
from models import User, Registro
from auth import verify_password, get_password_hash, create_access_token, get_current_user

from ultralytics import YOLO
from paddleocr import PaddleOCR

# ────────────────────────────────────────────────
# Modelos IA compartidos
# ────────────────────────────────────────────────
ai = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando LogiGate AI Backend...")

    Base.metadata.create_all(bind=engine)
    _seed_users()

    print("Cargando YOLOv11...")
    ai["yolo"] = YOLO("yolo11s.pt")

    print("Cargando PaddleOCR...")
    try:
        ai["ocr"] = PaddleOCR(use_angle_cls=True, lang="en")
        print("PaddleOCR listo.")
    except Exception as e:
        print(f"PaddleOCR no disponible: {e}. El scan retornará placa simulada.")
        ai["ocr"] = None

    print("Backend listo.")
    yield

    ai.clear()
    print("Recursos liberados.")


def _seed_users():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add_all([
                User(username="admin",     hashed_password=get_password_hash("admin123"),   nombre="Carlos Ruiz",     rol="admin"),
                User(username="guardia01", hashed_password=get_password_hash("guardia123"), nombre="Oficial Ramírez", rol="guardia"),
            ])
            db.commit()
            print("Usuarios iniciales creados.")
    finally:
        db.close()


# ────────────────────────────────────────────────
# App
# ────────────────────────────────────────────────
app = FastAPI(title="LogiGate AI", version="2.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  "https://localhost:5173",
        "http://localhost:5174",  "https://localhost:5174",
        "http://192.168.1.68:5173", "https://192.168.1.68:5173",
        "http://192.168.1.68:5174", "https://192.168.1.68:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class RegistroCreate(BaseModel):
    placa: str
    empresa: Optional[str] = None
    tipo_unidad: Optional[str] = None
    conductor: Optional[str] = None
    estado: str
    confianza: Optional[float] = None
    danos_visibles: bool = False
    sellos_rotos: bool = False
    notas: Optional[str] = None


# ────────────────────────────────────────────────
# Lógica de visión
# ────────────────────────────────────────────────
TIPO_MAP = {
    "truck": "Trailer 53'",
    "car": "Automóvil",
    "bus": "Autobús",
    "motorcycle": "Motocicleta",
    "van": "Van",
}


def _run_vision(img: np.ndarray) -> dict:
    """
    Detecta el vehículo con YOLO, recorta la región y extrae texto de placa con OCR.
    Devuelve placa, confianza y tipo_unidad.
    """
    yolo: YOLO = ai["yolo"]
    ocr: PaddleOCR = ai["ocr"]

    results = yolo(img, verbose=False)[0]

    region = img
    confianza = 0.0
    tipo = "Vehículo"

    if len(results.boxes) > 0:
        # Tomamos la detección con mayor confianza
        idx = int(results.boxes.conf.argmax())
        conf = float(results.boxes.conf[idx])
        box = results.boxes.xyxy[idx].tolist()
        cls_id = int(results.boxes.cls[idx])

        confianza = conf
        class_name = yolo.names.get(cls_id, "vehicle")
        tipo = TIPO_MAP.get(class_name, class_name.capitalize())

        # Recortar con margen
        h, w = img.shape[:2]
        x1 = max(0, int(box[0]) - 15)
        y1 = max(0, int(box[1]) - 15)
        x2 = min(w, int(box[2]) + 15)
        y2 = min(h, int(box[3]) + 15)
        region = img[y1:y2, x1:x2]

    if region.size == 0:
        region = img

    placa = "NO DETECTADA"

    if ocr is not None:
        try:
            ocr_result = ocr.predict(region)
            textos = []
            if ocr_result:
                for page in ocr_result:
                    # PaddleOCR 3.x: objeto con rec_texts y rec_scores
                    if hasattr(page, 'rec_texts') and hasattr(page, 'rec_scores'):
                        for text, score in zip(page.rec_texts, page.rec_scores):
                            if score > 0.45 and isinstance(text, str) and text.strip():
                                textos.append(text)
                    # Fallback formato antiguo (lista de listas)
                    elif isinstance(page, list):
                        for line in page:
                            try:
                                text_info = line[1]
                                if isinstance(text_info, (list, tuple)):
                                    text, conf = text_info[0], text_info[1]
                                elif isinstance(text_info, dict):
                                    text = text_info.get("transcription", text_info.get("text", ""))
                                    conf = text_info.get("score", text_info.get("confidence", 0))
                                else:
                                    continue
                                if conf > 0.45 and isinstance(text, str):
                                    textos.append(text)
                            except (IndexError, TypeError, KeyError):
                                pass
            candidatos = [
                t for t in textos
                if 3 <= len(t.replace("-", "").replace(" ", "")) <= 10
            ]
            if candidatos:
                placa = candidatos[0].upper().strip()
        except Exception as e:
            print(f"Error OCR: {e}")

    return {
        "placa": placa,
        "confianza": round(confianza * 100, 1),
        "tipo_unidad": tipo,
    }


# ────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────
@app.get("/")
def health():
    return {
        "status": "ok",
        "ia_status": "ready" if "yolo" in ai else "loading",
        "version": "2.4.0",
    }


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_access_token({
        "sub": user.username,
        "nombre": user.nombre,
        "rol": user.rol,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"username": user.username, "nombre": user.nombre, "rol": user.rol},
    }


@app.post("/api/v1/scan")
async def scan_image(image: UploadFile = File(...)):
    contents = await image.read()
    print(f"[SCAN] Imagen recibida: {len(contents)} bytes")
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        print("[SCAN] ERROR: imagen inválida")
        raise HTTPException(status_code=400, detail="Imagen inválida o corrupta")

    print(f"[SCAN] Imagen decodificada: {img.shape}")
    result = _run_vision(img)
    print(f"[SCAN] Resultado: {result}")
    return {**result, "status": "success"}


@app.post("/api/v1/registros")
def crear_registro(
    data: RegistroCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    registro = Registro(
        placa=data.placa.upper(),
        empresa=data.empresa,
        tipo_unidad=data.tipo_unidad,
        conductor=data.conductor,
        estado=data.estado,
        confianza=data.confianza,
        danos_visibles=int(data.danos_visibles),
        sellos_rotos=int(data.sellos_rotos),
        notas=data.notas,
        autorizado_por=current_user.get("nombre", current_user.get("sub")),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return {
        "id": registro.id,
        "placa": registro.placa,
        "estado": registro.estado,
        "created_at": registro.created_at,
    }


@app.get("/api/v1/registros")
def listar_registros(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    rows = db.query(Registro).order_by(Registro.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "placa": r.placa,
            "empresa": r.empresa,
            "tipo_unidad": r.tipo_unidad,
            "conductor": r.conductor,
            "estado": r.estado,
            "confianza": r.confianza,
            "danos_visibles": bool(r.danos_visibles),
            "sellos_rotos": bool(r.sellos_rotos),
            "notas": r.notas,
            "autorizado_por": r.autorizado_por,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@app.get("/api/v1/stats")
def get_stats(db: Session = Depends(get_db)):
    entradas = db.query(Registro).filter(Registro.estado == "entrada").count()
    salidas  = db.query(Registro).filter(Registro.estado == "salida").count()
    denegados = db.query(Registro).filter(Registro.estado == "denegado").count()
    en_patio = max(0, entradas - salidas)
    return {
        "en_patio": en_patio,
        "salidas_hoy": salidas,
        "denegados": denegados,
        "capacidad_total": 100,
        "ocupacion_pct": min(100, round(en_patio / 100 * 100, 1)),
    }
