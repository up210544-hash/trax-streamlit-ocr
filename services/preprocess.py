import cv2
import numpy as np
from PIL import Image

def pil_to_bgr(image):
    return cv2.cvtColor(np.array(image.convert('RGB')),cv2.COLOR_RGB2BGR)

def deskew(gray):
    inv=cv2.bitwise_not(gray)
    coords=np.column_stack(np.where(inv>0))
    if len(coords)<100:return gray
    angle=cv2.minAreaRect(coords)[-1]
    angle=-(90+angle) if angle<-45 else -angle
    h,w=gray.shape[:2]; M=cv2.getRotationMatrix2D((w/2,h/2),angle,1.0)
    return cv2.warpAffine(gray,M,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)

def preprocess(image,variant='adaptive'):
    bgr=pil_to_bgr(image); gray=cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY)
    gray=deskew(gray)
    gray=cv2.resize(gray,None,fx=1.5,fy=1.5,interpolation=cv2.INTER_CUBIC)
    if variant=='gray':out=cv2.equalizeHist(gray)
    elif variant=='otsu':out=cv2.threshold(cv2.GaussianBlur(gray,(3,3),0),0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    else:out=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,12)
    return Image.fromarray(out)

def crop_percent(image,left,top,right,bottom):
    w,h=image.size
    return image.crop((int(w*left),int(h*top),int(w*right),int(h*bottom)))
