from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager


models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Cargando modelo YOLOv11...")
    models["yolo"] = "Modelo cargado" 
    yield
    models.clear()
    print("Limpiando recursos...")

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanResponse(BaseModel):
    message: str
    filename: str
    status: str



@app.get("/")
def read_root():
    return {"Hello": "LogiGate API", "IA_Status": "Ready" if "yolo" in models else "Off"}

@app.post("/api/v1/scan", response_model=ScanResponse)
async def create_scan(image: UploadFile = File(...)):

    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


    results = models["yolo"].infer(img)[0]
    detections = sv.Detections.from_inference(results)


    
    return {"plate": "ABC-123", "confidence": 0.95}