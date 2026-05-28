# 🚛 LogiGate AI

> Sistema inteligente de control de acceso para patios logísticos portuarios  
> mediante visión por computadora y reconocimiento automático de placas.

![Stack](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)
![Stack](https://img.shields.io/badge/Frontend-SvelteKit-FF3E00?style=flat-square&logo=svelte)
![Stack](https://img.shields.io/badge/AI-YOLOv11-purple?style=flat-square)
![Stack](https://img.shields.io/badge/Edge-Raspberry_Pi_5-red?style=flat-square&logo=raspberry-pi)
![Stack](https://img.shields.io/badge/DB-PostgreSQL-336791?style=flat-square&logo=postgresql)

---

## 📌 ¿Qué problema resuelve?

Los patios logísticos del Puerto de Veracruz gestionan el acceso de decenas 
de vehículos diariamente usando métodos manuales (papel, radio, personal en 
garita). LogiGate automatiza este proceso:

- Detecta vehículos con visión por computadora
- Lee la placa automáticamente (OCR)
- Registra entradas y salidas en tiempo real
- Funciona **offline-first** sin depender de internet

---

## 🏗️ Arquitectura
