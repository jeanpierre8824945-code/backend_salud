# =============================================================================
# ARCHIVO: ver_modelos.py
# PROPÓSITO: Script utilitario de diagnóstico y exploración.
#   Consulta la API de Google Generative AI para listar todos los modelos
#   disponibles que admiten el método "generateContent" (generación de texto).
#   Se usa durante el desarrollo para verificar qué modelos de Gemini están
#   accesibles con la API Key configurada, y para elegir el nombre exacto
#   del modelo antes de configurarlo en main.py.
#
# USO: Ejecutar directamente desde la terminal:
#       python ver_modelos.py
#
# NOTA DE SEGURIDAD: La API Key está hardcodeada en este archivo solo para
#   pruebas rápidas de diagnóstico. En producción, siempre debe leerse
#   desde variables de entorno (.env) para evitar exposición de credenciales.
# =============================================================================
import os
import google.generativeai as genai   # SDK oficial de Google para interactuar con los modelos Gemini

# Inicialización del cliente de Gemini con la API Key de desarrollo.
# Esta clave permite autenticarse contra la API de Google AI Studio.
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Encabezado informativo impreso en consola antes de listar los modelos.
print("Modelos disponibles para chat:")

# Itera sobre todos los modelos disponibles en la cuenta de Google AI Studio
# asociada a la API Key configurada. Filtra únicamente aquellos que soporten
# el método "generateContent", que es el utilizado por el SDK para generar
# respuestas de texto (excluyendo modelos de solo embedding o clasificación).
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)   # Imprime el nombre del modelo (ej: "models/gemini-2.5-flash")