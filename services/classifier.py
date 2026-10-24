import re

def classify(text,scheduled_terms):
    t=str(text or '').upper().strip()
    if any(term in f' {t} ' for term in scheduled_terms):
        return 'PROGRAMADO','Actividad programada/WO detectada',False
    if re.match(r'^\s*\(\s*M\s*\)',t):
        return 'MAREP','Prefijo (M) detectado',True
    if t:
        return 'PIREP','Discrepancia sin prefijo (M)',True
    return 'REVISAR','Texto vacio o no legible',False

def strip_m_prefix(text):
    return re.sub(r'^\s*\(\s*M\s*\)\s*','',str(text or ''),count=1,flags=re.I)
