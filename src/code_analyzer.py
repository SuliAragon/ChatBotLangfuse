import ast
from langfuse import observe

class CodeAnalyzer:
    def __init__(self):
        pass

    @observe(as_type="span")
    def analyze_python(self, code):
        """Analiza código Python usando AST para extraer estructura."""
        try:
            tree = ast.parse(code)
            structure = {
                "classes": [],
                "functions": [],
                "imports": []
            }

            # Iteración controlada para top-level
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    structure["functions"].append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "No docstring",
                        "args": [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    structure["classes"].append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "No docstring",
                        "methods": methods
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    structure["imports"].append(module)

            return structure
        except SyntaxError as e:
            return {"error": f"Error de sintaxis: {str(e)[:100]}"}
        except Exception as e:
            return {"error": f"Error al analizar: {str(e)[:100]}"}

    @observe(as_type="span")
    def analyze(self, code, language="python"):
        if language.lower() == "python":
            return self.analyze_python(code)
        else:
            # Fallback básico para otros lenguajes (podría mejorarse con regex)
            return {"info": "Análisis detallado solo disponible para Python por ahora."}

if __name__ == "__main__":
    code = """
import os

class MiClase:
    '''Docstring de clase'''
    def metodo(self):
        pass

def mi_funcion(a, b):
    '''Docstring de funcion'''
    return a + b
"""
    analyzer = CodeAnalyzer()
    print(analyzer.analyze(code))
