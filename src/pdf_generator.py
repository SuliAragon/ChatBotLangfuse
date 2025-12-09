from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from langfuse import observe

class PDFGenerator:
    def __init__(self, output_filename="documentacion_tecnica.pdf"):
        self.output_filename = output_filename
        self.styles = getSampleStyleSheet()
        self.story = []

    def add_title(self, title):
        style = self.styles["Title"]
        self.story.append(Paragraph(title, style))
        self.story.append(Spacer(1, 12))

    def add_heading(self, text, level=1):
        if level == 1:
            style = self.styles["Heading1"]
        elif level == 2:
            style = self.styles["Heading2"]
        else:
            style = self.styles["Heading3"]
        self.story.append(Paragraph(text, style))
        self.story.append(Spacer(1, 12))

    def add_paragraph(self, text):
        style = self.styles["Normal"]
        # Reemplazar saltos de línea con <br/> para ReportLab
        text = text.replace("\n", "<br/>")
        self.story.append(Paragraph(text, style))
        self.story.append(Spacer(1, 12))

    def add_code_block(self, code):
        style = ParagraphStyle(
            'Code',
            parent=self.styles['Code'],
            backColor=colors.lightgrey,
            borderColor=colors.black,
            borderWidth=1,
            borderPadding=5,
            fontSize=8,
            leading=10,
            fontName='Courier'
        )
        # Escapar caracteres especiales si es necesario y formatear
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        code = code.replace("\n", "<br/>")
        self.story.append(Paragraph(code, style))
        self.story.append(Spacer(1, 12))

    @observe(as_type="span")
    def generate(self, data):
        """
        Genera el PDF basado en un diccionario de datos estructurado.
        data = {
            "title": "Título del Documento",
            "sections": [
                {"type": "heading", "level": 1, "content": "Introducción"},
                {"type": "paragraph", "content": "Texto del párrafo..."},
                {"type": "code", "content": "print('Hola')"}
            ]
        }
        """
        try:
            # Validar que data es un diccionario
            if not isinstance(data, dict):
                raise TypeError(f"data debe ser un diccionario, recibido: {type(data)}")
            
            self.story = [] # Reiniciar historia
            
            if "title" in data:
                self.add_title(str(data["title"]))

            sections = data.get("sections", [])
            if not isinstance(sections, list):
                raise TypeError(f"sections debe ser una lista, recibido: {type(sections)}")

            for i, section in enumerate(sections):
                if not isinstance(section, dict):
                    raise TypeError(f"section {i} debe ser un diccionario, recibido: {type(section)}")
                
                section_type = section.get("type", "paragraph")
                content = section.get("content", "")
                
                if section_type == "heading":
                    level = section.get("level", 1)
                    self.add_heading(str(content), int(level))
                elif section_type == "paragraph":
                    self.add_paragraph(str(content))
                elif section_type == "code":
                    self.add_code_block(str(content))
                else:
                    print(f"⚠️ Tipo de sección desconocido: {section_type}, tratando como párrafo")
                    self.add_paragraph(str(content))
            
            # Crear directorio data/ si no existe
            import os
            os.makedirs("data", exist_ok=True)
            output_path = os.path.join("data", self.output_filename)
            
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            doc.build(self.story)
            print(f"✅ PDF generado: {output_path}")
            return output_path
        except Exception as e:
            error_msg = f"Error generando PDF: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

if __name__ == "__main__":
    # Test básico
    gen = PDFGenerator("test_doc.pdf")
    data = {
        "title": "Documentación de Prueba",
        "sections": [
            {"type": "heading", "level": 1, "content": "1. Introducción"},
            {"type": "paragraph", "content": "Este es un párrafo de prueba para verificar la generación de PDFs."},
            {"type": "heading", "level": 2, "content": "1.1 Código de Ejemplo"},
            {"type": "code", "content": "def hello():\n    print('Hello World')"}
        ]
    }
    gen.generate(data)
