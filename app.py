# ============================================================
# app.py — Demo MVP: Agente WhatsApp Consultorio Médico Popayán
# ============================================================
# ETIQUETAS en comentarios:
#   [NÚCLEO] → lógica reutilizable en webhook WhatsApp / n8n
#   [UI]     → solo para la demo visual en Streamlit
# ============================================================

import streamlit as st
import openai
import json
import html
import os
from datetime import datetime, date

# ============================================================
# [NÚCLEO] CONSTANTES — cambia MODEL en una sola línea
# ============================================================
MODEL = "gpt-4o"

CONSULTORIO = {
    "nombre": "Consultorio Médico Salud Integral",
    "doctor": "Dr. Carlos Andrés Muñoz Castaño",
    "especialidad": "Medicina General y Familiar",
    "direccion": "Carrera 7 #5-28, Piso 2, Edificio Colón, Centro Histórico, Popayán, Cauca",
    "horario": "Lunes a Viernes, 8:00 AM – 12:00 PM y 2:00 PM – 6:00 PM",
    "telefono": "+57 312 456 7890",
    "precio_consulta": "$60.000 COP",
    "duracion_cita": "20 minutos",
    "indicaciones": (
        "Llegar 10 minutos antes. Traer documento de identidad "
        "y carnet de EPS si tiene. El consultorio queda en el segundo piso del Edificio Colón."
    ),
}

# Slots de atención disponibles (horario L-V 8-12 y 14-18, cada 30 min)
HORAS_DISPONIBLES = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30",
]

DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


# ============================================================
# [NÚCLEO] HERRAMIENTAS DEL AGENTE (funciones Python puras)
# ============================================================

def consultar_disponibilidad(fecha: str) -> dict:
    """
    Retorna los horarios libres para una fecha dada (YYYY-MM-DD).
    Excluye: fines de semana, fechas pasadas/hoy, y citas ya tomadas en session_state.
    """
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return {"error": f"Formato de fecha inválido: '{fecha}'. Usa YYYY-MM-DD."}

    hoy = date.today()
    if fecha_dt <= hoy:
        return {"error": "Las citas se agendan desde mañana en adelante."}

    if fecha_dt.weekday() >= 5:
        return {"error": "El consultorio no atiende sábados ni domingos."}

    citas = st.session_state.get("citas", [])
    horas_ocupadas = {c["hora"] for c in citas if c["fecha"] == fecha}
    horas_libres = [h for h in HORAS_DISPONIBLES if h not in horas_ocupadas]

    if not horas_libres:
        return {
            "disponible": False,
            "mensaje": f"El {fecha} está completamente ocupado. ¿Probamos otra fecha?",
        }

    return {
        "disponible": True,
        "fecha": fecha,
        "dia": DIAS_ES[fecha_dt.weekday()],
        "horarios_libres": horas_libres,
    }


def agendar_cita(nombre: str, motivo: str, fecha: str, hora: str, contacto: str = "") -> dict:
    """
    Valida disponibilidad y guarda la cita en st.session_state.
    Rechaza: fechas pasadas, fines de semana, horarios inválidos u ocupados.
    """
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return {"error": f"Formato de fecha inválido: '{fecha}'."}

    if fecha_dt <= date.today():
        return {"error": "Solo se pueden agendar citas desde mañana en adelante."}

    if fecha_dt.weekday() >= 5:
        return {"error": "El consultorio no atiende sábados ni domingos."}

    if hora not in HORAS_DISPONIBLES:
        return {"error": f"'{hora}' no es un horario válido del consultorio."}

    citas = st.session_state.get("citas", [])
    if any(c["fecha"] == fecha and c["hora"] == hora for c in citas):
        return {"error": f"El horario {hora} del {fecha} ya está ocupado. Por favor elige otro."}

    nueva_cita = {
        "nombre": nombre.strip(),
        "motivo": motivo.strip(),
        "fecha": fecha,
        "hora": hora,
        "contacto": contacto.strip(),
        "agendada_en": datetime.now().strftime("%H:%M"),
    }

    if "citas" not in st.session_state:
        st.session_state.citas = []
    st.session_state.citas.append(nueva_cita)

    return {
        "confirmada": True,
        "cita": nueva_cita,
        "mensaje": (
            f"Cita confirmada para {nombre.strip()} el {fecha} a las {hora}. "
            f"📍 {CONSULTORIO['direccion']}. "
            f"{CONSULTORIO['indicaciones']}"
        ),
    }


