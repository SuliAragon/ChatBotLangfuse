from langchain_google_genai import ChatGoogleGenerativeAI
from .pdf_generator import PDFGenerator
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class ConversationPDFGenerator:
    """
    Genera PDFs con resúmenes inteligentes de conversaciones del chatbot.
    Analiza el historial de mensajes y crea un documento con:
    - Resumen de la conversación
    - Código discutido (si aplica)
    - Mejoras sugeridas
    - Buenas prácticas aplicables
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash", 
            temperature=0.3,
            max_output_tokens=8192
        )
        self.pdf_gen = PDFGenerator()
    
    def generate_from_conversation(self, chat_history):
        """
        Genera un PDF con el resumen de la conversación.
        
        Args:
            chat_history (list): Lista de mensajes de la conversación.
                Puede ser una lista de dicts con 'role' y 'content',
                o una lista de tuplas (user_msg, assistant_msg).
        
        Returns:
            dict: Diccionario con 'success', 'message' y 'pdf_path'
        """
        try:
            # Normalizar historial a formato de texto legible
            conversation_text = self._format_conversation(chat_history)
            
            if not conversation_text.strip():
                return {
                    "success": False,
                    "message": "No hay conversación para exportar.",
                    "pdf_path": None
                }
            
            # Generar análisis inteligente con el LLM
            print("📊 Analizando conversación con IA...")
            analysis = self._analyze_conversation(conversation_text)
            
            # Generar estructura del PDF
            print("📄 Generando estructura del PDF...")
            pdf_data = self._create_pdf_structure(analysis)
            
            # Generar PDF con nombre único basado en timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.pdf_gen.output_filename = f"conversacion_resumen_{timestamp}.pdf"
            pdf_path = self.pdf_gen.generate(pdf_data)
            
            return {
                "success": True,
                "message": f"PDF generado exitosamente: {pdf_path}",
                "pdf_path": pdf_path
            }
            
        except Exception as e:
            error_msg = f"Error generando PDF de conversación: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "pdf_path": None
            }
    
    def _format_conversation(self, chat_history):
        """Convierte el historial de chat a texto legible."""
        formatted = []
        
        if not chat_history:
            return ""
        
        for item in chat_history:
            # Si es un dict con role/content
            if isinstance(item, dict) and 'role' in item and 'content' in item:
                role = "Usuario" if item['role'] == 'user' else "Asistente"
                formatted.append(f"{role}: {item['content']}")
            # Si es una tupla/lista (user, assistant)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                user_msg, assistant_msg = item
                formatted.append(f"Usuario: {user_msg}")
                formatted.append(f"Asistente: {assistant_msg}")
            else:
                # Formato desconocido, convertir a string
                formatted.append(f"Mensaje: {str(item)}")
        
        return "\n\n".join(formatted)
    
    def _analyze_conversation(self, conversation_text):
        """Usa el LLM para analizar la conversación y extraer información clave."""
        
        prompt = f"""Eres un asistente experto en análisis de conversaciones técnicas sobre programación.

CONVERSACIÓN A ANALIZAR:
{conversation_text}

INSTRUCCIONES:
Analiza la conversación y genera un resumen estructurado en formato JSON con los siguientes campos:

1. "resumen_general": Un párrafo conciso (2-3 frases) sobre el tema principal de la conversación
2. "temas_discutidos": Lista de los temas principales discutidos (máximo 5)
3. "codigo_compartido": Lista de fragmentos de código mencionados o discutidos (si los hay). Cada elemento debe tener "descripcion" y "codigo"
4. "mejoras_sugeridas": Lista de mejoras o recomendaciones que se mencionaron
5. "buenas_practicas": Lista de buenas prácticas de programación discutidas o aplicables
6. "conclusiones": Conclusión final de la conversación (1-2 frases)

FORMATO DE SALIDA (JSON):
Devuelve SOLO un JSON válido con esta estructura exacta:
{{
  "resumen_general": "Texto del resumen...",
  "temas_discutidos": ["Tema 1", "Tema 2", ...],
  "codigo_compartido": [
    {{"descripcion": "Función de ejemplo", "codigo": "def ejemplo():\\n    pass"}},
    ...
  ],
  "mejoras_sugeridas": ["Mejora 1", "Mejora 2", ...],
  "buenas_practicas": ["Práctica 1", "Práctica 2", ...],
  "conclusiones": "Texto de conclusión..."
}}

