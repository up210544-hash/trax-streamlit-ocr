# TRAX Bitacoras · Streamlit

Aplicacion de revision asistida para transcribir bitacoras, clasificar PIREP/MAREP, excluir mantenimiento programado y exportar el layout de 48 columnas para TRAX.

## OCR recomendado

- **Streamlit Community Cloud:** Tesseract para precarga y revision humana. Es ligero y se instala con `packages.txt`.
- **Equipo/servidor con mas memoria:** PP-OCRv5/PP-OCR para manuscrito y texto mixto. Instala `requirements-paddle.txt`.
- La transcripcion de `defect_description` y `resolution_description` debe ser literal. Nunca se debe importar texto sin revisar.

## Ejecutar localmente

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Para PP-OCR:

```powershell
pip install -r requirements-paddle.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud

1. Crea un repositorio de GitHub y sube todo el contenido de esta carpeta.
2. En Streamlit Community Cloud selecciona repositorio, rama `main` y archivo `app.py`.
3. Selecciona Python 3.12.
4. Despliega. `packages.txt` instala Tesseract y las librerias del sistema.
5. Para una prueba estable usa `requirements.txt`. PP-OCR puede superar los recursos gratuitos; para usarlo reemplaza el contenido de `requirements.txt` con el de `requirements-paddle.txt` y prueba la memoria disponible.

## Flujo

1. Carga `AVIONES.xlsx` y el formato TRAX, o usa los incluidos.
2. Carga los PDF con nombres numerados. La app ordena por el numero final.
3. Prepara paginas.
4. Selecciona una pagina, recorta la zona de texto y ejecuta OCR.
5. Transcribe literalmente cada reporte y accion correctiva.
6. Usa “Guardar y crear otro item” si una hoja tiene dos discrepancias.
7. MAREP: `(M)` / `TEC MANTTO`. PIREP: `PILOTO`.
8. Excluye Transit/Daily/Weekly/WO.
9. Corrige todos los errores y descarga Excel o TXT.

## Seguridad

Community Cloud procesa archivos fuera de la red corporativa. Usa documentos reales solo si la politica de la empresa lo permite. Para uso operacional, despliega en servidor interno.