def escalar_a_humano(motivo: str) -> dict:
    """
    Registra la escalación y devuelve los datos de contacto del consultorio.
    """
    if "escalaciones" not in st.session_state:
        st.session_state.escalaciones = []
    st.session_state.escalaciones.append({
        "motivo": motivo,
        "hora": datetime.now().strftime("%H:%M"),
    })
    return {
        "escalado": True,
        "contacto": CONSULTORIO["telefono"],
        "mensaje": (
            "Te conecto con alguien del consultorio para que te ayude mejor 🙏. "
            f"También puedes llamar directamente al {CONSULTORIO['telefono']} "
            f"en horario {CONSULTORIO['horario']}."
        ),
    }


# ============================================================
# [NÚCLEO] SCHEMAS JSON DE LAS HERRAMIENTAS PARA OPENAI
# ============================================================
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_disponibilidad",
            "description": "Consulta los horarios disponibles para una fecha específica en el consultorio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha": {
                        "type": "string",
                        "description": "Fecha en formato YYYY-MM-DD (ej: 2025-06-23)",
                    }
                },
                "required": ["fecha"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agendar_cita",
            "description": (
                "Agenda una cita médica cuando el paciente ya confirmó fecha, hora "
                "y proporcionó su nombre completo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {
                        "type": "string",
                        "description": "Nombre completo del paciente",
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Motivo breve de la consulta (ej: consulta general, control, revisión)",
                    },
                    "fecha": {
                        "type": "string",
                        "description": "Fecha en formato YYYY-MM-DD",
                    },
                    "hora": {
                        "type": "string",
                        "description": "Hora en formato HH:MM (ej: 09:00)",
                    },
                    "contacto": {
                        "type": "string",
                        "description": "Número de teléfono o contacto del paciente (opcional)",
                    },
                },
                "required": ["nombre", "motivo", "fecha", "hora"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalar_a_humano",
            "description": (
                "Escala la conversación a una persona del consultorio cuando: "
                "el paciente describe síntomas, pide orientación clínica, o la situación lo requiere."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "motivo": {
                        "type": "string",
                        "description": "Razón por la que se escala al personal del consultorio",
                    }
                },
                "required": ["motivo"],
            },
        },
    },
]

TOOLS_MAP = {
    "consultar_disponibilidad": consultar_disponibilidad,
    "agendar_cita": agendar_cita,
    "escalar_a_humano": escalar_a_humano,
}


# ============================================================
# [NÚCLEO] SYSTEM PROMPT — incluye fecha de hoy para fechas relativas
# ============================================================
def get_system_prompt() -> str:
    hoy = date.today()
    fecha_legible = f"{DIAS_ES[hoy.weekday()]} {hoy.day} de {MESES_ES[hoy.month]} de {hoy.year}"

    return f"""Eres el asistente virtual de WhatsApp del {CONSULTORIO['nombre']} en Popayán, Colombia.
Atiendes a los pacientes con calidez y profesionalismo, como en un chat real de WhatsApp.

DATOS DEL CONSULTORIO:
- Doctor: {CONSULTORIO['doctor']} — {CONSULTORIO['especialidad']}
- Dirección: {CONSULTORIO['direccion']}
- Horario de atención: {CONSULTORIO['horario']}
- Precio por consulta: {CONSULTORIO['precio_consulta']} (duración aproximada {CONSULTORIO['duracion_cita']})
- Teléfono: {CONSULTORIO['telefono']}
- Indicaciones al llegar: {CONSULTORIO['indicaciones']}

HOY ES {fecha_legible} ({hoy.isoformat()}).
Usa esta fecha para interpretar expresiones como "mañana", "el viernes", "la próxima semana", etc.

TUS FUNCIONES:
1. Responder preguntas ADMINISTRATIVAS: horario, dirección, precio, qué traer, cómo llegar.
2. AGENDAR citas siguiendo este flujo:
   - Pregunta qué fecha le interesa al paciente.
   - Llama a consultar_disponibilidad para ver horarios reales.
   - Muestra los horarios disponibles de forma corta (ej: "Tenemos 9:00, 10:00 y 14:30 ¿cuál le queda mejor?").
   - Cuando el paciente elija una hora, pide su nombre completo si no lo tienes.
   - Llama a agendar_cita y confirma la cita.

GUARDRAIL CRÍTICO — RESPONSABILIDAD MÉDICA Y LEY 1581 DE HABEAS DATA (COLOMBIA):
JAMÁS des consejo médico. JAMÁS interpretes síntomas. JAMÁS diagnostiques.
JAMÁS recomiendes medicamentos ni tratamientos.
Si el paciente describe síntomas o pide orientación clínica: muéstrale empatía,
NO opines del tema médico, y llama a escalar_a_humano inmediatamente.

ESTILO:
- Mensajes CORTOS: máximo 2-3 frases por turno.
- Español colombiano cálido y natural. Puedes usar "usted" o "tú" según el tono del paciente.
- Emojis con moderación (máximo 2 por mensaje).
- Sin formato markdown. Este es un chat de WhatsApp, no un documento.
- Al mostrar horarios disponibles, ponlos en una línea corta separados por comas, no en lista.
"""


