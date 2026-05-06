"""
ETL — Admira Enterprise
Lee archivos Excel desde Google Drive usando una Service Account.
Reemplaza el ETL local que dependía de C:\\Users\\ADmira01\\...

Estructura esperada en Drive:
REPORTES ALDAIR Y BRYAN/
├── Aldair/  → headers en fila 1, datos desde fila 2
│   └── 2026/MAYO/MONITOREO X_MES.xlsx
└── Byan/    → headers en fila 2, datos desde fila 3
    └── 2026/MAYO/MONITOREO ADMIRA X.X.XX.xlsx
"""

import io
import os
import re
import warnings
from datetime import datetime

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from database import SessionLocal
from models import Reporte

warnings.filterwarnings("ignore")

# ==========================================
# CONFIGURACIÓN
# ==========================================
FOLDER_ID_RAIZ = "15T3PU5K48QpzNmM7yAKoaUIZPQBuHYcZ"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Render guarda los Secret Files en /etc/secrets/
CREDENTIALS_PATH = os.getenv(
    "GOOGLE_CREDENTIALS_PATH",
    "/etc/secrets/google_credentials.json"
)


def obtener_servicio_drive():
    """Crea y retorna el cliente autenticado de Google Drive."""
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def listar_archivos_excel(service, folder_id):
    """Lista recursivamente todos los .xlsx dentro de una carpeta de Drive."""
    archivos = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            pageToken=page_token
        ).execute()

        for item in response.get("files", []):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                # Recursión en subcarpetas
                archivos.extend(listar_archivos_excel(service, item["id"]))
            elif item["name"].endswith(".xlsx") and not item["name"].startswith("~"):
                archivos.append(item)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return archivos


def descargar_excel(service, file_id):
    """Descarga un archivo xlsx de Drive y lo retorna como BytesIO."""
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer


def limpiar_hora(texto_columna):
    """Extrae la hora numérica del nombre de la columna (ej: 'REPORTE 13:00 HRS' → 13)."""
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
    """
    Detecta si los headers están en fila 0 (Aldair) o fila 1 (Bryan).
    Bryan tiene una fila de título en la fila 0 antes de los headers reales.
    """
    primera_fila = str(df_raw.iloc[0, 0]).upper()
    if "REPORTE" in primera_fila or "DIA" in primera_fila or "FECHA" not in primera_fila:
        return 1  # Bryan — headers en fila índice 1
    return 0  # Aldair — headers en fila índice 0


def procesar_dataframe(df, nombre_hoja, nombre_archivo):
    """Procesa un DataFrame y retorna lista de registros para la BD."""
    registros = []
    df.columns = [str(c).strip().upper() for c in df.columns]

    col_player = next((c for c in df.columns if "PLAYER" in c), None)
    if not col_player:
        return registros

    col_fecha = next((c for c in df.columns if "FECHA" in c), None)
    if not col_fecha:
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

        # Intentar parsear distintos formatos de fecha
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
    """Lee todas las hojas de un Excel y retorna los registros procesados."""
    registros = []
    try:
        xls = pd.ExcelFile(buffer)
        for hoja in xls.sheet_names:
            # Ignorar hojas de resumen
            nombre_hoja_upper = hoja.upper()
            if "REPORTE" in nombre_hoja_upper and "PROYECTO" in nombre_hoja_upper:
                continue
            if nombre_hoja_upper in ("RESUMEN", "SUMMARY", "REPORTE DE PROYECTOS"):
                continue

            try:
                # Leer con header=0 primero para detectar la estructura
                df_raw = pd.read_excel(buffer, sheet_name=hoja, header=0, dtype=str)

                if df_raw.empty:
                    continue

                header_row = detectar_header_row(df_raw)

                # Releer con el header correcto
                df = pd.read_excel(buffer, sheet_name=hoja, header=header_row, dtype=str)

                if df.empty:
                    continue

                registros_hoja = procesar_dataframe(df, hoja, nombre_archivo)
                registros.extend(registros_hoja)

            except Exception as e:
                print(f"  ⚠️ Error en hoja '{hoja}' de {nombre_archivo}: {e}")

    except Exception as e:
        print(f"  ❌ Error leyendo {nombre_archivo}: {e}")

    return registros


def upsert_registros(db, registros):
    """
    Inserta registros nuevos usando upsert por clave única.
    Clave única: (fecha, hora_numerica, player)
    No hace DELETE masivo — solo inserta lo que no existe.
    """
    if not registros:
        return 0

    # Obtener claves ya existentes en la BD
    existentes = set(
        db.query(
            Reporte.fecha,
            Reporte.hora_numerica,
            Reporte.player
        ).all()
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
    print("🚀 INICIANDO ETL DESDE GOOGLE DRIVE...")

    try:
        service = obtener_servicio_drive()
        print("✅ Conexión a Google Drive establecida")
    except Exception as e:
        print(f"❌ Error conectando a Google Drive: {e}")
        return

    # Listar todos los archivos Excel recursivamente
    print("📂 Buscando archivos Excel en Drive...")
    try:
        archivos = listar_archivos_excel(service, FOLDER_ID_RAIZ)
        print(f"   Encontrados: {len(archivos)} archivos")
    except Exception as e:
        print(f"❌ Error listando archivos: {e}")
        return

    if not archivos:
        print("⚠️ No se encontraron archivos Excel en Drive")
        return

    # Procesar cada archivo
    registros_totales = []
    for archivo in archivos:
        nombre = archivo["name"]
        print(f"  📄 Procesando: {nombre}")
        try:
            buffer = descargar_excel(service, archivo["id"])
            registros = procesar_archivo_excel(buffer, nombre)
            registros_totales.extend(registros)
            print(f"     → {len(registros)} registros extraídos")
        except Exception as e:
            print(f"     ❌ Error: {e}")

    print(f"\n📊 Total registros procesados: {len(registros_totales)}")

    if not registros_totales:
        print("⚠️ No se encontraron datos válidos en los archivos")
        return

    # Guardar en BD con upsert
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