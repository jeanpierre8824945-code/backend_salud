# =============================================================================
# ARCHIVO: test_chat.py
# PROPÓSITO: Script de prueba de integración (smoke test) para el endpoint
#   POST /api/chat del servidor FastAPI de SERENA.
#
#   Permite diagnosticar el comportamiento del endpoint sin necesidad de
#   un cliente HTTP externo (como Postman o el frontend de la app), usando
#   únicamente la librería estándar urllib de Python (sin dependencias extra).
#
#   Este script ayuda a determinar si el endpoint:
#     - Responde con HTTP 200 y el JSON esperado (funcionamiento normal).
#     - Retorna un HTTP 422 por datos faltantes o malformados (error de validación).
#     - Lanza un HTTP 500 por un fallo en la llamada a la API de Gemini.
#     - Se queda en estado "pending" sin responder (timeout de red o servidor caído).
#
# USO: Ejecutar directamente desde la terminal con el servidor FastAPI activo:
#       python test_chat.py
#
# REQUISITO: El servidor debe estar corriendo en http://127.0.0.1:8000
# =============================================================================

import urllib.request   # Módulo estándar para realizar peticiones HTTP sin librerías externas
import json             # Módulo estándar para serializar el payload Python a formato JSON
import urllib.error     # Módulo estándar para capturar errores HTTP específicos (4xx, 5xx) y de red

# URL del endpoint de chat que se desea probar.
# Apunta al servidor local en el puerto 8000 (uvicorn por defecto).
url = "http://127.0.0.1:8000/api/chat"

# Exactamente el JSON que proporcionaste, sin el campo "correo"
# Payload de prueba mínimo: no incluye el campo "correo" que es obligatorio
# en el esquema ChatRequest de main.py. Esto activa intencionalmente una
# respuesta HTTP 422 (Unprocessable Entity) para verificar la validación.
payload = {"nombre": "Jean", "mensaje": "Hola, esto es una prueba", "tono": "empatico", "longitud": "normal"}

# Serialización del diccionario Python a bytes JSON (formato requerido por la API REST).
data = json.dumps(payload).encode('utf-8')

# Construcción del objeto Request con método POST, cuerpo JSON y cabecera Content-Type.
# La cabecera 'Content-Type: application/json' le indica a FastAPI cómo parsear el body.
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

print(f"Enviando petición POST a {url}...")

try:
    # Envío de la petición HTTP con un timeout de 15 segundos.
    # Si el servidor no responde en ese tiempo, se lanza socket.timeout → URLError.
    # El timeout permite detectar si el endpoint se queda "colgado" (estado pending).
    with urllib.request.urlopen(req, timeout=15) as response:
        # Respuesta exitosa (HTTP 2xx): se imprime el código de estado y el body decodificado.
        print(f"Código HTTP: {response.status}")
        print(f"Respuesta: {response.read().decode('utf-8')}")

except urllib.error.HTTPError as e:
    # HTTPError: el servidor respondió con un código de error HTTP (4xx o 5xx).
    # Se captura el body del error para obtener el detalle (ej: campos faltantes en 422,
    # o el mensaje de excepción en un 500 por fallo de Gemini).
    print(f"Código HTTP: {e.code}")
    print(f"Respuesta de Error: {e.read().decode('utf-8')}")

except urllib.error.URLError as e:
    # URLError: error de red o de resolución de dirección.
    # Puede ocurrir si el servidor no está corriendo, o si la URL es inaccesible.
    # Se distingue el caso de timeout del resto de errores de conexión.
    if isinstance(e.reason, TimeoutError) or "timeout" in str(e.reason).lower():
        # El endpoint no respondió dentro del límite de 15 segundos.
        # Indica que el servidor está bloqueado o en estado "pending".
        print("Resultado: El script se quedó colgado (TIMEOUT).")
    else:
        # Otro error de red: servidor apagado, puerto incorrecto, firewall, etc.
        print(f"Resultado: Error de conexión o URL inválida: {e.reason}")

except Exception as e:
    # Captura genérica para cualquier otro error inesperado no contemplado anteriormente.
    print(f"Resultado: Error inesperado: {e}")

