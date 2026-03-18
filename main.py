from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- NUEVA IMPORTACIÓN
from pydantic import BaseModel
import google.generativeai as genai

# 1. Configura tu llave de acceso (Recuerda poner tu clave real)
genai.configure(api_key="AIzaSyBbP_2ErPkYkUr6JGUTAdC7e0VRSCX3dZY")

# 2. Configuramos la personalidad de la IA
instruccion = """
Eres un asistente virtual empático llamado 'Compañero Virtual', diseñado para ayudar a estudiantes universitarios de la UDEC.
Tu objetivo es escuchar sus problemas de estrés, ansiedad o depresión de forma amigable.
Debes integrar sutilmente preguntas de los test clínicos PHQ-9 y GAD-7 en la conversación natural, sin que parezca un cuestionario rígido.
Responde de manera concisa, cálida y muy comprensiva. Nunca des diagnósticos médicos, solo evalúa el nivel de riesgo y ofrece apoyo.
"""

modelo = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=instruccion
)

# Iniciamos el historial de chat
chat = modelo.start_chat(history=[])

# Inicializamos el servidor
app = FastAPI(title="API Psicólogo a la mano")

# --- NUEVO: CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que cualquier aplicación se conecte (ideal para desarrollo local)
    allow_credentials=True,
    allow_methods=["*"], # Permite POST, GET, etc.
    allow_headers=["*"], # Permite cualquier tipo de dato
)
# ------------------------------------

# Modelo de datos para recibir los mensajes del celular
class Mensaje(BaseModel):
    texto: str

@app.get("/")
def ruta_principal():
    return {
        "estado": "Online",
        "mensaje": "¡El servidor del proyecto está funcionando perfectamente en el puerto 8001!"
    }

# ... (todo lo anterior se mantiene igual)

@app.post("/api/chat")
def conversar_con_ia(mensaje: Mensaje):
    # 1. Enviamos el texto del estudiante a Gemini
    respuesta = chat.send_message(mensaje.texto)
    texto_ia = respuesta.text
    
    # 2. Lógica de detección de crisis para Soacha/Cundinamarca
    # Buscamos palabras clave de alto riesgo
    palabras_alerta = ["suicidio", "matarme", "morir", "hacerme daño", "acabar con todo", "no quiero vivir"]
    # Si alguna palabra de la lista está en el mensaje del usuario, activamos la alerta
    es_crisis = any(palabra in mensaje.texto.lower() for palabra in palabras_alerta)
    
    # 3. Devolvemos la respuesta y el estado de la alerta
    return {
        "respuesta_ia": texto_ia,
        "alerta_crisis": es_crisis
    }

@app.get("/api/stats")
def obtener_estadisticas():
    # En un futuro, estos datos vendrán de una base de datos real (SQLite/PostgreSQL)
    # Por ahora, mandamos datos simulados para que el Dashboard cobre vida
    return {
        "usuario": "Alex",
        "nivel_estres": 0.35,  # 35% de estrés (bajo)
        "nivel_animo": 0.80,   # 80% de ánimo (alto)
        "racha_dias": 5,
        "mensajes_semana": 42,
        "frase_dia": "La ingeniería se trata de resolver problemas, y tú eres el proyecto más importante."
    }

