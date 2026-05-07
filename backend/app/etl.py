"""
ETL — Admira Enterprise
Lee archivos Excel desde Google Drive usando una Service Account.
Estrategia: lista todas las carpetas sin filtro de fecha,
pero solo descarga archivos modificados recientemente.
"""

import io
import os
import re
import warnings
from datetime import datetime, timedelta, timezone

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from database import SessionLocal
from models import Reporte

warnings.filterwarnings("ignore")

FOLDER_IDS = {
    "Aldair": "1DEgdjyFfcdci7PZwJ7ix_xZ7bdWN9XsP",
    "Byan":   "1yKQ2cgFIrqg1G7kfLgswQSa5ly0ePtZ9",
}

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_PATH = os.getenv(
    "GOOGLE_CREDENTIALS_PATH",
    "/etc/secrets/google_credentials.json"
)
DIAS_ATRAS = int(os.getenv("ETL_DIAS_ATRAS", "30"))


def obtener_servicio_drive():
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def listar_archivos_recientes(service, folder_id, fecha_limite_str):
    """
    Lista recursivamente carpetas sin filtro de fecha,
    pero solo retorna archivos .xlsx modificados después de fecha_limite.
    """
    archivos = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            pageToken=page_token,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        ).execute()

        for item in response.get("files", []):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                # Recursar en todas las subcarpetas sin filtro de fecha
                archivos.extend(listar_archivos_recientes(service, item["id"], fecha_limite_str))
            elif item["name"].endswith(".xlsx") and not item["name"].startswith("~"):
                # Solo incluir archivos modificados recientemente
                modified = item.get("modifiedTime", "")
                if modified >= fecha_limite_str:
                    archivos.append(item)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return archivos


def descargar_excel(service, file_id):
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer


def limpiar_hora(texto_columna):
    texto = str(texto_columna).upper().strip()
    match = re.search(r"(\d{1,2})[:\.](\d{2})", texto)
    if match:
        hora = int(match.group(1))
        if "PM" in texto and hora != 12:
            hora += 12
        elif "AM" in texto and hora == 12:
            hora = 0
        return hora
    return None


def detectar_header_row(df_raw):
    primera_fila = str(df_raw.iloc[0, 0]).upper()
    if "REPORTE" in primera_fila or "DIA" in primera_fila or "FECHA" not in primera_fila:
        return 1
    return 0


def procesar_dataframe(df, nombre_hoja, nombre_archivo):
    registros = []
    df.columns = [str(c).strip().upper() for c in df.columns]

    col_player = next((c for c in df.columns if "PLAYER" in c), None)
    col_fecha = next((c for c in df.columns if "FECHA" in c), None)
    if not col_player or not col_fecha:
        return registros

    cols_horarios = [
        c for c in df.columns
        if (":" in c or "REPORTE" in c)
        and "FECHA" not in c
        and "DESCONEXIONES" not in c
        and "TOTAL" not in c
    ]
    if not cols_horarios:
        return registros

    df = df.dropna(subset=[col_player])

    for _, row in df.iterrows():
        fecha_raw = str(row.get(col_fecha, "")).split(" ")[0].strip()
        fecha_obj = None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y"):
            try:
                fecha_obj = datetime.strptime(fecha_raw, fmt).date()
                break
            except ValueError:
                continue
        if not fecha_obj:
            continue

        player = str(row[col_player]).strip()
        if not player or player.lower() in ("nan", "none", ""):
            continue

        for col_h in cols_horarios:
            estado = str(row.get(col_h, "")).strip()
            if estado.lower() in ("nan", "nat", "", "none"):
                continue
            hora_num = limpiar_hora(col_h)
            if hora_num is not None:
                registros.append({
                    "fecha": fecha_obj,
                    "hora_numerica": hora_num,
                    "horario_legible": col_h,
                    "player": player,
                    "estado": estado,
                    "proyecto": nombre_hoja,
                    "archivo_origen": nombre_archivo,
                })
    return registros


def procesar_archivo_excel(buffer, nombre_archivo):
    registros = []
    try:
        xls = pd.ExcelFile(buffer)
        for hoja in xls.sheet_names:
            hoja_upper = hoja.upper()
            if ("REPORTE" in hoja_upper and "PROYECTO" in hoja_upper) or \
               hoja_upper in ("RESUMEN", "SUMMARY", "REPORTE DE PROYECTOS"):
                continue
            try:
                df_raw = pd.read_excel(buffer, sheet_name=hoja, header=0, dtype=str)
                if df_raw.empty:
                    continue
                header_row = detectar_header_row(df_raw)
                df = pd.read_excel(buffer, sheet_name=hoja, header=header_row, dtype=str)
                if df.empty:
                    continue
                registros.extend(procesar_dataframe(df, hoja, nombre_archivo))
            except Exception as e:
                print(f"  ⚠️ Error en hoja '{hoja}' de {nombre_archivo}: {e}")
    except Exception as e:
        print(f"  ❌ Error leyendo {nombre_archivo}: {e}")
    return registros


def upsert_registros(db, registros):
    if not registros:
        return 0
    existentes = set(
        db.query(Reporte.fecha, Reporte.hora_numerica, Reporte.player).all()
    )
    nuevos = [
        r for r in registros
        if (r["fecha"], r["hora_numerica"], r["player"]) not in existentes
    ]
    if nuevos:
        db.bulk_insert_mappings(Reporte, nuevos)
        db.commit()
    return len(nuevos)


def procesar_todo():
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=DIAS_ATRAS)
    fecha_limite_str = fecha_limite.strftime("%Y-%m-%dT%H:%M:%S")
    print(f"🚀 INICIANDO ETL DESDE GOOGLE DRIVE (archivos desde {fecha_limite.strftime('%d/%m/%Y')})...")

    try:
        service = obtener_servicio_drive()
        print("✅ Conexión a Google Drive establecida")
    except Exception as e:
        print(f"❌ Error conectando a Google Drive: {e}")
        return

    registros_totales = []

    for responsable, folder_id in FOLDER_IDS.items():
        print(f"\n📁 Procesando carpeta: {responsable}")
        try:
            archivos = listar_archivos_recientes(service, folder_id, fecha_limite_str)
            print(f"   Encontrados: {len(archivos)} archivos")

            for archivo in archivos:
                nombre = archivo["name"]
                modified = archivo.get("modifiedTime", "")[:10]
                print(f"  📄 {nombre} (modificado: {modified})")
                try:
                    buffer = descargar_excel(service, archivo["id"])
                    registros = procesar_archivo_excel(buffer, nombre)
                    registros_totales.extend(registros)
                    print(f"     → {len(registros)} registros extraídos")
                except Exception as e:
                    print(f"     ❌ Error: {e}")
        except Exception as e:
            print(f"  ❌ Error listando carpeta {responsable}: {e}")

    print(f"\n📊 Total registros procesados: {len(registros_totales)}")
    if not registros_totales:
        print("⚠️ No se encontraron archivos modificados recientemente")
        return

    db = SessionLocal()
    try:
        print("💾 Guardando en base de datos (upsert)...")
        nuevos = upsert_registros(db, registros_totales)
        print(f"✅ ETL completado — {nuevos} registros nuevos insertados")
    except Exception as e:
        db.rollback()
        print(f"❌ Error guardando en BD: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    procesar_todo()