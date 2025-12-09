from langchain_google_genai import ChatGoogleGenerativeAI
from .rag_engine import RAGEngine
from .pdf_generator import PDFGenerator
from .code_analyzer import CodeAnalyzer
import json
import os
from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler
from langfuse import observe

load_dotenv()

# Inicializar componentes
pdf_gen = PDFGenerator()
analyzer = CodeAnalyzer()

# Intentar inicializar RAG, pero hacerlo opcional
rag_available = False
try:
    rag = RAGEngine()
    rag_available = True
except Exception as e:
    print(f"⚠️ RAG no disponible: {e}")
    rag = None


class DocumentationAgent:
    def __init__(self):
        # Inicializar Langfuse Callback Handler
        self.langfuse_handler = CallbackHandler()
        
        # Aumentar max_output_tokens para evitar cortes en JSON largos
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash", 
            temperature=0.3,
            max_output_tokens=8192,
            callbacks=[self.langfuse_handler]
        )
    
    @observe(as_type="generation")
    def run(self, code):
        """Ejecuta el flujo de generación de documentación de forma secuencial."""
        try:
            print("\n" + "="*60)
            print("🚀 Iniciando generación de documentación")
            print("="*60)
            
            # Paso 1: Analizar estructura del código
            print("\n📊 Paso 1: Analizando estructura del código...")
            # with langfuse_context.observe(name="Code Analysis", as_type="observation"):
            structure = analyzer.analyze(code, language="python")
            print(f"   ✓ Encontradas {len(structure.get('functions', []))} funciones y {len(structure.get('classes', []))} clases")
            
            # Paso 2: Consultar mejores prácticas (con fallback)
            print("\n📚 Paso 2: Consultando mejores prácticas...")
            if rag_available and rag:
                try:
                    # with langfuse_context.observe(name="RAG Retrieval", as_type="observation"):
                    docs = rag.query("python documentation best practices")
                    best_practices = "\n".join([d.page_content for d in docs[:2]])  # Top 2
                    print("   ✓ Mejores prácticas obtenidas desde RAG")
                except Exception as e:
                    print(f"   ⚠ RAG falló, usando fallback: {e}")
                    best_practices = """- Usa docstrings en formato PEP 257
- Incluye type hints
- Documenta parámetros y retornos"""
            else:
                best_practices = """- Usa docstrings en formato PEP 257
- Incluye type hints
- Documenta parámetros y retornos"""
                print("   ✓ Usando mejores prácticas predefinidas")
            
            # Paso 3: Generar contenido con LLM
            print("\n✍️ Paso 3: Generando contenido de documentación con IA...")
            prompt = f"""Eres un experto técnico. Genera documentación profesional para este código.

CÓDIGO ANALIZADO:
{json.dumps(structure, indent=2)}

MEJORES PRÁCTICAS A SEGUIR:
{best_practices}

INSTRUCCIONES:
1. Crea un título descriptivo
2. Para cada función/clase, crea una sección con:
   - Heading con el nombre
   - Párrafo explicando su propósito
   - Si tiene docstring, inclúyela
3. Incluye una sección de mejores prácticas aplicadas

FORMATO DE SALIDA (JSON):
Devuelve SOLO un JSON válido con esta estructura exacta:
{{
  "title": "Documentación de [nombre del código]",
  "sections": [
    {{"type": "heading", "level": 1, "content": "Introducción"}},
    {{"type": "paragraph", "content": "Descripción general..."}},
    {{"type": "heading", "level": 2, "content": "Función: nombre_funcion"}},
    {{"type": "paragraph", "content": "Descripción de la función..."}},
    {{"type": "heading", "level": 1, "content": "Mejores Prácticas Aplicadas"}},
    {{"type": "paragraph", "content": "Lista de mejores prácticas..."}}
  ]
}}

IMPORTANTE: Devuelve SOLO el JSON, sin texto adicional antes o después. Asegúrate de cerrar todas las llaves y comillas."""

            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Extracción robusta de JSON buscando el primer objeto JSON bien balanceado
            def extract_json(text: str) -> str:
                start = text.find('{')
                if start == -1:
                    return ''
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
                return ''

            extracted = extract_json(content)
            if extracted:
                content = extracted
            else:
                # Fallback a regex (menos robusta) si no se encontró por balanceo
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
            
            print(f"   ✓ Contenido generado ({len(content)} caracteres)")
            
            # Paso 4: Generar PDF
            print("\n📄 Paso 4: Generando PDF...")
            # Intentar parsear el JSON extraído
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                # Intentar pedir al LLM que corrija el JSON mal formado
                try:
                    repair_prompt = (
                        "El siguiente texto pretende ser un objeto JSON pero tiene errores de formato. "
                        "Devuelve SOLO el JSON válido y corregido, sin ningún comentario adicional.\n\n"
                        "TEXTO: \n" + content
                    )
                    repair_resp = self.llm.invoke(repair_prompt)
                    repaired = repair_resp.content.strip()
                    # Extraer de nuevo con el mismo método
                    extracted2 = extract_json(repaired)
                    if extracted2:
                        repaired = extracted2
                    data = json.loads(repaired)
                except Exception as e2:
                    raise json.JSONDecodeError(f"JSON repair failed: {e2}", doc=content, pos=0)
            
            # with langfuse_context.observe(name="PDF Generation", as_type="observation"):
            pdf_path = pdf_gen.generate(data)
            
            print("\n" + "="*60)
            print(f"✅ ÉXITO: Documentación generada en {pdf_path}")
            print("="*60 + "\n")
            
            return {
                "output": f"Documentación generada exitosamente en: {pdf_path}",
                "pdf_path": pdf_path
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"Error al parsear JSON del LLM: {str(e)}\nContenido recibido (inicio): {content[:500]}..."
            print(f"\n❌ {error_msg}\n")
            return {"output": error_msg, "pdf_path": None}
        except Exception as e:
            error_msg = f"Error durante la generación: {type(e).__name__}: {str(e)}"
            print(f"\n❌ {error_msg}\n")
            return {"output": error_msg, "pdf_path": None}

if __name__ == "__main__":
    # Test
    agent = DocumentationAgent()
    sample_code = """
    def suma(a, b):
        return a + b
    """
    print(agent.run(sample_code))