# ============================================================
# [NÚCLEO] LOOP DEL AGENTE — reutilizable desde webhook WhatsApp/n8n
# ============================================================
def run_agent(user_text: str, history: list, api_key: str) -> tuple[str, list]:
    """
    Recibe el texto del usuario y el historial previo (formato OpenAI, sin system prompt).
    Ejecuta el ciclo tool-calling hasta obtener respuesta final (máx. 6 iteraciones).
    Retorna (respuesta_final: str, historial_actualizado: list).

    Para usar desde un webhook de WhatsApp: pasar api_key y persistir el historial
    por número de teléfono en una base de datos. El resto es idéntico.
    """
    client = openai.OpenAI(api_key=api_key)

    messages: list[dict] = (
        [{"role": "system", "content": get_system_prompt()}]
        + history
        + [{"role": "user", "content": user_text}]
    )

    for _ in range(6):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.4,
        )

        choice = response.choices[0]
        msg = choice.message

        # Construir dict del mensaje del asistente (sin campos extra del SDK)
        assistant_msg: dict = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                fn = TOOLS_MAP.get(fn_name)
                result = fn(**fn_args) if fn else {"error": f"Herramienta desconocida: {fn_name}"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            # Respuesta final del agente
            final_text = msg.content or "Lo siento, ocurrió un error. Por favor intenta de nuevo."
            # Historial sin el system prompt para guardar en session_state / base de datos
            new_history = [m for m in messages if m.get("role") != "system"]
            return final_text, new_history

    fallback = "Lo siento, no pude procesar tu solicitud. Por favor intenta de nuevo. 🙏"
    new_history = [m for m in messages if m.get("role") != "system"]
    return fallback, new_history


# ============================================================
# [UI] CONFIGURACIÓN DE PÁGINA STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Agente WhatsApp — Consultorio Médico Popayán",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# [UI] VERIFICACIÓN DE API KEY — falla limpia si no está
# ============================================================
try:
    api_key: str = st.secrets.get("OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
except Exception:
    api_key = os.environ.get("OPENAI_API_KEY", "")

if not api_key:
    st.error(
        "**⚠️ Falta la clave de OpenAI.**\n\n"
        "Agrega tu `OPENAI_API_KEY` en `.streamlit/secrets.toml`:\n\n"
        "```toml\nOPENAI_API_KEY = 'sk-...'\n```\n\n"
        "O como variable de entorno: `export OPENAI_API_KEY=sk-...`"
    )
    st.stop()

# ============================================================
# [UI] SESSION STATE — dos listas separadas (pantalla vs historial OpenAI)
# ============================================================
if "messages_display" not in st.session_state:
    # Lista de dicts {role: "paciente"|"bot", text: str, time: str}
    st.session_state.messages_display = []

if "messages_history" not in st.session_state:
    # Historial en formato OpenAI (sin system prompt) para pasar a run_agent
    st.session_state.messages_history = []

if "citas" not in st.session_state:
    st.session_state.citas = []

if "escalaciones" not in st.session_state:
    st.session_state.escalaciones = []

# ============================================================
# [UI] SIDEBAR — citas agendadas en la sesión
# ============================================================
with st.sidebar:
    st.markdown("## 📅 Citas agendadas")

    citas = st.session_state.citas
    if not citas:
        st.info("Aún no hay citas en esta sesión.")
    else:
        citas_ordenadas = sorted(citas, key=lambda c: (c["fecha"], c["hora"]))
        for c in citas_ordenadas:
            with st.container():
                st.markdown(
                    f"**{c['nombre']}**  \n"
                    f"📆 {c['fecha']}  ⏰ {c['hora']}  \n"
                    f"📋 {c['motivo']}"
                    + (f"  \n📱 {c['contacto']}" if c["contacto"] else "")
                )
                st.divider()

        col_btn, _ = st.columns([1, 1])
        with col_btn:
            if st.button("🗑️ Limpiar citas", use_container_width=True):
                st.session_state.citas = []
                st.rerun()

    st.caption("Agendamiento simulado · luego se conecta a Google Calendar")

    if st.session_state.escalaciones:
        st.markdown("---")
        st.markdown("### 🚨 Escalaciones al personal")
        for e in st.session_state.escalaciones:
            st.warning(f"⏰ {e['hora']}: {e['motivo']}")


# ============================================================
# [UI] CSS ESTILO WHATSAPP
# ============================================================
st.html("""
<style>
/* ── Header verde WhatsApp ── */
.wa-header {
    background-color: #008069;
    color: white;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-radius: 10px 10px 0 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.wa-avatar {
    width: 42px;
    height: 42px;
    background: #25d366;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
    border: 2px solid rgba(255,255,255,0.3);
}
.wa-info { display: flex; flex-direction: column; line-height: 1.3; }
.wa-name { font-weight: 600; font-size: 15px; letter-spacing: 0.1px; }
.wa-status { font-size: 12px; opacity: 0.85; }

/* ── Área de mensajes ── */
.wa-chat {
    background-color: #efeae2;
    height: 520px;
    overflow-y: auto;
    padding: 14px 10px 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 3px;
    border-left: 1px solid #d1d7db;
    border-right: 1px solid #d1d7db;
    scroll-behavior: smooth;
}

/* ── Filas de mensaje ── */
.msg-row { display: flex; margin-bottom: 2px; }
.msg-row.incoming { justify-content: flex-start; }
.msg-row.outgoing { justify-content: flex-end; }

/* ── Burbujas ── */
.bubble {
    max-width: 72%;
    padding: 7px 11px 5px 11px;
    font-size: 14px;
    line-height: 1.45;
    position: relative;
    word-wrap: break-word;
    word-break: break-word;
}
.bubble.incoming {
    background: #ffffff;
    border-radius: 0px 8px 8px 8px; /* esquina sup. izq. recta */
    box-shadow: 0 1px 1px rgba(0,0,0,0.10);
}
.bubble.outgoing {
    background: #d9fdd3;
    border-radius: 8px 0px 8px 8px; /* esquina sup. der. recta */
    box-shadow: 0 1px 1px rgba(0,0,0,0.10);
}
.bubble-text { color: #111b21; }
.bubble-time {
    font-size: 11px;
    color: #667781;
    text-align: right;
    margin-top: 3px;
    margin-bottom: -1px;
    white-space: nowrap;
}

/* ── Footer del chat ── */
.wa-footer {
    background: #f0f2f5;
    border: 1px solid #d1d7db;
    border-top: none;
    border-radius: 0 0 10px 10px;
    padding: 7px 14px;
    font-size: 12px;
    color: #8696a0;
    text-align: center;
}

/* ── Placeholder vacío ── */
.wa-empty {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #8696a0;
    font-size: 13px;
    flex-direction: column;
    gap: 8px;
}
</style>
""")


# ============================================================
# [UI] TABS PRINCIPALES
# ============================================================
tab1, tab2 = st.tabs(["💬 Consultorio", "🏗️ Resumen de obra"])


# ============================================================
# [UI] TAB 1 — CHAT ESTILO WHATSAPP
# ============================================================
with tab1:
    # Centrar el chat con columnas
    _, col_chat, _ = st.columns([0.5, 3, 0.5])

    with col_chat:
        # Header del "teléfono"
        st.html(f"""
        <div class="wa-header">
            <div class="wa-avatar">🏥</div>
            <div class="wa-info">
                <span class="wa-name">{CONSULTORIO['nombre']}</span>
                <span class="wa-status">🟢 En línea</span>
            </div>
        </div>
        """)

        # Construir HTML de burbujas
        if not st.session_state.messages_display:
            bubbles_html = """
            <div class="wa-empty">
                <span style="font-size:32px">💬</span>
                <span>Escribe para comenzar la conversación</span>
            </div>"""
        else:
            bubbles_html = ""
            for m in st.session_state.messages_display:
                safe_text = html.escape(m["text"]).replace("\n", "<br>")
                t = m["time"]
                if m["role"] == "bot":
                    bubbles_html += f"""
                    <div class="msg-row incoming">
                        <div class="bubble incoming">
                            <div class="bubble-text">{safe_text}</div>
                            <div class="bubble-time">{t}</div>
                        </div>
                    </div>"""
                else:
                    bubbles_html += f"""
                    <div class="msg-row outgoing">
                        <div class="bubble outgoing">
                            <div class="bubble-text">{safe_text}</div>
                            <div class="bubble-time">{t} ✓✓</div>
                        </div>
                    </div>"""

        # Contenedor scrollable de mensajes
        st.html(f"""
        <div class="wa-chat" id="wa-chat-box">
            {bubbles_html}
        </div>
        """)

        # Footer tipo WhatsApp
        st.html("""
        <div class="wa-footer">
            🔒 Mensajes cifrados de extremo a extremo
        </div>
        """)

    # Chat input fuera de columnas (requisito de Streamlit)
    prompt = st.chat_input("Escribe como si fueras el paciente…")

    if prompt:
        now = datetime.now().strftime("%H:%M")

        # Agregar mensaje del paciente a la pantalla
        st.session_state.messages_display.append({
            "role": "paciente",
            "text": prompt,
            "time": now,
        })

        # Llamar al núcleo del agente
        with st.spinner("✍️ escribiendo…"):
            try:
                response, new_history = run_agent(
                    user_text=prompt,
                    history=st.session_state.messages_history,
                    api_key=api_key,
                )
                st.session_state.messages_history = new_history

                st.session_state.messages_display.append({
                    "role": "bot",
                    "text": response,
                    "time": datetime.now().strftime("%H:%M"),
                })

            except openai.AuthenticationError:
                st.session_state.messages_display.append({
                    "role": "bot",
                    "text": "⚠️ La clave de OpenAI no es válida. Verifícala en los secrets.",
                    "time": datetime.now().strftime("%H:%M"),
                })
            except openai.RateLimitError:
                st.session_state.messages_display.append({
                    "role": "bot",
                    "text": "⚠️ Se superó el límite de la API. Espera un momento e intenta de nuevo.",
                    "time": datetime.now().strftime("%H:%M"),
                })
            except Exception as e:
                st.session_state.messages_display.append({
                    "role": "bot",
                    "text": f"⚠️ Error técnico: {str(e)[:120]}",
                    "time": datetime.now().strftime("%H:%M"),
                })

        st.rerun()


# ============================================================
# [UI] TAB 2 — RESUMEN SEMANAL DE OBRA (segunda demo de agente)
# ============================================================
NOTAS_EJEMPLO = """Obra: Edificio residencial "Los Cerezos" — Cra 9 #18-40, Barrio Bolívar, Popayán, Cauca
Maestro de obra: Don Hernando Mosquera | Semana del 16 al 20 de junio de 2025

LUNES 16/06:
Se avanzó en la fundición de columnas del bloque B. Se completaron 4 de 6 columnas programadas. El proveedor de varilla (Aceros del Cauca) no llegó en la tarde — dijo que el camión tuvo un problema en la vía Cali-Popayán. Hay que reagendar entrega para el miércoles.

MARTES 17/06:
Lluvia desde las 2:00 pm. No se pudo trabajar en cubierta ni en el pañete exterior. Se aprovechó para instalar tubería sanitaria interior (baños piso 1 y 2). La cuadrilla de mampostería terminó el muro divisorio del local 2.

MIÉRCOLES 18/06:
Llegó la varilla. Se instalaron 8 ventanas del primer piso (falta el pañete interior en los marcos, aprox. 2 días de trabajo). El maestro reporta que la mezcla de mortero del muro norte quedó muy seca, hay que revisar adherencia.

JUEVES 19/06:
Visita del supervisor, Ing. Bermúdez. Observación crítica: falta refuerzo en la unión columna-viga del eje 3; debe corregirse antes de continuar con la losa del segundo piso. Se tomaron fotos. El arquitecto fue notificado.

VIERNES 20/06:
Se retomó trabajo en cubierta. Avance del 60% en impermeabilización (falta el sector norte). El maestro Hernando estima 2 días más para terminar la cubierta si no llueve. Pendiente urgente: cotización de pintura exterior (3 casas proveedoras en Popayán, buscar antes del martes)."""

with tab2:
    st.subheader("🏗️ Resumen semanal de obra")
    st.caption(
        "Pega las notas crudas de la semana (mensajes de WhatsApp, apuntes del maestro, "
        "notas de voz transcritas) y genera un resumen estructurado listo para enviar."
    )

    notas = st.text_area(
        "Notas de la semana",
        value=NOTAS_EJEMPLO,
        height=260,
        placeholder="Pega aquí los mensajes o notas de la semana…",
        key="notas_obra",
    )

    generar = st.button("✨ Generar resumen semanal", type="primary", key="btn_resumen")

    if generar:
        if not notas.strip():
            st.warning("Ingresa las notas de la semana antes de generar el resumen.")
        else:
            with st.spinner("Generando resumen con IA…"):
                try:
                    client = openai.OpenAI(api_key=api_key)
                    completion = client.chat.completions.create(
                        model=MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Eres un asistente de gestión de obras de construcción en Colombia. "
                                    "Recibes notas crudas de la semana y generas un resumen estructurado "
                                    "listo para enviar por WhatsApp. "
                                    "Usa EXACTAMENTE estas secciones y emojis, en texto plano sin markdown:\n\n"
                                    "✅ AVANCES DE LA SEMANA\n"
                                    "🚧 PENDIENTES\n"
                                    "⚠️ RIESGOS Y ALERTAS\n"
                                    "📊 PROGRESO ESTIMADO (solo un % y una frase breve)\n"
                                    "➡️ PRÓXIMOS PASOS (máx. 3)\n\n"
                                    "Sé conciso, práctico y en español colombiano. "
                                    "Sin asteriscos ni formato markdown — es para WhatsApp."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    "Genera el resumen semanal de estas notas de obra:\n\n"
                                    + notas
                                ),
                            },
                        ],
                        max_tokens=700,
                        temperature=0.3,
                    )
                    resumen = completion.choices[0].message.content or ""

                    st.success("✅ Resumen generado")
                    st.text_area(
                        "Resumen para WhatsApp",
                        value=resumen,
                        height=340,
                        key="resumen_output",
                    )
                    st.download_button(
                        label="⬇️ Descargar .txt",
                        data=resumen,
                        file_name=f"resumen_obra_{date.today().isoformat()}.txt",
                        mime="text/plain",
                    )

                except openai.AuthenticationError:
                    st.error("⚠️ La clave de OpenAI no es válida. Verifícala en los secrets.")
                except Exception as e:
                    st.error(f"Error al generar el resumen: {e}")


# ============================================================
# [UI] FOOTER GLOBAL
# ============================================================
st.html("""
<div style="text-align:center; color:#aaa; font-size:12px; margin-top:24px; padding-bottom:8px;">
    Demo · agendamiento simulado · falta conectar WhatsApp Business API y Google Calendar
</div>
""")
