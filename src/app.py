import gradio as gr
from .agent import DocumentationAgent
from .conversation_pdf_tool import ConversationPDFGenerator
import os
from .rag_engine import RAGEngine

# Inicializar agente y herramienta de PDF
agent = DocumentationAgent()
pdf_conversation_gen = ConversationPDFGenerator()

# Inicializar RAG (opcional)
try:
    rag = RAGEngine()
except Exception as e:
    print(f"⚠️ No se pudo inicializar RAG en la interfaz: {e}")
    rag = None


def process_chat(user_message, chat_history):
    """
    Procesa mensajes del chat. Detecta si el usuario pide un PDF de la conversación
    y lo genera, o responde normalmente usando RAG para buenas prácticas.
    
    Returns:
        tuple: (messages, messages, pdf_path) donde pdf_path es None si no se generó PDF
    """
    # Normalizar el estado de chat a una lista de mensajes dict {'role','content'}
    messages = []
    if chat_history:
        for item in chat_history:
            # Si ya es un dict con role/content
            if isinstance(item, dict) and 'role' in item and 'content' in item:
                messages.append({'role': item['role'], 'content': item['content']})
            # Si es una tupla/lista (user, assistant)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                user_m, assistant_m = item
                messages.append({'role': 'user', 'content': str(user_m)})
                messages.append({'role': 'assistant', 'content': str(assistant_m)})
            else:
                # Convertir cualquier otro formato a assistant message
                messages.append({'role': 'assistant', 'content': str(item)})

    if not user_message or not user_message.strip():
        return messages, messages, None

    # Detectar si el usuario pide un PDF de la conversación
    pdf_keywords = [
        "genera pdf", "generar pdf", "exporta pdf", "exportar pdf",
        "crea pdf", "crear pdf", "resumen pdf", "pdf conversacion",
        "pdf de la conversacion", "dame un pdf", "haz un pdf",
        "genera un resumen", "exporta conversacion", "resumen de conversacion",
        "generame", "generame un pdf", "hazme un pdf", "crea un pdf",
        "resumen en pdf", "pdf con el resumen", "pdf de esta conversacion",
        "exportar a pdf", "guardar en pdf", "descargar pdf"
    ]
    
    user_lower = user_message.lower()
    wants_pdf = any(keyword in user_lower for keyword in pdf_keywords)
    
    # Debug logging
    print(f"🔍 Mensaje del usuario: '{user_message}'")
    print(f"🔍 Detección PDF: {wants_pdf}")
    print(f"🔍 Historial tiene {len(messages)} mensajes")
    
    if wants_pdf:
        # Generar PDF de la conversación
        print("📄 Usuario solicitó PDF de conversación...")
        
        if not messages:
            answer = "⚠️ Aún no tenemos conversación para exportar. ¡Hablemos un poco primero! Pregúntame sobre documentación de código, comparte código para analizar, o hazme cualquier consulta. Luego podrás pedirme que genere un PDF con el resumen de todo lo que hayamos discutido."
            pdf_path = None
        else:
            result = pdf_conversation_gen.generate_from_conversation(messages)
            
            if result["success"]:
                pdf_path = result["pdf_path"]
                # Crear respuesta más concisa con link de descarga
                answer = f"""✅ ¡PDF generado exitosamente!

📄 **Tu resumen está listo para descargar** (haz click en el botón de abajo)

El PDF incluye:
• Resumen de la conversación
• Temas discutidos y código compartido
• Mejoras y buenas prácticas sugeridas
• Conclusiones

También lo puedes encontrar en: `{pdf_path}`"""
            else:
                answer = f"❌ Hubo un error al generar el PDF: {result['message']}"
                pdf_path = None
        
        # Añadir mensajes al historial
        messages.append({'role': 'user', 'content': user_message})
        messages.append({'role': 'assistant', 'content': answer})
        return messages, messages, pdf_path
    
    # Si no pide PDF, responder normalmente con RAG
    context = ""
    try:
        if rag:
            docs = rag.query(user_message)
            context = "\n\n".join([d.page_content for d in docs[:3]])
    except Exception as e:
        print(f"⚠️ Error consultando RAG: {e}")
        # Fallback: búsqueda simple por archivos en `knowledge_base/`
        try:
            import glob
            kb_path = getattr(rag, 'knowledge_base_path', 'knowledge_base') if rag else 'knowledge_base'
            files = glob.glob(os.path.join(kb_path, '**', '*.txt'), recursive=True)
            q_tokens = [t.lower() for t in user_message.split() if len(t) > 2]
            scored = []
            for fp in files:
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        txt = f.read()
                    score = sum(txt.lower().count(tok) for tok in q_tokens)
                    scored.append((score, txt))
                except Exception:
                    continue
            scored.sort(reverse=True, key=lambda x: x[0])
            context = "\n\n".join([t for s, t in scored[:3] if s > 0])
            if not context and scored:
                context = scored[0][1][:1000]
        except Exception as e2:
            print(f"⚠️ Fallback de búsqueda simple falló: {e2}")

    # Construir prompt para el LLM
    instructions = (
        "Eres un asistente experto en documentación de código y buenas prácticas de programación. "
        "Respondes en español de forma clara, concisa y profesional. "
        "Puedes analizar código que el usuario comparta en el chat y dar recomendaciones sobre cómo documentarlo mejor. "
        "También puedes explicar tus capacidades cuando te lo pregunten. "
        "Si te piden generar un PDF de la conversación, explícales que deben pedirlo con frases como "
        "'Genera un PDF con el resumen de esta conversación' o 'Exporta esta conversación a PDF'."
    )

    prompt = f"{instructions}\n\nCONTEXTO DE LA BASE DE CONOCIMIENTO:\n{context}\n\nPREGUNTA DEL USUARIO:\n{user_message}\n\nRESPUESTA:" 

    try:
        resp = agent.llm.invoke(prompt)
        answer = resp.content.strip()
    except Exception as e:
        print(f"⚠️ Error invocando LLM para chat: {e}")
        # Fallback simple
        answer = (
            "Soy un asistente de documentación de código. Puedo ayudarte con buenas prácticas, "
            "analizar código que compartas, y generar PDFs con resúmenes de nuestras conversaciones. "
            "¿En qué puedo ayudarte?"
        )

    # Añadir ambos mensajes al historial
    messages.append({'role': 'user', 'content': user_message})
    messages.append({'role': 'assistant', 'content': answer})

    return messages, messages, None


