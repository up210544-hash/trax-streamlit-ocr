import pandas as pd
REQUIRED=['defect','defect_item','reported_date','ac','station','reported_by','chapter','section','defect_description','resolution_description','defect_type','resolved_date','status','defect_cat']
def validate(df,valid_aircraft):
    errors=[]
    for i,row in df.iterrows():
        n=i+2
        for c in REQUIRED:
            if c not in row or pd.isna(row[c]) or str(row[c]).strip()=='':errors.append(f'Fila {n}: falta {c}')
        ac=str(row.get('ac','')).strip().upper()
        if ac and ac not in valid_aircraft:errors.append(f'Fila {n}: matricula no catalogada ({ac})')
        if '[ILEGIBLE]' in str(row.get('defect_description','')).upper() or '[ILEGIBLE]' in str(row.get('resolution_description','')).upper():errors.append(f'Fila {n}: contiene [ILEGIBLE]')
        if str(row.get('defect_type','')).upper()=='MAREP' and str(row.get('reported_by','')).upper()!='TEC MANTTO':errors.append(f'Fila {n}: MAREP requiere TEC MANTTO')
        if str(row.get('defect_type','')).upper()=='PIREP' and str(row.get('reported_by','')).upper()!='PILOTO':errors.append(f'Fila {n}: PIREP requiere PILOTO')
    return errors
