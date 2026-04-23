import pandas as pd
import os
import warnings
import re
from datetime import datetime

# Importamos la conexión a la base de datos y nuestro modelo de tabla
from database import SessionLocal
from models import Reporte

# --- CONFIGURACIÓN ---
CARPETA_RAIZ = r'C:\Users\ADmira01\OneDrive\Documentos\ADMIRA\Reportes admira' 

warnings.filterwarnings('ignore')

def limpiar_hora(texto_columna):
    texto = str(texto_columna).upper().strip()
    match = re.search(r'(\d{1,2})[:.](\d{2})', texto)
    if match:
        hora = int(match.group(1))
        if "PM" in texto and hora != 12: hora += 12
        elif "AM" in texto and hora == 12: hora = 0
        elif hora > 12 and "AM" not in texto: pass
        return hora
    return None

def procesar_todo():
    print(f"🚀 INICIANDO EXTRACCIÓN Y CARGA A BASE DE DATOS...")
    registros_finales = []
    
    for raiz, carpetas, archivos in os.walk(CARPETA_RAIZ):
        for archivo in archivos:
            if archivo.endswith((".xlsx", ".csv")) and not archivo.startswith("~"):
                ruta = os.path.join(raiz, archivo)
                try:
                    if archivo.endswith(".xlsx"):
                        xls = pd.ExcelFile(ruta)
                        hojas = xls.sheet_names
                    else:
                        hojas = ['CSV_DATA'] # Si es CSV, lo tratamos como una sola hoja

                    for hoja in hojas:
                        if "REPORTE" in hoja.upper() and "PROYECTO" in hoja.upper():
                            continue
                            
                        # Leer archivo
                        if archivo.endswith(".xlsx"):
                            df = pd.read_excel(ruta, sheet_name=hoja, header=1, dtype=str)
                        else:
                            df = pd.read_csv(ruta, dtype=str)
                        
                        df.columns = [str(c).strip().upper() for c in df.columns]
                        
                        col_player = next((c for c in df.columns if "PLAYER" in c), None)
                        if not col_player: continue
                        
                        cols_horarios = [c for c in df.columns if (":" in c or "REPORTE" in c) and "FECHA" not in c and "DESCONEXIONES" not in c]
                        df = df.dropna(subset=[col_player])
                        
                        for _, row in df.iterrows():
                            # Buscar columna de fecha
                            col_fecha = next((c for c in df.columns if "FECHA" in c), 'FECHA DE REPORTE')
                            fecha_raw = str(row.get(col_fecha, '')).split(' ')[0]
                            
                            if not re.match(r'\d{4}-\d{2}-\d{2}', fecha_raw):
                                continue
                            
                            # Transformación clave: Convertir texto a objeto Date real
                            fecha_obj = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
                            player = str(row[col_player]).strip()
                            
                            for col_h in cols_horarios:
                                estado = str(row[col_h]).strip()
                                if estado.lower() in ['nan', 'nat', '', 'none']: 
                                    continue
                                    
                                hora_num = limpiar_hora(col_h)
                                if hora_num is not None:
                                    registros_finales.append({
                                        "fecha": fecha_obj,
                                        "hora_numerica": hora_num,
                                        "horario_legible": col_h,
                                        "player": player,
                                        "estado": estado,
                                        "proyecto": hoja if archivo.endswith(".xlsx") else archivo.replace('.csv', ''),
                                        "archivo_origen": archivo
                                    })
                except Exception as e:
                    print(f"  ❌ Error leyendo {archivo}: {e}")

    # --- GUARDADO EN BASE DE DATOS ---
    if registros_finales:
        print(f"\n🧩 Insertando {len(registros_finales)} registros en SQLite...")
        db = SessionLocal()
        try:
            # 1. Limpiamos la tabla para no duplicar datos si corremos el script varias veces
            db.query(Reporte).delete()
            
            # 2. Inserción masiva (Bulk Insert) - ¡Mil veces más rápido que un ciclo for!
            db.bulk_insert_mappings(Reporte, registros_finales)
            db.commit()
            print(f"💾 ¡LISTO! Base de datos poblada con éxito.")
        except Exception as e:
            db.rollback()
            print(f"❌ Error al guardar en BD: {e}")
        finally:
            db.close()
    else:
        print("⚠️ No se encontraron datos válidos. Revisa la ruta de CARPETA_RAIZ.")

if __name__ == "__main__":
    procesar_todo()