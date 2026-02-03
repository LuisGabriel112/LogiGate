# LogiGate
🚛 LogiGate AI: Sistema inteligente de gestión de patios logísticos. Automatización de accesos mediante LPR, inspección de daños con visión artificial y predicción de flujos para entornos portuarios. Por JOLTEC.

# LogiGate AI 🚛🤖
> **Transformando la logística portuaria con Inteligencia Artificial.**

LogiGate AI es una plataforma integral diseñada para optimizar la operación de patios de maniobras y depósitos de contenedores. Mediante el uso de visión artificial avanzada, eliminamos los cuellos de botella en los accesos y digitalizamos la trazabilidad de activos en tiempo real.

---

## ✨ Características Principales

* **🔍 Motor LPR & OCR:** Reconocimiento automático de placas y números de contenedor con precisión industrial.
* **📸 Evidence Engine:** Captura automatizada de estado físico para blindaje jurídico ante daños.
* **📊 Smart Queue (IA Predictiva):** Algoritmos que predicen la saturación de puertas basándose en tendencias históricas.
* **🗺️ Interactive Patio Map:** Visualización en tiempo real de la ocupación y ubicación de unidades.
* **📶 Offline-First:** Diseñado para funcionar en condiciones de red inestables (PWA).

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
| :--- | :--- |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+) |
| **Frontend** | [SvelteKit](https://kit.svelte.dev/) + Tailwind CSS |
| **IA & Visión** | YOLOv11 & PaddleOCR |
| **Base de Datos** | PostgreSQL + TimescaleDB |
| **Mensajería** | Redis & MQTT |

---

## 🏗️ Arquitectura del Sistema

El sistema utiliza una arquitectura asíncrona para procesar flujos de video e imágenes sin bloquear la interfaz de usuario. 

1.  **Captura:** PWA en dispositivos móviles u ONVIF para cámaras fijas.
2.  **Inferencia:** Microservicio en FastAPI procesando modelos de visión.
3.  **Persistencia:** Datos estructurados en PostgreSQL con series de tiempo.
4.  **Notificación:** WebSockets para actualizaciones en tiempo real en el Dashboard.

---

## 🚀 Instalación (Desarrollo)

### Requisitos previos
* Python 3.11+
* Node.js 18+
* Docker & Docker Compose

### Pasos
1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/logigate-ai.git](https://github.com/tu-usuario/logigate-ai.git)
