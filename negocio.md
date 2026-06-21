# Prototipo: Agente de WhatsApp para Consultorio Médico
**Popayán, Colombia — Demo MVP**

---

## Qué es esto

Un agente de inteligencia artificial que atiende a los pacientes por WhatsApp, responde preguntas del consultorio y agenda citas automáticamente — sin que el médico ni su secretaria tengan que estar pendientes del celular.

Este archivo es el prototipo de demostración. La lógica del agente ya funciona completa. Lo que falta es conectarlo al canal real (WhatsApp Business) y al calendario real (Google Calendar).

---

## Qué SÍ hace hoy (en el prototipo)

| Funcionalidad | Detalle |
|---|---|
| Responde preguntas del consultorio | Dirección, horario, precio, qué traer, cómo llegar |
| Consulta disponibilidad de horarios | Muestra los slots libres del día solicitado |
| Agenda citas | Pide fecha, hora y nombre — confirma y guarda |
| Detecta conflictos | No permite dos citas en el mismo horario |
| Rechaza fines de semana y fechas pasadas | Validación automática |
| Escala a humano | Si el paciente describe síntomas o pide orientación médica |
| Guardrail médico-legal | Nunca da consejo médico ni interpreta síntomas |
| Resumen semanal de obra | Segunda demo: convierte notas crudas en reporte estructurado |

---

## Qué NO hace todavía (falta para producción)

| Faltante | Qué se necesita |
|---|---|
| Recibir mensajes reales de WhatsApp | Conectar WhatsApp Business API (Meta) |
| Enviar respuestas al celular del paciente | Mismo conector de WhatsApp Business |
| Guardar citas en Google Calendar | Reemplazar la simulación por la API de Google Calendar |
| Recordatorios automáticos | Programar mensajes 24h antes de la cita |
| Historial por paciente | Base de datos para guardar conversaciones por número |
| Panel de administración | Ver y gestionar todas las citas desde un dashboard |
| Aviso legal de datos (Ley 1581) | Mensaje de consentimiento al iniciar conversación |

---

## Cómo funciona por dentro

```
Paciente escribe en WhatsApp
        ↓
Mensaje llega al agente de IA
        ↓
El agente decide qué hacer:
   ├── Pregunta administrativa → responde directo
   ├── Quiere agendar cita    → consulta horarios → ofrece opciones → confirma → guarda
   └── Describe síntomas      → responde con empatía → escala al personal
        ↓
Respuesta regresa al paciente en segundos
```

El agente nunca improvisa datos del consultorio. Todo lo que dice (dirección, precio, horario) viene de una configuración fija que el médico define una sola vez.

---

## Ejemplos de conversación

### Ejemplo 1 — Agendar una cita

> **Paciente:** Buenas, quiero sacar una cita
>
> **Agente:** ¡Hola! Con gusto te ayudo 😊 ¿Qué día te quedaría mejor?
>
> **Paciente:** El martes
>
> **Agente:** Para el martes 24 de junio tenemos disponible: 8:00, 9:00, 10:30, 14:00 y 15:30 ¿Cuál te queda bien?
>
> **Paciente:** A las 9
>
> **Agente:** Perfecto. ¿Me das tu nombre completo para registrar la cita?
>
> **Paciente:** Ana Lucía Castaño
>
> **Agente:** ✅ Cita confirmada para Ana Lucía Castaño el martes 24 de junio a las 9:00. 📍 Carrera 7 #5-28, Piso 2, Centro, Popayán. Recuerda llegar 10 minutos antes con tu cédula 🙏

---

### Ejemplo 2 — Pregunta sobre precio y ubicación

> **Paciente:** Cuánto vale la consulta y dónde quedan?
>
> **Agente:** La consulta general vale $60.000 COP y dura aproximadamente 20 minutos. Quedamos en la Carrera 7 #5-28, Piso 2, Edificio Colón, Centro Histórico de Popayán. ¿Te gustaría agendar una cita? 📍

---

### Ejemplo 3 — Guardrail médico (lo más importante)

> **Paciente:** Me duele mucho el pecho desde ayer y tengo dificultad para respirar
>
> **Agente:** Entiendo que debes estar incómodo/a, ojalá te mejores pronto 🙏 Eso es algo que el doctor debe evaluar personalmente. Te conecto con alguien del consultorio para que te orienten mejor. También puedes llamar directo al +57 312 456 7890.

El agente **nunca** dice qué puede ser, qué tomar ni si es grave. Eso es responsabilidad exclusiva del médico.

---

### Ejemplo 4 — Horario no disponible

> **Paciente:** ¿Hay citas para el domingo?
>
> **Agente:** El consultorio no atiende sábados ni domingos. Atendemos de lunes a viernes de 8:00 AM a 12:00 PM y de 2:00 PM a 6:00 PM. ¿Te sirve algún día de la semana?

---

## Por qué tiene sentido para un consultorio en Popayán

**Problema actual:** La secretaria recibe mensajes de WhatsApp todo el día — preguntas repetidas sobre horarios, precios y disponibilidad. Agenda citas a mano y a veces se cruzan o se olvidan.

**Con el agente:**
- Atiende pacientes 24/7, incluso fines de semana (aunque el consultorio no atienda)
- Responde en segundos, no en horas
- No agenda dos pacientes en el mismo horario
- La secretaria solo interviene cuando hay algo que el agente no puede resolver
- El médico llega con su agenda ya organizada

**Costo vs. beneficio:** Un solo mes de consultas mal coordinadas (pacientes que no llegan, horas cruzadas, llamadas perdidas) cuesta más que implementar el sistema.

---

## Hoja de ruta para producción

### Fase 1 — Lo que ya está listo ✅
- Agente con inteligencia artificial funcionando
- Lógica de agendamiento validada
- Guardrails legales y médicos implementados
- Interfaz de demostración

### Fase 2 — Conectar WhatsApp (2-3 semanas)
- Registrar número en WhatsApp Business API (Meta)
- Crear webhook que recibe mensajes y llama al agente
- Enviar respuestas de vuelta al paciente

### Fase 3 — Conectar Google Calendar (1 semana)
- Reemplazar el agendamiento simulado por el calendario real del médico
- El médico ve las citas en su Google Calendar como siempre

### Fase 4 — Recordatorios y panel (2 semanas)
- Mensaje automático al paciente 24h antes de su cita
- Panel web simple para que la secretaria vea y gestione citas

---

## Preguntas frecuentes

**¿El agente puede equivocarse?**
Sí, como cualquier sistema de IA. Por eso siempre tiene la opción de escalar a una persona. El médico siempre tiene la última palabra.

**¿Los datos de los pacientes están seguros?**
En producción se implementa conforme a la Ley 1581 de Habeas Data de Colombia: consentimiento explícito, datos encriptados, sin compartir con terceros.

**¿Funciona con el número de WhatsApp que ya tenemos?**
Sí. Se migra el número existente a WhatsApp Business API sin cambiarlo.

**¿Qué pasa si el paciente escribe mal o con errores?**
El agente de IA entiende lenguaje natural, errores de ortografía y expresiones coloquiales colombianas. No necesita que el paciente escriba de forma perfecta.

**¿Se puede personalizar para otra especialidad médica?**
Sí. Cambiar los datos del consultorio, el horario, los precios y las instrucciones del agente toma menos de una hora.

---

*Prototipo construido con Streamlit + OpenAI GPT-4o. Para producción: WhatsApp Business API + Google Calendar API.*