IMPORTANTE: Si alguna sección no aplica (por ejemplo, no se compartió código), usa una lista vacía [] o string vacío "".
Devuelve SOLO el JSON, sin texto adicional antes o después."""

        response = self.llm.invoke(prompt)
        content = response.content.strip()
        
        # Extraer JSON (reusar lógica similar a agent.py)
        json_content = self._extract_json(content)
        
        try:
            analysis = json.loads(json_content)
            return analysis
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parseando JSON del análisis: {e}")
            # Fallback: estructura básica
            return {
                "resumen_general": "Conversación sobre programación y buenas prácticas.",
                "temas_discutidos": ["Programación", "Buenas prácticas"],
                "codigo_compartido": [],
                "mejoras_sugeridas": [],
                "buenas_practicas": [],
                "conclusiones": "Conversación técnica completada."
            }
    
    def _extract_json(self, text):
        """Extrae el primer objeto JSON bien balanceado del texto."""
        start = text.find('{')
        if start == -1:
            return '{}'
        
        depth = 0
        in_string = False
        escape = False
        
        for i in range(start, len(text)):
            ch = text[i]
            
            if ch == '"' and not escape:
                in_string = not in_string
            
            if ch == '\\' and not escape:
                escape = True
                continue
            else:
                escape = False
            
            if not in_string:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
        
        return text[start:] if depth > 0 else '{}'
    
    def _create_pdf_structure(self, analysis):
        """Crea la estructura de datos para el PDFGenerator."""
        
        sections = []
        
        # Título
        title = "Resumen de Conversación - Asistente de Documentación"
        
        # Fecha
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        sections.append({
            "type": "paragraph",
            "content": f"Fecha de generación: {fecha}"
        })
        sections.append({"type": "paragraph", "content": " "})  # Espacio
        
        # Resumen General
        sections.append({"type": "heading", "level": 1, "content": "Resumen General"})
        sections.append({
            "type": "paragraph",
            "content": analysis.get("resumen_general", "No disponible.")
        })
        
        # Temas Discutidos
        temas = analysis.get("temas_discutidos", [])
        if temas:
            sections.append({"type": "heading", "level": 1, "content": "Temas Discutidos"})
            temas_text = "\n".join([f"• {tema}" for tema in temas])
            sections.append({"type": "paragraph", "content": temas_text})
        
        # Código Compartido
        codigo_items = analysis.get("codigo_compartido", [])
        if codigo_items:
            sections.append({"type": "heading", "level": 1, "content": "Código Discutido"})
            for item in codigo_items:
                desc = item.get("descripcion", "Código")
                codigo = item.get("codigo", "")
                sections.append({"type": "heading", "level": 2, "content": desc})
                sections.append({"type": "code", "content": codigo})
        
        # Mejoras Sugeridas
        mejoras = analysis.get("mejoras_sugeridas", [])
        if mejoras:
            sections.append({"type": "heading", "level": 1, "content": "Mejoras Sugeridas"})
            mejoras_text = "\n".join([f"• {mejora}" for mejora in mejoras])
            sections.append({"type": "paragraph", "content": mejoras_text})
        
        # Buenas Prácticas
        practicas = analysis.get("buenas_practicas", [])
        if practicas:
            sections.append({"type": "heading", "level": 1, "content": "Buenas Prácticas Aplicables"})
            practicas_text = "\n".join([f"• {practica}" for practica in practicas])
            sections.append({"type": "paragraph", "content": practicas_text})
        
        # Conclusiones
        sections.append({"type": "heading", "level": 1, "content": "Conclusiones"})
        sections.append({
            "type": "paragraph",
            "content": analysis.get("conclusiones", "Conversación finalizada.")
        })
        
        return {
            "title": title,
            "sections": sections
        }


if __name__ == "__main__":
    # Test básico
    test_history = [
        {"role": "user", "content": "¿Cómo documento una función en Python?"},
        {"role": "assistant", "content": "Usa docstrings con comillas triples. Ejemplo:\ndef suma(a, b):\n    \"\"\"Suma dos números.\"\"\"\n    return a + b"}
    ]
    
    gen = ConversationPDFGenerator()
    result = gen.generate_from_conversation(test_history)
    print(result)
