from src.conversation_pdf_tool import ConversationPDFGenerator

# Test manual
gen = ConversationPDFGenerator()

# Simular conversación
test_history = [
    {"role": "user", "content": "Hola, quiero mejorar la documentación de mi código"},
    {"role": "assistant", "content": "¡Hola! Puedo ayudarte con eso. ¿Qué tipo de código estás documentando?"},
    {"role": "user", "content": "Es código Python, tengo funciones sin docstrings"},
    {"role": "assistant", "content": "Para Python, deberías usar docstrings siguiendo PEP 257. Aquí hay un ejemplo:\n\ndef suma(a, b):\n    '''Suma dos números.\n    \n    Args:\n        a: Primer número\n        b: Segundo número\n    \n    Returns:\n        La suma de a y b\n    '''\n    return a + b"},
    {"role": "user", "content": "Genera un PDF con el resumen de esta conversación"}
]

print("Probando generación de PDF...")
result = gen.generate_from_conversation(test_history)

print("\nResultado:")
print(f"  Success: {result['success']}")
print(f"  Message: {result['message']}")
print(f"  PDF Path: {result['pdf_path']}")
