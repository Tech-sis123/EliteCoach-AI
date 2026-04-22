import zipfile
import xml.etree.ElementTree as ET
import os

def extract_docx_text(docx_path):
    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            xml_content = zip_ref.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # Namespace for Word documents
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # Extract all text elements
            text_elements = root.findall('.//w:t', namespaces)
            text = ' '.join([t.text for t in text_elements if t.text])
            
            return text
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"

def extract_pdf_text(pdf_path):
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
            return text
    except ImportError:
        return "PyPDF2 not installed. Cannot extract PDF text."
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

# Extract DOCX
docx_path = 'EliteCoachAI_PRD-1.docx'
if os.path.exists(docx_path):
    print("=" * 80)
    print("DOCX CONTENT: EliteCoachAI_PRD-1.docx")
    print("=" * 80)
    print(extract_docx_text(docx_path))
    print("\n")

# Extract PDF
pdf_path = 'Elite coach projectscope.pdf'
if os.path.exists(pdf_path):
    print("=" * 80)
    print("PDF CONTENT: Elite coach projectscope.pdf")
    print("=" * 80)
    print(extract_pdf_text(pdf_path))
