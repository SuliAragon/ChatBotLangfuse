import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def test_gemini_connection():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key == "tu_api_key_aqui":
        print("❌ ERROR: La API Key de Google no está configurada en el archivo .env")
        return

    try:
        print("🔄 Intentando conectar con Gemini Flash...")
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        response = llm.invoke("Di 'Hola Mundo' si me escuchas.")
        print(f"✅ ÉXITO: Respuesta de Gemini: {response.content}")
    except Exception as e:
        print(f"❌ ERROR: Falló la conexión con Gemini. Detalles: {e}")

if __name__ == "__main__":
    test_gemini_connection()
