from dataclasses import dataclass
import pytesseract
from .preprocess import preprocess

@dataclass
class OCRResult:
    text:str
    confidence:float
    engine:str

def tesseract_ocr(image,psm=6,whitelist=None,variant='adaptive'):
    img=preprocess(image,variant)
    config=f'--oem 3 --psm {psm}'
    if whitelist:config+=f' -c tessedit_char_whitelist={whitelist}'
    data=pytesseract.image_to_data(img,lang='eng+spa',config=config,output_type=pytesseract.Output.DICT)
    words=[]; scores=[]
    for t,c in zip(data['text'],data['conf']):
        t=str(t).strip()
        try:c=float(c)
        except:c=-1
        if t:words.append(t)
        if c>=0:scores.append(c)
    return OCRResult(' '.join(words),sum(scores)/len(scores) if scores else 0.0,'Tesseract')

def paddle_available():
    try:
        import paddleocr
        return True
    except Exception:return False

def paddle_ocr(image):
    # Optional: requires requirements-paddle.txt. Kept lazy to reduce cloud memory.
    from paddleocr import PaddleOCR
    import numpy as np
    ocr=PaddleOCR(use_doc_orientation_classify=True,use_doc_unwarping=True,use_textline_orientation=True,lang='en')
    result=ocr.predict(np.array(image.convert('RGB')))
    texts=[]; scores=[]
    for page in result:
        payload=getattr(page,'json',None)
        if callable(payload): payload=payload()
        if isinstance(payload,dict):
            res=payload.get('res',payload)
            texts.extend(res.get('rec_texts',[]) or [])
            scores.extend(res.get('rec_scores',[]) or [])
    return OCRResult(' '.join(str(x) for x in texts),100*(sum(scores)/len(scores)) if scores else 0.0,'PP-OCR')
