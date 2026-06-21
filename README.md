# Agente WhatsApp — Consultorio Médico Popayán · Demo MVP

Demo funcional de un agente conversacional estilo WhatsApp para un consultorio médico en Popayán, Colombia.
Construido con Streamlit + OpenAI (function calling). **No es producción** — el objetivo es demostrar
que la lógica del agente ya funciona y "solo falta conectarlo a WhatsApp y Google Calendar reales".

---

## Lo que incluye esta demo

| Funcionalidad | Estado |
|---|---|
| Chat estilo WhatsApp (CSS custom) | ✅ Funciona |
| Agente con function calling (OpenAI) | ✅ Funciona |
| Consultar disponibilidad de horarios | ✅ Simulado en memoria |
| Agendar citas | ✅ Simulado en `session_state` |
| Escalar a humano (síntomas / consultas médicas) | ✅ Funciona |
| Guardrail médico-legal (Ley 1581) | ✅ En el system prompt |
| Resumen semanal de obra con IA | ✅ Funciona |
| Sidebar con citas de la sesión | ✅ Funciona |
| Conexión a WhatsApp Business API | 🔧 Falta para producción |
| Google Calendar real | 🔧 Falta para producción |

---

## Correr localmente

### 1. Clonar y crear entorno

```bash
git clone <url-del-repo>
cd proyecto_popayan
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar la API key

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editar .streamlit/secrets.toml y pegar tu clave de OpenAI
```

El archivo `.streamlit/secrets.toml` debe quedar así:

```toml
OPENAI_API_KEY = "sk-proj-..."
```

### 3. Levantar la app

```bash
streamlit run app.py
```

Se abre automáticamente en `http://localhost:8501`.

---

## Desplegar en Streamlit Cloud

1. **Sube el repo a GitHub** (asegúrate de que `.streamlit/secrets.toml` esté en `.gitignore` — ya está).

2. **Entra a** [share.streamlit.io](https://share.streamlit.io) e inicia sesión con tu cuenta de GitHub.

3. **New app** → selecciona el repo → rama `main` → archivo `app.py` → **Deploy**.

4. **Agrega el secret:** en el panel de tu app ve a  
   `Settings > Secrets` y pega:
   ```toml
   OPENAI_API_KEY = "sk-proj-..."
   ```

5. La app queda en una URL pública tipo `https://tu-app.streamlit.app`.

---

## Cambiar el modelo de OpenAI

En `app.py`, línea ~15:

```python
MODEL = "gpt-4o"   # cambia a "gpt-4o-mini", "gpt-4-turbo", etc.
```

---

## Qué falta para producción

### 1. Conectar WhatsApp Business API

La función `run_agent()` en `app.py` ya está diseñada para reutilizarse desde un webhook:

```python
# En un webhook FastAPI / n8n / Flask:
from app import run_agent, TOOLS_MAP  # importar el núcleo

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(data: dict):
    numero = data["from"]
    texto  = data["text"]["body"]

    # Cargar historial del usuario desde base de datos
    history = db.get_history(numero)

    respuesta, nuevo_history = run_agent(texto, history, api_key=OPENAI_API_KEY)

    # Guardar historial actualizado
    db.save_history(numero, nuevo_history)

    # Enviar respuesta por WhatsApp Business API
    whatsapp_client.send_message(to=numero, body=respuesta)
```

El agente (system prompt, tools, guardrails) es exactamente el mismo. Solo cambia el transporte.

### 2. Reemplazar el agendamiento simulado

Las funciones `consultar_disponibilidad()` y `agendar_cita()` en `app.py` tienen interfaces claras.
Para conectar Google Calendar real, reemplaza sus cuerpos con llamadas a la Google Calendar API
(biblioteca `google-api-python-client`). La firma y los valores retornados permanecen iguales,
por lo que el agente no necesita cambios.

```python
# Reemplazo de consultar_disponibilidad() para producción:
from googleapiclient.discovery import build

def consultar_disponibilidad(fecha: str) -> dict:
    service = build("calendar", "v3", credentials=get_credentials())
    # ... llamar freebusy API y retornar el mismo formato de dict
```

### 3. Persistencia del historial

En la demo, el historial vive en `st.session_state` (se pierde al recargar).
En producción: guardar `messages_history` por número de teléfono en Redis, PostgreSQL o Firestore.

### 4. Consideraciones legales (Colombia)

- Aviso de tratamiento de datos (Ley 1581 / Decreto 1377) al iniciar la conversación.
- Consentimiento explícito antes de guardar nombre y datos de contacto.
- El guardrail médico ya está en el system prompt; revisarlo con un abogado antes de lanzar.

---

## Estructura del proyecto

```
proyecto_popayan/
├── app.py                        # Toda la lógica: núcleo del agente + UI de demo
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── secrets.toml.example      # Plantilla (subir al repo)
│   └── secrets.toml              # TU clave real (NO subir — en .gitignore)
└── README.md
```

---

## Tecnologías

- **Streamlit** — UI web en Python, desplegable en Streamlit Cloud gratis
- **OpenAI SDK** — GPT-4o con function calling nativo
- **CSS custom** — Replica la paleta y layout de WhatsApp Web

---

*Demo construida como MVP para demostración comercial. No usar en producción sin completar los puntos anteriores.*
