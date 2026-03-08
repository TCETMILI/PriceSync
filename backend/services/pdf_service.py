import fitz  # PyMuPDF
import os
from tempfile import mkdtemp
from pathlib import Path

def convert_pdf_to_images(pdf_path: str, output_dir: str = None, dpi: int = 300) -> list[str]:
    """
    Reads a PDF file and converts each page to a PNG image with the specified DPI.
    Returns a list of file paths to the generated images.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF belgesi bulunamadı: {pdf_path}")
        
    doc = fitz.open(pdf_path)
    if output_dir is None:
        output_dir = mkdtemp(prefix="pdf_pages_")
    
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=dpi)
        output_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(output_path)
        image_paths.append(output_path)
        
    return image_paths
