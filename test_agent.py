from src.agent import DocumentationAgent

agent = DocumentationAgent()
sample_code = """
def suma(a, b):
    '''Suma dos números'''
    return a + b

def resta(a, b):
    return a - b
"""

print("Probando agente de documentación...")
print("=" * 50)
result = agent.run(sample_code)
print("=" * 50)
print(f"Resultado: {result}")
