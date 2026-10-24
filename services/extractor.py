import re
from rapidfuzz import process,fuzz

REGEXES=[r'\bN\d{3,5}[A-Z]{1,2}\b',r'\bX[AB]-?[A-Z]{3}\b']
DATE_RE=r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b'
ATA_RE=r'\b(\d{2})\s*[-/]\s*(\d{1,2})\b'

def norm(s):return re.sub(r'\s+',' ',str(s or '')).strip().upper()
def extract_candidate(text):
    t=norm(text); result={}
    for pat in REGEXES:
        m=re.search(pat,t)
        if m:
            ac=m.group(0)
            if ac.startswith(('XA','XB')) and '-' not in ac:ac=ac[:2]+'-'+ac[2:]
            result['ac']=ac;break
    m=re.search(DATE_RE,t)
    if m:
        d,mo,y=m.groups(); y=y[-2:]; result['reported_date']=f'{int(d):02d}-{int(mo):02d}-{y}'
    m=re.search(ATA_RE,t)
    if m:result['chapter']=int(m.group(1));result['section']=int(m.group(2))
    folios=re.findall(r'\b\d{7}\b',t)
    if folios:result['defect']=int(folios[-1])
    return result

def match_aircraft(candidate,valid):
    c=norm(candidate)
    if not c:return '',0,[]
    if c in valid:return c,100,[c]
    matches=process.extract(c,valid,scorer=fuzz.ratio,limit=5)
    best=matches[0] if matches else ('',0,0)
    return best[0],float(best[1]),[m[0] for m in matches]
