#  This code will take the file uploaded and extract its content to transform them into raw text string. will handle both .pdf and .txt files.
#  using PyMupdf 
import fitz

def extract_text(filename:str, content:bytes) -> str:
    if filename.endswith('.pdf'):
        return process_pdf(content)
    
    else:
        return process_txt(content)
    

def process_txt(content:bytes) -> str:
    try:
        return content.decode('utf-8')
# using the latin-1 encoding for crash prevention  
    except UnicodeDecodeError:
        return content.decode('latin-1')
    
def process_pdf(content:bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    collective_text=[]
    
    for page in doc:
        collective_text.append(page.get_text())
    doc.close()
    final_text= "\n".join(collective_text)
    # checking if the text was extracted or not 
    if final_text.strip() == "":
        raise ValueError("Error: no text found in the PDF file.")  
    return final_text