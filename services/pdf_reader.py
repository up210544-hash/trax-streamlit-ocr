import fitz
from PIL import Image
import io

def pdf_to_images(data: bytes, dpi: int=220):
    doc=fitz.open(stream=data,filetype='pdf')
    scale=dpi/72
    matrix=fitz.Matrix(scale,scale)
    pages=[]
    for i,page in enumerate(doc,start=1):
        pix=page.get_pixmap(matrix=matrix,alpha=False)
        pages.append((i,Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')))
    return pages
