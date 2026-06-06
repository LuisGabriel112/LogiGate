"""
Descarga dataset de Roboflow y fine-tunea el modelo de detección de daños.
Uso: python train_damage_model.py
"""
import os
import glob
import shutil
from pathlib import Path

# ── Configuración ──────────────────────────────────────────────────────────────
ROBOFLOW_API_KEY = "7P3l47cTE5Zr3RRA5zuG"
WORKSPACE        = "car-damaged-detection-e66m0"
PROJECT          = "car-damaged-severity-detection"
VERSION          = 29
DATASET_DIR      = "./damage_dataset"
OUTPUT_DIR       = "./damage_model_trained"

# Hiperparámetros de entrenamiento
EPOCHS     = 50
IMGSZ      = 640
BATCH      = 8        # bajar a 4 si hay poca RAM
PATIENCE   = 15       # early stopping si no mejora en N epochs
DEVICE     = "cpu"    # cambiar a 0 si tienes GPU NVIDIA

# Modelo base (el que ya usamos, lo fine-tuneamos)
BASE_MODEL = "yolo11x-seg.pt"
# ──────────────────────────────────────────────────────────────────────────────


def download_dataset():
    print("\n[1/3] Descargando dataset de Roboflow...")
    from roboflow import Roboflow
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    proj = rf.workspace(WORKSPACE).project(PROJECT)
    version = proj.version(VERSION)
    dataset = version.download("yolov8", location=DATASET_DIR, overwrite=False)
    print(f"    Dataset descargado en: {dataset.location}")
    return dataset.location


def extract_if_needed(dataset_path: str) -> str:
    """Extrae el zip si Roboflow no lo hizo automáticamente."""
    import zipfile
    zip_path = os.path.join(dataset_path, "roboflow.zip")
    if os.path.exists(zip_path):
        print(f"    Extrayendo {zip_path}...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(dataset_path)
        os.remove(zip_path)
        print("    Extracción completa.")
    return dataset_path


def fix_yaml(dataset_path: str) -> str:
    """Localiza data.yaml y corrige rutas para que funcione correctamente."""
    # Buscar data.yaml en el directorio y subdirectorios
    matches = glob.glob(os.path.join(dataset_path, "**", "data.yaml"), recursive=True)
    if not matches:
        matches = glob.glob(os.path.join(dataset_path, "*.yaml"), recursive=False)
    if not matches:
        raise FileNotFoundError(f"No se encontró data.yaml en {dataset_path}")

    yaml_path = matches[0]
    dataset_abs = str(Path(dataset_path).resolve()).replace("\\", "/")

    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"    YAML original:\n{content}\n")

    # Corregir rutas absolutas → relativas al yaml
    content = content.replace(dataset_abs + "/train", "train")
    content = content.replace(dataset_abs + "/valid", "valid")
    content = content.replace(dataset_abs + "/test",  "test")
    content = content.replace(dataset_abs.replace("/", "\\") + "\\train", "train")
    content = content.replace(dataset_abs.replace("/", "\\") + "\\valid", "valid")

    fixed_path = os.path.join(os.path.dirname(yaml_path), "data_fixed.yaml")
    with open(fixed_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"    YAML corregido: {fixed_path}")
    print(f"    Contenido:\n{content}")
    return fixed_path


def train(yaml_path: str):
    print("\n[2/3] Iniciando entrenamiento...")
    from ultralytics import YOLO

    model = YOLO(BASE_MODEL)
    results = model.train(
        data=yaml_path,
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        patience=PATIENCE,
        device=DEVICE,
        project=OUTPUT_DIR,
        name="damage_v1",
        exist_ok=True,
        # Augmentaciones para mejor generalización
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        flipud=0.1,
        fliplr=0.5,
        mosaic=1.0,
        copy_paste=0.3,
    )
    return results


def copy_best_model():
    print("\n[3/3] Copiando mejor modelo...")
    candidates = glob.glob(f"{OUTPUT_DIR}/damage_v1/weights/best.pt")
    if not candidates:
        print("    ERROR: No se encontró best.pt")
        return None
    src = candidates[0]
    dst = "./damage_model_custom.pt"
    shutil.copy(src, dst)
    size_mb = os.path.getsize(dst) / 1024 / 1024
    print(f"    Modelo guardado: {dst} ({size_mb:.1f} MB)")
    return dst


if __name__ == "__main__":
    print("=" * 60)
    print("  LogiGate — Fine-tuning Motor de Daños")
    print("=" * 60)

    try:
        dataset_path = download_dataset()
    except Exception as e:
        print(f"ERROR al descargar dataset: {e}")
        raise

    dataset_path = extract_if_needed(dataset_path)
    yaml_path = fix_yaml(dataset_path)

    try:
        train(yaml_path)
    except Exception as e:
        print(f"ERROR en entrenamiento: {e}")
        raise

    model_path = copy_best_model()

    if model_path:
        print("\n" + "=" * 60)
        print("  ENTRENAMIENTO COMPLETADO")
        print(f"  Modelo: {model_path}")
        print("  Actualiza main.py para usar este modelo:")
        print(f"    damage_engine_ia = DamageDetectionEngine('{model_path}')")
        print("=" * 60)
