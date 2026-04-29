import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

# --- IMPORTACIONES PARA LA BASE DE DATOS ---
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# ==========================================
# CONFIGURACIÓN DE GEMINI IA
# ==========================================
api_key_env = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key_env)


# ==========================================
# CONFIGURACIÓN DE FASTAPI Y CORS
# ==========================================
app = FastAPI(title="API Psicólogo a la mano")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# ==========================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ==========================================
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./serena.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# MODELOS DE LA BASE DE DATOS (Las Tablas Reales)
# ==========================================
class UsuarioDB(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    correo = Column(String, unique=True, index=True)
    password = Column(String) 
    
    sesiones_completadas = Column(Integer, default=0)
    dias_activos = Column(Integer, default=1)
    bienestar_porcentaje = Column(Integer, default=100)

class CitaDB(Base):
    __tablename__ = "citas"
    
    id = Column(Integer, primary_key=True, index=True)
    correo_estudiante = Column(String, index=True)
    especialista_id = Column(String, index=True)
    fecha = Column(String, index=True) 
    hora = Column(String) 

# ¡AQUÍ ESTÁ LA MAGIA! La orden de crear las tablas ahora está al final de todos los modelos.
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# MODELOS PYDANTIC (Para recibir datos del frontend)
# ==========================================
class ChatRequest(BaseModel):
    mensaje: str
    correo: str
    nombre: str = "Estudiante"
    tono: str = "empatico"
    longitud: str = "normal"
    historial: list = []

class UsuarioRegistro(BaseModel):
    nombre: str
    correo: str
    password: str

class UsuarioLogin(BaseModel):
    correo: str
    password: str

class ResultadoTest(BaseModel):
    correo: str
    puntaje: int
    test_id: str

class CitaRequest(BaseModel):
    correo_estudiante: str
    especialista_id: str
    fecha: str
    hora: str





# ==========================================
# RUTAS DE LA APLICACIÓN
# ==========================================
@app.get("/")
def ruta_principal():
    return {
        "estado": "Online",
        "mensaje": "¡El servidor del proyecto está funcionando perfectamente en el puerto 8001!"
    }

@app.post("/api/registro")
def registrar_usuario(usuario: UsuarioRegistro, db: Session = Depends(get_db)):
    usuario_existente = db.query(UsuarioDB).filter(UsuarioDB.correo == usuario.correo).first()
    if usuario_existente:
        return {"exito": False, "mensaje": "El correo ya está registrado en el sistema."}
    
    nuevo_usuario = UsuarioDB(
        nombre=usuario.nombre,
        correo=usuario.correo,
        password=usuario.password
    )
    
    db.add(nuevo_usuario)
    db.commit()
    return {"exito": True, "mensaje": "¡Cuenta creada con éxito!"}

@app.post("/api/login")
def iniciar_sesion(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    user_db = db.query(UsuarioDB).filter(UsuarioDB.correo == usuario.correo).first()
    
    if not user_db or user_db.password != usuario.password:
        return {"exito": False, "mensaje": "Correo o contraseña incorrectos."}
    
    return {
        "exito": True, 
        "mensaje": f"Bienvenido de nuevo, {user_db.nombre}",
        "datos_usuario": {
            "nombre": user_db.nombre,
            "correo": user_db.correo,
            "sesiones": user_db.sesiones_completadas,
            "dias_activos": user_db.dias_activos,
            "bienestar": f"{user_db.bienestar_porcentaje}%"
        }
    }

@app.post("/api/guardar-test")
def guardar_resultado_test(datos: ResultadoTest, db: Session = Depends(get_db)):
    user_db = db.query(UsuarioDB).filter(UsuarioDB.correo == datos.correo).first()
    if not user_db:
        return {"exito": False, "mensaje": "Usuario no encontrado"}

    user_db.sesiones_completadas += 1
    impacto = datos.puntaje * 2 
    nuevo_bienestar = 100 - impacto
    
    if nuevo_bienestar < 10: 
        nuevo_bienestar = 10 
        
    user_db.bienestar_porcentaje = nuevo_bienestar
    db.commit()

    return {
        "exito": True,
        "nuevas_metricas": {
            "sesiones": user_db.sesiones_completadas,
            "bienestar": f"{user_db.bienestar_porcentaje}%"
        }
    }

@app.get("/api/citas-ocupadas")
def obtener_citas_ocupadas(especialista_id: str, fecha: str, db: Session = Depends(get_db)):
    citas = db.query(CitaDB).filter(
        CitaDB.especialista_id == especialista_id,
        CitaDB.fecha == fecha
    ).all()
    
    horas_ocupadas = [cita.hora for cita in citas]
    return {"horas_ocupadas": horas_ocupadas}

@app.post("/api/agendar-cita")
def agendar_cita(cita: CitaRequest, db: Session = Depends(get_db)):
    existente = db.query(CitaDB).filter(
        CitaDB.especialista_id == cita.especialista_id,
        CitaDB.fecha == cita.fecha,
        CitaDB.hora == cita.hora
    ).first()
    
    if existente:
        return {"exito": False, "mensaje": "Lo sentimos, este horario acaba de ser ocupado."}
    
    nueva_cita = CitaDB(
        correo_estudiante=cita.correo_estudiante,
        especialista_id=cita.especialista_id,
        fecha=cita.fecha,
        hora=cita.hora
    )
    db.add(nueva_cita)
    db.commit()
    
    return {"exito": True, "mensaje": "Cita agendada correctamente."}

@app.post("/api/chat")
def conversar_con_ia(request: ChatRequest):
    # 2. Refinamos la instrucción para que NO sea un robot
    instruccion_base = f"""
    Eres SERENA, una IA de apoyo emocional para la UDEC. Hablas con {request.nombre}.
    
    REGLAS DE ORO PARA NO SER UN ROBOT:
    1. NO SALUDES en cada mensaje. Si ya saludaste en el historial, ve directo a la charla.
    2. Habla de forma natural, como un amigo o mentor, NO como un cuestionario médico.
    3. Usa el nombre del usuario solo una vez cada tanto, no en todas las frases.
    4. Integra las preguntas de PHQ-9 o GAD-7 de forma orgánica. Si el usuario dice "tengo muchas tareas", no preguntes "dirías que te has sentido así 2 semanas", mejor di: "Uff, la carga académica en la UDEC es pesada. ¿Eso te ha quitado el sueño o las ganas de hacer otras cosas?"
    """

    modos_tono = {
        "empatico": "Sé muy humano y cercano. Usa lenguaje de validación emocional.",
        "directo": "Sé práctico y breve. Menos charla, más soluciones.",
        "motivador": "Dale energía al estudiante, recuérdale que es capaz."
    }

    prompt_final = f"{instruccion_base}\nPersonalidad: {modos_tono.get(request.tono, 'empatico')}"

    modelo_udec = genai.GenerativeModel(
        'gemini-2.5-flash',
        system_instruction=prompt_final
    )

    # 3. CONSTRUIMOS EL CHAT CON MEMORIA RESTRUCTURADA
    # Convertimos tu historial del celular al formato que entiende Gemini
    history_gemini = []
    for m in request.historial:
        role = "user" if m['emisor'] == 'user' else "model"
        history_gemini.append({"role": role, "parts": [m['texto']]})

    # Iniciamos el chat con el pasado de la conversación
    chat_sesion = modelo_udec.start_chat(history=history_gemini)

    try:
        # Enviamos el mensaje dentro del contexto del chat
        respuesta = chat_sesion.send_message(request.mensaje)
        
        # Lógica de crisis sencilla
        es_crisis = any(p in request.mensaje.lower() for p in ["suicidio", "matarme", "morir"])
        
        return {
            "respuesta_ia": respuesta.text,
            "alerta_crisis": es_crisis
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"respuesta_ia": "Se me cruzaron los cables, ¿me repites?", "alerta_crisis": False}

@app.get("/api/stats")
def obtener_estadisticas():
    return {
        "usuario": "Alex",
        "nivel_estres": 0.35,  
        "nivel_animo": 0.80,   
        "racha_dias": 5,
        "mensajes_semana": 42,
        "frase_dia": "La ingeniería se trata de resolver problemas, y tú eres el proyecto más importante."
    }



@app.get("/api/mis-citas/{correo}")
def obtener_mis_citas(correo: str, db: Session = Depends(get_db)):
    # Buscamos todas las citas agendadas bajo el correo del estudiante
    citas = db.query(CitaDB).filter(CitaDB.correo_estudiante == correo).all()
    
    # Formateamos la lista para enviarla al celular
    citas_formateadas = [
        {"especialista_id": c.especialista_id, "fecha": c.fecha, "hora": c.hora} 
        for c in citas
    ]
    
    return {"citas": citas_formateadas}



@app.delete("/api/eliminar-usuario/{correo}")
def eliminar_usuario_completo(correo: str, db: Session = Depends(get_db)):
    # 1. Buscamos al usuario
    user = db.query(UsuarioDB).filter(UsuarioDB.correo == correo).first()
    
    if not user:
        return {"exito": False, "mensaje": "Usuario no encontrado en la base de datos."}

    try:
        # 2. Borramos primero sus citas para no dejar datos huérfanos
        db.query(CitaDB).filter(CitaDB.correo_estudiante == correo).delete()
        
        # 3. Borramos al usuario
        db.delete(user)
        
        # 4. Confirmamos los cambios en el archivo serena.db
        db.commit()
        return {"exito": True, "mensaje": "Cuenta y datos eliminados correctamente."}
    except Exception as e:
        db.rollback()
        return {"exito": False, "mensaje": f"Error al eliminar: {str(e)}"}
    


@app.get("/api/historial-completo/{correo}")
def obtener_historial_real(correo: str, db: Session = Depends(get_db)):
    # 1. Traemos las citas de la base de datos
    citas = db.query(CitaDB).filter(CitaDB.correo_estudiante == correo).all()
    
    historial = []
    
    # 2. Convertimos las citas en "eventos" de historial
    for cita in citas:
        # Buscamos el nombre del doctor para que no salga solo el ID
        # (Aquí podrías hacer un join si tienes tabla de doctores, 
        # o usar un diccionario simple por ahora)
        historial.append({
            "fecha": cita.fecha,
            "tipo": "Cita Médica",
            "detalle": f"Sesión agendada para las {cita.hora}",
            "icono": "calendar-outline"
        })
    
    # 3. Ordenamos por fecha (opcional, para que lo más nuevo salga arriba)
    historial.sort(key=lambda x: x['fecha'], reverse=True)
    
    return {"historial": historial}


# 1. Modelo de datos para los recursos
class Recurso(BaseModel):
    id: int
    categoria: str # 'video', 'lectura', 'tip'
    titulo: str
    descripcion: str
    enlace: str = "" # Para YouTube o PDF
    icono: str

@app.get("/api/recursos")
def obtener_recursos():
    # Aquí puedes añadir los que quieras
    return [
        # CATEGORÍA: VIDEOS
        {
            "id": 1, "categoria": "video", 
            "titulo": "Meditación 5 Minutos", 
            "descripcion": "Ideal para antes de un parcial en la UDEC.",
            "enlace": "https://www.youtube.com/watch?v=z6X5oEIg6Ak",
            "icono": "videocam-outline"
        },
        # CATEGORÍA: LECTURAS / FRASES
        {
            "id": 2, "categoria": "lectura", 
            "titulo": "El poder del 'Todavía'", 
            "descripcion": "Frase: 'No es que no sepas, es que NO sabes TODAVÍA'.",
            "enlace": "",
            "icono": "book-outline"
        },
        # CATEGORÍA: TIPS
        {
            "id": 3, "categoria": "tip", 
            "titulo": "Técnica Pomodoro", 
            "descripcion": "Estudia 25 min, descansa 5. Evita el agotamiento académico.",
            "enlace": "",
            "icono": "bulb-outline"
        }
    ]