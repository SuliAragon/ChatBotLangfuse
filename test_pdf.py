from src.pdf_generator import PDFGenerator
import json

# Test 1: Diccionario directo
print("Test 1: Usando diccionario Python")
gen = PDFGenerator("test_dict.pdf")
data_dict = {
    "title": "Documentación de Test",
    "sections": [
        {"type": "heading", "level": 1, "content": "Introducción"},
        {"type": "paragraph", "content": "Este es un test."},
        {"type": "code", "content": "def test():\n    pass"}
    ]
}
try:
    result = gen.generate(data_dict)
    print(f"✅ Test 1 exitoso: {result}")
except Exception as e:
    print(f"❌ Test 1 falló: {e}")

# Test 2: JSON string
print("\nTest 2: Usando JSON string")
gen2 = PDFGenerator("test_json.pdf")
data_json = json.dumps(data_dict)
try:
    data_parsed = json.loads(data_json)
    result2 = gen2.generate(data_parsed)
    print(f"✅ Test 2 exitoso: {result2}")
except Exception as e:
    print(f"❌ Test 2 falló: {e}")
