# 🚛 LogiGate AI

> Sistema inteligente de control de acceso para patios logísticos portuarios
> mediante visión por computadora y reconocimiento automático de placas.

![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)
![SvelteKit](https://img.shields.io/badge/Frontend-SvelteKit-FF3E00?style=flat-square&logo=svelte)
![YOLOv11](https://img.shields.io/badge/AI-YOLOv11-purple?style=flat-square)
![RPi](https://img.shields.io/badge/Edge-Raspberry_Pi_5-red?style=flat-square&logo=raspberry-pi)
![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-336791?style=flat-square&logo=postgresql)

---

## 📌 ¿Qué problema resuelve?

Los patios logísticos del Puerto de Veracruz gestionan el acceso de decenas
de vehículos diariamente usando métodos manuales. LogiGate automatiza este proceso:

- Detecta vehículos con visión por computadora
- Lee la placa automáticamente (OCR)
- Registra entradas y salidas en tiempo real
- Funciona **offline-first** sin depender de internet

---

## 🏗️ Arquitectura

    Cámara PoE (Hikvision)
        │
        ▼
    YOLOv11 + PaddleOCR  ←── Inferencia NCNN (~0.5-1.0s)
        │
        ▼
    FastAPI Backend  ──►  PostgreSQL (local)
        │
        ▼
    SvelteKit PWA (Dashboard offline-first)
        │
        ▼  (sync cuando hay internet)
    Nube / Reportes

**Hardware:** Raspberry Pi 5 · Cámara PoE Hikvision · Inyector PoE · Cat6
**Costo de hardware:** ~$6,000 MXN

---

## 🛠️ Tech Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | SvelteKit (Svelte 5) · PWA offline-first |
| Backend | FastAPI · Python |
| Base de datos | PostgreSQL |
| Visión por computadora | YOLOv11 · PaddleOCR |
| Inferencia en edge | NCNN |
| Hardware | Raspberry Pi 5 · Cámara PoE Hikvision |

---

## 🚀 Instalación

**Requisitos:** Python 3.11+ · PostgreSQL · Node.js 18+

**Backend**

```bash
git clone https://github.com/LuisGabriel112/LogiGate
cd LogiGate/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```


---

## 👤 Autores

**Luis Gabriel Venegas Saucedo**
[LinkedIn](https://linkedin.com/in/luis-gabriel-venegas-saucedo-26a68b236) ·
[GitHub](https://github.com/LuisGabriel112) ·
venegassaucedoluis@gmail.com 

---

**Joshua Neftalí Marín Leynez**
[LinkedIn](https://www.linkedin.com/in/joshua-neftal%C3%AD-mar%C3%ADn-leynez-6519213a7/) ·
[GitHub](https://github.com/joshuamar0902) ·
joshuaneft30@gmail.com
