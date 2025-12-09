# Generador de Documentación Técnica con IA

Este proyecto utiliza LangChain, Gemini Flash y Gradio para generar documentación técnica en PDF a partir de código fuente.

## Estructura del Proyecto

- `src/`: Código fuente del chatbot.
  - `agent.py`: Lógica del agente LangChain.
  - `rag_engine.py`: Motor RAG para consultar buenas prácticas.
  - `pdf_generator.py`: Generador de PDFs con ReportLab.
  - `code_analyzer.py`: Herramienta de análisis de código.
  - `app.py`: Interfaz gráfica con Gradio.
- `knowledge_base/`: Documentos de texto con buenas prácticas de documentación.
- `requirements.txt`: Dependencias del proyecto.
- `.env`: Archivo de configuración para API Keys.

## Instrucciones de Instalación

1.  **Configurar Entorno Virtual:**
    Abre una terminal en la carpeta del proyecto (`chatbot_doc_gen`) y ejecuta:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar API Keys:**
    - Abre el archivo `.env`.
    - Pega tu `GOOGLE_API_KEY` (Gemini).
    - (Opcional) Pega tus claves de Langfuse si vas a usar monitorización.

## Ejecución

1.  **Probar la conexión:**
    ```bash
    python test_setup.py
    ```

2.  **Iniciar la Aplicación:**
    ```bash
    python -m src.app
    ```
    Abre el navegador en la URL que aparecerá (usualmente http://127.0.0.1:7860).

## Uso

1.  Pega tu código en el área de texto.
2.  Haz clic en "Generar Documentación".
3.  Espera a que el agente piense y genere el PDF.
4.  Descarga el archivo PDF resultante.
