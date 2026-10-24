from pathlib import Path
import io,json,re
import pandas as pd
import streamlit as st
from PIL import Image
from services.file_order import numeric_file_key
from services.pdf_reader import pdf_to_images
from services.preprocess import crop_percent
from services.ocr_engine import tesseract_ocr,paddle_ocr,paddle_available
from services.extractor import extract_candidate,match_aircraft,norm
from services.classifier import classify,strip_m_prefix
from services.validator import validate
from services.exporter import export_xlsx,export_tsv

BASE=Path(__file__).parent
st.set_page_config(page_title='TRAX Bitacoras',page_icon='✈️',layout='wide')

def load_json(name):
    return json.loads((BASE/'configuration'/name).read_text(encoding='utf-8'))
def load_aircraft(upload=None):
    p=upload if upload else BASE/'templates'/'AVIONES.xlsx'
    df=pd.read_excel(p,engine='openpyxl')
    col='TAIL' if 'TAIL' in df.columns else df.columns[0]
    return sorted({norm(x) for x in df[col].dropna()})
def template_path(upload):
    if not upload:return str(BASE/'templates'/'formato_reportes.xlsx')
    path='/tmp/formato_reportes.xlsx';open(path,'wb').write(upload.getvalue());return path

def blank_record(source,page,full_text,valid,defaults,scheduled):
    cand=extract_candidate(full_text)
    ac=cand.get('ac','');best,score,choices=match_aircraft(ac,valid) if ac else ('',0,[])
    return {'incluir':False,'archivo':source,'pagina':page,'clasificacion':'REVISAR','motivo':'Pendiente de transcripcion literal','confianza_ocr':0.0,'alternativas_matricula':', '.join(choices),
    'wo':'','defect':cand.get('defect',''),'defect_item':1,'reported_hours':defaults['reported_hours'],'reported_minutes':defaults['reported_minutes'],'reported_date':cand.get('reported_date',''),'ac':best if score>=85 else ac,'station':'','reported_by':'PILOTO','chapter':cand.get('chapter',''),'section':cand.get('section',''),'reference_task_card':'','rii':'','defect_description':'','resolution_description':'','defect_type':'PIREP','reference_sequence_number':'','resolved_by':defaults['resolved_by'],'resolved_date':cand.get('reported_date',''),'resolved_hours':defaults['resolved_hours'],'resolved_minutes':defaults['resolved_minutes'],'reference':'','status':defaults['status'],'defer':'','defer_by':'','defer_date':'','defer_to_date':'','mel':'','name_1':'','mel_number':'','defer_category':'','schedule_hours':'','schedule_cycles':'','schedule_days':'','defer_to_hour':'','defer_to_minute':'','plan_defect':'','repeat_number':'','completed_number':'','defer_hour':'','defer_minute':'','defer_notes':'','linking_defect':'','linking_defect_item':'','defect_cat':defaults['defect_cat'],'asc_code':'','rii_inspection_by':'','inspected_by':'','ocr_pagina':full_text}

def sync_rules(df,scheduled):
    out=df.copy()
    for i,row in out.iterrows():
        cls,reason,inc=classify(row.get('defect_description',''),scheduled)
        out.at[i,'clasificacion']=cls;out.at[i,'motivo']=reason
        if cls=='MAREP':
            out.at[i,'defect_type']='MAREP';out.at[i,'reported_by']='TEC MANTTO';out.at[i,'defect_description']=strip_m_prefix(row.get('defect_description',''))
        elif cls=='PIREP':out.at[i,'defect_type']='PIREP';out.at[i,'reported_by']='PILOTO'
        elif cls=='PROGRAMADO':out.at[i,'incluir']=False
    return out

st.title('TRAX · Extractor y revisor de bitacoras')
st.warning('El OCR propone texto. defect_description y resolution_description deben compararse literalmente contra la imagen antes de exportar.')
defaults=load_json('defaults.json');scheduled=load_json('scheduled_terms.json')
with st.sidebar:
    st.header('Archivos maestros')
    aircraft_file=st.file_uploader('AVIONES.xlsx',type='xlsx',key='ac')
    template_file=st.file_uploader('Formato TRAX.xlsx',type='xlsx',key='tpl')
    dpi=st.slider('DPI de PDF',180,300,220,20)
    engine=st.radio('OCR',['Tesseract','PP-OCR (si esta instalado)'])
    if engine.startswith('PP') and not paddle_available():st.error('PP-OCR no esta instalado. Usa requirements-paddle.txt o selecciona Tesseract.')
valid=load_aircraft(aircraft_file);tpl=template_path(template_file)
uploads=st.file_uploader('Bitacoras PDF, JPG o PNG',type=['pdf','png','jpg','jpeg'],accept_multiple_files=True)
if uploads:
    ordered=sorted(uploads,key=lambda x:numeric_file_key(x.name))
    st.caption('Orden: '+' → '.join(x.name for x in ordered))
    if st.button('Preparar paginas',type='primary'):
        pages=[];records=[]
        bar=st.progress(0);total=len(ordered)
        for ix,up in enumerate(ordered):
            imgs=pdf_to_images(up.getvalue(),dpi) if up.name.lower().endswith('.pdf') else [(1,Image.open(io.BytesIO(up.getvalue())).convert('RGB'))]
            for pnum,img in imgs:
                low=img.copy();low.thumbnail((1800,1800))
                result=paddle_ocr(low) if engine.startswith('PP') and paddle_available() else tesseract_ocr(low,psm=6,variant='gray')
                pages.append({'archivo':up.name,'pagina':pnum,'imagen':img,'ocr':result.text,'confianza':result.confidence})
                records.append(blank_record(up.name,pnum,result.text,valid,defaults,scheduled))
            bar.progress((ix+1)/total)
        st.session_state.pages=pages;st.session_state.records=pd.DataFrame(records);st.session_state.selected_page=0

