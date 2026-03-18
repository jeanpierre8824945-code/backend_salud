import google.generativeai as genai

genai.configure(api_key="AIzaSyBbP_2ErPkYkUr6JGUTAdC7e0VRSCX3dZY")

print("Modelos disponibles para chat:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)