# Diseño de la interfaz simplificada
with gr.Blocks(title="Asistente de Documentación de Código") as demo:
    gr.HTML('''
    <style>
    .header {text-align: center; margin-bottom: 20px}
    .subtitle {color: #666; text-align: center; margin-bottom: 30px}
    </style>
    ''')
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("# 🤖 Asistente de Documentación de Código")
            gr.Markdown(
                "<div class='subtitle'>Tu experto en buenas prácticas de documentación y análisis de código. "
                "Pregúntame lo que quieras o pídeme que genere un PDF con el resumen de nuestra conversación.</div>",
                elem_classes="subtitle"
            )
    
    with gr.Row():
        with gr.Column(scale=1):
            chat_bot = gr.Chatbot(
                label="Conversación",
                height=500,
                show_label=True
            )
            message = gr.Textbox(
                label="Escribe tu mensaje aquí",
                placeholder="Ej: ¿Cómo documento una función en Python? o Genera un PDF con el resumen de esta conversación",
                lines=3,
                show_label=True
            )
            with gr.Row():
                send_btn = gr.Button("Enviar", variant="primary", scale=2)
                clear_btn = gr.Button("Limpiar chat", scale=1)
            
            # Componente para descargar PDF generado
            pdf_output = gr.File(
                label="📄 Descargar PDF generado",
                visible=True,
                interactive=False
            )
            
            gr.Markdown("""
            ### 💡 ¿Qué puedo hacer?
            
            - **Consultar buenas prácticas**: Pregúntame sobre documentación de código
            - **Analizar código**: Comparte código y te daré sugerencias
            - **Generar PDFs**: Pide "Genera un PDF con el resumen de esta conversación"
            
            ### 📚 Ejemplos de preguntas:
            
            - ¿Cómo documento una función en Python?
            - Dame ejemplos de docstrings con estilo Google
            - Analiza este código: `def suma(a, b): return a + b`
            - ¿Cómo funcionas?
            - Genera un PDF con nuestra conversación
            """)
    
    # Event handlers
    send_btn.click(
        fn=process_chat,
        inputs=[message, chat_bot],
        outputs=[chat_bot, chat_bot, pdf_output]
    ).then(
        lambda: "",  # Limpiar el textbox después de enviar
        outputs=[message]
    )
    
    clear_btn.click(
        lambda: ([], [], None),
        outputs=[chat_bot, chat_bot, pdf_output]
    )
    
    message.submit(
        fn=process_chat,
        inputs=[message, chat_bot],
        outputs=[chat_bot, chat_bot, pdf_output]
    ).then(
        lambda: "",
        outputs=[message]
    )

if __name__ == "__main__":
    # Permite sobrescribir el puerto por variable de entorno `GRADIO_SERVER_PORT`
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    demo.launch(server_name="127.0.0.1", server_port=port)