if 'pages' in st.session_state and st.session_state.pages:
    pages=st.session_state.pages
    names=[f"{p['archivo']} · pagina {p['pagina']}" for p in pages]
    idx=st.selectbox('Pagina para revisar',range(len(names)),format_func=lambda i:names[i],key='selected_page')
    page=pages[idx]
    left,right=st.columns([1.05,1])
    with left:
        st.image(page['imagen'],caption=names[idx],use_container_width=True)
        st.caption(f"Confianza OCR de pagina: {page['confianza']:.1f}%")
        st.text_area('OCR bruto de pagina',page['ocr'],height=190,disabled=True)
        st.subheader('OCR de recorte')
        c1,c2,c3,c4=st.columns(4)
        L=c1.number_input('Izq %',0,95,0)/100;T=c2.number_input('Arriba %',0,95,35)/100;R=c3.number_input('Der %',5,100,100)/100;B=c4.number_input('Abajo %',5,100,80)/100
        if L<R and T<B:
            crop=crop_percent(page['imagen'],L,T,R,B);st.image(crop,use_container_width=True)
            if st.button('Leer recorte'):
                rr=paddle_ocr(crop) if engine.startswith('PP') and paddle_available() else tesseract_ocr(crop,psm=6,variant='adaptive')
                st.session_state.crop_text=rr.text;st.session_state.crop_conf=rr.confidence
            if 'crop_text' in st.session_state:
                st.text_area(f"Texto del recorte ({st.session_state.get('crop_conf',0):.1f}%)",st.session_state.crop_text,height=130)
    with right:
        st.subheader('Transcripcion literal')
        df=st.session_state.records
        current=df[(df.archivo==page['archivo'])&(df.pagina==page['pagina'])]
        if current.empty:
            st.info('No hay item para esta pagina.')
        else:
            ri=current.index[0]
            with st.form('edit_form'):
                a,b,c=st.columns(3)
                defect=a.text_input('Folio',str(df.at[ri,'defect'] or ''));item=b.number_input('Item',1,20,int(df.at[ri,'defect_item'] or 1));ac=c.text_input('Matricula',str(df.at[ri,'ac'] or '')).upper()
                a,b,c=st.columns(3);date=a.text_input('Fecha DD-MM-AA',str(df.at[ri,'reported_date'] or ''));station=b.text_input('Estacion',str(df.at[ri,'station'] or '')).upper();dtype=c.selectbox('Tipo',['PIREP','MAREP','PROGRAMADO'],index=['PIREP','MAREP','PROGRAMADO'].index(df.at[ri,'defect_type'] if df.at[ri,'defect_type'] in ['PIREP','MAREP','PROGRAMADO'] else 'PIREP'))
                a,b=st.columns(2);ch=a.text_input('Chapter',str(df.at[ri,'chapter'] or ''));sec=b.text_input('Section',str(df.at[ri,'section'] or ''))
                desc=st.text_area('DEFECT DESCRIPTION · literal y completo',str(df.at[ri,'defect_description'] or ''),height=145)
                resolution=st.text_area('RESOLUTION DESCRIPTION · literal y completo',str(df.at[ri,'resolution_description'] or ''),height=180)
                include=st.checkbox('Incluir en exportacion',value=bool(df.at[ri,'incluir']))
                col1,col2=st.columns(2);save=col1.form_submit_button('Guardar item',type='primary');duplicate=col2.form_submit_button('Guardar y crear otro item')
            if save or duplicate:
                vals={'defect':defect,'defect_item':item,'ac':ac,'reported_date':date,'resolved_date':date,'station':station,'chapter':ch,'section':sec,'defect_description':desc,'resolution_description':resolution,'defect_type':dtype,'reported_by':'TEC MANTTO' if dtype=='MAREP' else 'PILOTO','incluir':include}
                for k,v in vals.items():df.at[ri,k]=v
                if duplicate:
                    new=df.loc[ri].copy();new['defect_item']=item+1;new['defect_description']='';new['resolution_description']='';new['incluir']=False
                    st.session_state.records=pd.concat([df,pd.DataFrame([new])],ignore_index=True)
                else:st.session_state.records=df
                st.rerun()

    st.divider();st.subheader('Consolidado editable')
    edited=st.data_editor(st.session_state.records,use_container_width=True,hide_index=True,num_rows='dynamic',column_config={'defect_description':st.column_config.TextColumn(width='large'),'resolution_description':st.column_config.TextColumn(width='large'),'ocr_pagina':st.column_config.TextColumn(disabled=True,width='small')})
    edited=sync_rules(edited,scheduled);st.session_state.records=edited
    chosen=edited[edited['incluir']==True].reset_index(drop=True)
    errors=validate(chosen,valid) if not chosen.empty else ['No hay registros seleccionados']
    a,b,c,d=st.columns(4);a.metric('Paginas',len(pages));b.metric('Items',len(edited));c.metric('Seleccionados',len(chosen));d.metric('Errores',len(errors))
    if errors:
        with st.expander('Pendientes antes de exportar',expanded=True):
            for e in errors:st.warning(e)
    xlsx=export_xlsx(chosen,tpl);tsv=export_tsv(chosen,tpl)
    c1,c2=st.columns(2)
    c1.download_button('Descargar Excel TRAX',xlsx,'DEFECT_REPORTS_TRAX.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',disabled=bool(errors))
    c2.download_button('Descargar TXT TRAX',tsv,'DEFECT_REPORTS_TRAX.txt','text/tab-separated-values',disabled=bool(errors))
else:
    st.info('Carga los PDF, confirma el orden y pulsa Preparar paginas.')
