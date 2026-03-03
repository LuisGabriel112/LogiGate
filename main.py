from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # El origen de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanTarget(BaseModel):
    url: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/v1/scan")
async def create_scan(target: ScanTarget):
    # El uso de 'async' permite que la API no se bloquee mientras procesa
    return {
        "message": "Escaneo iniciado",
        "target_received": target.url,
        "status": "processing"
    }