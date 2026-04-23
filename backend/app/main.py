import os
import sys
import subprocess
from datetime import datetime, timedelta, date
from typing import Optional, List
import math

from dotenv import load_dotenv
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from fastapi import FastAPI, Depends, Query, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, not_, or_
from apscheduler.schedulers.background import BackgroundScheduler

import models
from database import engine, get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "admira_secreto_super_seguro_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="ADMIRA Enterprise API")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admira-enterprise.vercel.app", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel): email: str; password: str

# ==========================================
# AUTH Y SEGURIDAD
# ==========================================
def verificar_password(plain_password, hashed_password): return pwd_context.verify(plain_password, hashed_password)

def crear_token_acceso(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def obtener_usuario_actual(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise HTTPException(status_code=401, detail="Token inválido")
    except Exception: raise HTTPException(status_code=401, detail="Token expirado o inválido")
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None: raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario

def requerir_roles(roles_permitidos: List[str]):
    def verificador_de_rol(usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
        if usuario_actual.rol.upper() not in roles_permitidos: raise HTTPException(status_code=403, detail="Operación no permitida")
        return usuario_actual
    return verificador_de_rol

def aplicar_filtro_cliente(usuario: models.Usuario, proyecto_solicitado: Optional[str] = None):
    if usuario.rol.upper() == 'CLIENTE': return usuario.email.split('@')[1].split('.')[0].upper()
    return proyecto_solicitado

# ==========================================
# ETL AUTOMÁTICO
# ==========================================
def ejecutar_etl():
    try:
        ruta_etl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etl.py")
        subprocess.run([sys.executable, ruta_etl], check=True)
    except Exception as e: print(f"Error ETL: {e}")

@app.on_event("startup")
def iniciar_tareas_programadas():
    scheduler = BackgroundScheduler()
    for hora in [9, 12, 13, 15, 17, 18]: scheduler.add_job(ejecutar_etl, 'cron', hour=hora, minute=15)
    scheduler.start()

@app.post("/api/sincronizar")
def sincronizar_manual(background_tasks: BackgroundTasks, usuario_actual: models.Usuario = Depends(requerir_roles(["ADMIN", "DIRECTIVO", "SOPORTE"]))):
    background_tasks.add_task(ejecutar_etl)
    return {"mensaje": "Sincronización iniciada"}

# ==========================================
# REGLAS GLOBALES Y FILTROS CORE
# ==========================================
REGLA_LIVERPOOL = not_(and_(models.Reporte.proyecto.ilike("%LIVERPOOL%"), models.Reporte.hora_numerica == 9))

# FUNCIÓN MAESTRA DE ALIAS: Fusiona SUSUKY con SUZUKY en las búsquedas SQL
def aplicar_filtro_proyecto(query, modelo_columna, proyecto_str):
    if not proyecto_str or proyecto_str == "Todos los Proyectos": 
        return query
    if proyecto_str.upper() in ["SUZUKY", "SUSUKY"]:
        return query.filter(or_(modelo_columna.ilike("%SUZUKY%"), modelo_columna.ilike("%SUSUKY%")))
    return query.filter(modelo_columna.ilike(f"%{proyecto_str}%"))

def get_ventana_vigencia(db: Session, proyecto: Optional[str] = None):
    query_fechas = db.query(models.Reporte.fecha).distinct()
    query_fechas = aplicar_filtro_proyecto(query_fechas, models.Reporte.proyecto, proyecto)
    fechas = query_fechas.order_by(models.Reporte.fecha.desc()).limit(2).all()
    return [f[0] for f in fechas]

def obtener_inventario_activo(db: Session):
    ultimos_5_archivos = db.query(models.Reporte.fecha, models.Reporte.hora_numerica)\
        .distinct().order_by(models.Reporte.fecha.desc(), models.Reporte.hora_numerica.desc()).limit(5).all()
    if not ultimos_5_archivos: return None
    filtros_or = or_(*[and_(models.Reporte.fecha == f, models.Reporte.hora_numerica == h) for f, h in ultimos_5_archivos])
    return db.query(models.Reporte.player).filter(filtros_or).distinct().subquery()

# ==========================================
# ENDPOINTS PRINCIPALES
# ==========================================
@app.post("/api/login")
def iniciar_sesion(credenciales: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == credenciales.email).first()
    if not usuario or not verificar_password(credenciales.password, usuario.password_hash): raise HTTPException(status_code=401, detail="Error")
    if not usuario.activo: raise HTTPException(status_code=400, detail="Inactivo")
    datos_token = {"sub": usuario.email, "rol": usuario.rol, "nombre": usuario.nombre_completo, "id": usuario.id}
    return {"access_token": crear_token_acceso(datos_token, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)), "token_type": "bearer", "usuario": datos_token}

@app.get("/api/configuracion")
def obtener_configuracion_inicial(db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    if usuario_actual.rol.upper() == 'CLIENTE': 
        return {"proyectos": [aplicar_filtro_cliente(usuario_actual)], "fecha_inicio_sugerida": date.today(), "fecha_fin_sugerida": date.today()}
    
    proyectos = db.query(models.Reporte.proyecto).distinct().all()
    proyectos_limpios = set()
    for p in proyectos:
        if p[0]:
            nombre = "SUZUKY" if p[0].upper() == "SUSUKY" else p[0].upper()
            proyectos_limpios.add(nombre)

    return {"proyectos": sorted(list(proyectos_limpios)), "fecha_inicio_sugerida": db.query(func.min(models.Reporte.fecha)).scalar(), "fecha_fin_sugerida": db.query(func.max(models.Reporte.fecha)).scalar()}

@app.get("/api/kpis")
def obtener_kpis(proyecto: Optional[str] = None, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    proyecto_seguro = aplicar_filtro_cliente(usuario_actual, proyecto)
    subq_activos = obtener_inventario_activo(db)
    if subq_activos is None:
        return {"uptime":0, "uniquePlayers":0, "proyectosActivos":0, "proyectosSLA":0, "dona_activos":0, "dona_caidos":0}

    query_base = db.query(models.Reporte).filter(models.Reporte.player.in_(subq_activos)).filter(REGLA_LIVERPOOL)
    query_base = aplicar_filtro_proyecto(query_base, models.Reporte.proyecto, proyecto_seguro)
    if fecha_inicio and fecha_fin: query_base = query_base.filter(models.Reporte.fecha.between(fecha_inicio, fecha_fin))

    unique_players = query_base.with_entities(func.count(func.distinct(models.Reporte.player))).scalar() or 0
    if unique_players == 0:
        return {"uptime":0, "uniquePlayers":0, "proyectosActivos":0, "proyectosSLA":0, "dona_activos":0, "dona_caidos":0}

    total_registros = query_base.count()
    total_caidas = query_base.filter(models.Reporte.estado == 'Sin conexión').count()
    porcentaje_uptime = ((total_registros - total_caidas) / total_registros) if total_registros > 0 else 0

    stats_proyectos = query_base.with_entities(
        models.Reporte.proyecto,
        func.count(models.Reporte.id).label('total'),
        func.count(models.Reporte.id).filter(models.Reporte.estado == 'Sin conexión').label('caidas')
    ).group_by(models.Reporte.proyecto).all()

    # FUSIÓN DE PROYECTOS PARA KPIs
    proyectos_dict = {}
    for p in stats_proyectos:
        if not p.proyecto: continue
        nombre_proy = "SUZUKY" if p.proyecto.upper() == "SUSUKY" else p.proyecto.upper()
        if nombre_proy not in proyectos_dict:
            proyectos_dict[nombre_proy] = {"total": 0, "caidas": 0}
        proyectos_dict[nombre_proy]["total"] += p.total
        proyectos_dict[nombre_proy]["caidas"] += p.caidas

    proyectos_activos = len(proyectos_dict)
    proyectos_sla = 0
    for data in proyectos_dict.values():
        uptime_p = ((data["total"] - data["caidas"]) / data["total"]) if data["total"] > 0 else 0
        if uptime_p >= 0.70: proyectos_sla += 1

    return {
        "uptime": round(porcentaje_uptime * 100, 1), 
        "uniquePlayers": unique_players, 
        "proyectosActivos": proyectos_activos, 
        "proyectosSLA": proyectos_sla,
        "dona_activos": round(unique_players * porcentaje_uptime), 
        "dona_caidos": unique_players - round(unique_players * porcentaje_uptime)
    }

@app.get("/api/graficas/barras")
def obtener_datos_barras(proyecto: Optional[str] = None, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    proyecto_seguro = aplicar_filtro_cliente(usuario_actual, proyecto)
    subq_activos = obtener_inventario_activo(db)
    if subq_activos is None: return {"categorias": [], "series": []}

    # 1. Obtenemos el UNIVERSO TOTAL de registros por hora
    query_base = db.query(models.Reporte).filter(models.Reporte.player.in_(subq_activos)).filter(REGLA_LIVERPOOL)
    query_base = aplicar_filtro_proyecto(query_base, models.Reporte.proyecto, proyecto_seguro)
    if fecha_inicio and fecha_fin: query_base = query_base.filter(models.Reporte.fecha.between(fecha_inicio, fecha_fin))

    t9 = t1 = t3 = t5 = tOther = 0
    for h, c in query_base.with_entities(models.Reporte.hora_numerica, func.count(func.distinct(models.Reporte.player))).group_by(models.Reporte.hora_numerica).all():
        if h == 9: t9 += c
        elif h in [12, 13]: t1 += c
        elif h == 15: t3 += c
        elif h == 17: t5 += c
        else: tOther += c

    # 2. Obtenemos ÚNICAMENTE LOS CAÍDOS por hora
    query_caidos = query_base.filter(models.Reporte.estado == 'Sin conexión')
    
    c9 = c1 = c3 = c5 = cOther = 0
    for h, c in query_caidos.with_entities(models.Reporte.hora_numerica, func.count(func.distinct(models.Reporte.player))).group_by(models.Reporte.hora_numerica).all():
        if h == 9: c9 += c
        elif h in [12, 13]: c1 += c
        elif h == 15: c3 += c
        elif h == 17: c5 += c
        else: cOther += c
        
    # 3. Calculamos el porcentaje INDIVIDUAL por cada franja
    def calc_uptime(total, caidos):
        if total == 0: return 0 
        return round(((total - caidos) / total) * 100, 1)

    return {
        "categorias": ['9:00 am', '12/1:00 pm', '3:00 pm', '5:00 pm', 'Otros'], 
        "series": [calc_uptime(t9, c9), calc_uptime(t1, c1), calc_uptime(t3, c3), calc_uptime(t5, c5), calc_uptime(tOther, cOther)]
    }

@app.get("/api/tabla")
def obtener_tabla(proyecto: Optional[str] = None, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, estado: Optional[str] = None, player: Optional[str] = None, pagina: int = Query(1), filas_por_pagina: int = Query(10), db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    proyecto_seguro = aplicar_filtro_cliente(usuario_actual, proyecto)
    try:
        subq_activos = obtener_inventario_activo(db)
        if subq_activos is None: return {"total_registros": 0, "pagina_actual": 1, "total_paginas": 1, "items": []}
        
        query = db.query(models.Reporte).filter(models.Reporte.player.in_(subq_activos)).filter(REGLA_LIVERPOOL)
        query = aplicar_filtro_proyecto(query, models.Reporte.proyecto, proyecto_seguro)
        
        if fecha_inicio and fecha_fin: query = query.filter(models.Reporte.fecha.between(fecha_inicio, fecha_fin))
        if estado: query = query.filter(models.Reporte.estado == estado)
        if player: query = query.filter(models.Reporte.player.ilike(f"%{player}%"))
        
        # 1. Obtenemos el total real
        total = query.count()
        
        # 2. Calculamos las páginas reales
        total_paginas = math.ceil(total / filas_por_pagina) if total > 0 else 1
        
        # 3. Traemos solo los registros de esta página
        registros = query.order_by(models.Reporte.fecha.desc(), models.Reporte.hora_numerica.desc()).offset((pagina-1)*filas_por_pagina).limit(filas_por_pagina).all()
        
        # 4. Retornamos las variables dinámicas (YA NO ESTÁN DUROS)
        return {
            "total_registros": total, 
            "pagina_actual": pagina, 
            "total_paginas": total_paginas,
            "items": [{"FECHA": r.fecha.isoformat() if r.fecha else "", "HORARIO_LEGIBLE": r.horario_legible, "PLAYER": r.player, "ESTADO": r.estado, "PROYECTO": "SUZUKY" if (r.proyecto and r.proyecto.upper() == "SUSUKY") else r.proyecto, "ARCHIVO_ORIGEN": r.archivo_origen or ""} for r in registros]
        }
    except Exception as e: 
        return {"total_registros": 0, "pagina_actual": 1, "total_paginas": 1, "items": [], "error": str(e)}

@app.get("/api/graficas/tendencia")
def obtener_tendencia(proyecto: Optional[str] = None, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    proyecto_seguro = aplicar_filtro_cliente(usuario_actual, proyecto)
    subq_activos = obtener_inventario_activo(db)
    if subq_activos is None: return {"categorias": [], "series": []}

    query = db.query(
        models.Reporte.fecha,
        func.count(models.Reporte.id).label('total'),
        func.count(models.Reporte.id).filter(models.Reporte.estado == 'Sin conexión').label('caidas')
    ).filter(models.Reporte.player.in_(subq_activos)).filter(REGLA_LIVERPOOL)

    query = aplicar_filtro_proyecto(query, models.Reporte.proyecto, proyecto_seguro)
    if fecha_inicio and fecha_fin: 
        query = query.filter(models.Reporte.fecha.between(fecha_inicio, fecha_fin))

    resultados = query.group_by(models.Reporte.fecha).order_by(models.Reporte.fecha.asc()).all()

    categorias, series = [], []
    for r in resultados:
        if r.fecha is None: continue
        uptime = round(((r.total - r.caidas) / r.total) * 100, 1) if r.total > 0 else 0
        # Formato de fecha corto (Ej. "09 Abr")
        categorias.append(r.fecha.strftime("%d %b"))
        series.append(uptime)

    return {"categorias": categorias, "series": series}

@app.get("/api/monitoreo/status")
def obtener_estatus_monitoreo(proyecto: Optional[str] = None, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    proyecto_seguro = aplicar_filtro_cliente(usuario_actual, proyecto)
    subq_activos = obtener_inventario_activo(db)
    if subq_activos is None: return []
    ventana = get_ventana_vigencia(db, proyecto_seguro)
    if not ventana: return []
    query = db.query(models.Reporte).filter(models.Reporte.fecha == ventana[0]).filter(models.Reporte.player.in_(subq_activos))
    query = aplicar_filtro_proyecto(query, models.Reporte.proyecto, proyecto_seguro)
    subq = query.with_entities(models.Reporte.player, func.max(models.Reporte.hora_numerica).label('max_h')).group_by(models.Reporte.player).subquery()
    registros = db.query(models.Reporte).join(subq, (models.Reporte.player == subq.c.player) & (models.Reporte.hora_numerica == subq.c.max_h)).filter(models.Reporte.fecha == ventana[0]).all()
    vistos, resultado = set(), []
    for r in registros:
        if r.player not in vistos:
            resultado.append({"player": r.player, "estado": r.estado, "proyecto": "SUZUKY" if (r.proyecto and r.proyecto.upper() == "SUSUKY") else r.proyecto, "ultima_conexion": f"{r.fecha} {r.horario_legible}", "alerta": r.estado == 'Sin conexión'})
            vistos.add(r.player)
    return resultado

@app.get("/api/reporte/consolidado")
def obtener_reporte_consolidado(proyecto: Optional[str] = Query(None), fecha_inicio: Optional[date] = Query(None), fecha_fin: Optional[date] = Query(None), db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(requerir_roles(["ADMIN", "DIRECTIVO"]))):
    try:
        subq_activos = obtener_inventario_activo(db)
        if subq_activos is None: return []
        query = db.query(models.Reporte).filter(models.Reporte.player.in_(subq_activos)).filter(REGLA_LIVERPOOL)
        query = aplicar_filtro_proyecto(query, models.Reporte.proyecto, proyecto)
        if fecha_inicio and fecha_fin: query = query.filter(models.Reporte.fecha.between(fecha_inicio, fecha_fin))
            
        registros = query.all()
        if not registros: return []
        datos_players = {}
        for r in registros:
            p = r.player
            if p not in datos_players: 
                nombre_p = "SUZUKY" if (r.proyecto and r.proyecto.upper() == "SUSUKY") else r.proyecto
                datos_players[p] = {"proyecto": nombre_p, "total": 0, "caidas": 0, "ultima_fecha": r.fecha, "ultima_hora": r.hora_numerica, "ultimo_estado": r.estado, "horario_legible": r.horario_legible, "archivo_origen": r.archivo_origen}
            datos_players[p]["total"] += 1
            if r.estado == 'Sin conexión': datos_players[p]["caidas"] += 1
            if r.fecha > datos_players[p]["ultima_fecha"] or (r.fecha == datos_players[p]["ultima_fecha"] and r.hora_numerica > datos_players[p]["ultima_hora"]):
                datos_players[p].update({"ultima_fecha": r.fecha, "ultima_hora": r.hora_numerica, "ultimo_estado": r.estado, "horario_legible": r.horario_legible, "archivo_origen": r.archivo_origen})
        resultado = []
        for player, data in datos_players.items():
            uptime = round(((data["total"] - data["caidas"]) / data["total"]) * 100, 1) if data["total"] > 0 else 0
            resultado.append({"player": player, "proyecto": data["proyecto"], "total_reportes": data["total"], "caidas": data["caidas"], "uptime": uptime, "alerta": data["ultimo_estado"] == 'Sin conexión', "ultimo_estado": data["ultimo_estado"], "ultima_conexion": f"{data['ultima_fecha']} {data['horario_legible']}", "archivo_origen": data["archivo_origen"] or ""})
        return sorted(resultado, key=lambda x: x["uptime"])
    except Exception as e: return []

# ==========================================
# ENDPOINTS USUARIOS
# ==========================================
class PerfilUpdate(BaseModel): nombre: str
class PasswordUpdate(BaseModel): password_actual: str; password_nueva: str
class UsuarioCreate(BaseModel): nombre_completo: str; email: str; password: str; rol: str
class UsuarioUpdate(BaseModel): nombre_completo: Optional[str] = None; rol: Optional[str] = None; activo: Optional[bool] = None

@app.put("/api/usuarios/perfil")
def actualizar_perfil(datos: PerfilUpdate, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    usuario_actual.nombre_completo = datos.nombre
    db.commit()
    return {"mensaje": "Perfil actualizado"}

@app.put("/api/usuarios/password")
def cambiar_password(datos: PasswordUpdate, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    if not verificar_password(datos.password_actual, usuario_actual.password_hash): raise HTTPException(status_code=400, detail="Error")
    usuario_actual.password_hash = pwd_context.hash(datos.password_nueva)
    db.commit()
    return {"mensaje": "Contraseña actualizada"}

@app.get("/api/usuarios/estadisticas")
def obtener_estadisticas_usuarios(db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(requerir_roles(["ADMIN", "DIRECTIVO"]))):
    return {"total": db.query(models.Usuario).count(), "activos": db.query(models.Usuario).filter(models.Usuario.activo == True).count(), "roles": db.query(func.count(func.distinct(models.Usuario.rol))).scalar() or 0}

@app.post("/api/usuarios")
def crear_nuevo_usuario(datos: UsuarioCreate, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(requerir_roles(["ADMIN", "DIRECTIVO"]))):
    if db.query(models.Usuario).filter(models.Usuario.email == datos.email).first(): raise HTTPException(status_code=400, detail="Error")
    nuevo_usuario = models.Usuario(nombre_completo=datos.nombre_completo, email=datos.email, password_hash=pwd_context.hash(datos.password), rol=datos.rol.upper(), activo=True)
    db.add(nuevo_usuario)
    db.commit()
    return {"mensaje": "Usuario creado"}

@app.get("/api/usuarios")
def listar_usuarios(db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(requerir_roles(["ADMIN", "DIRECTIVO"]))):
    return [{"id": u.id, "nombre_completo": u.nombre_completo, "email": u.email, "rol": u.rol, "activo": u.activo} for u in db.query(models.Usuario).all()]

@app.put("/api/usuarios/{usuario_id}")
def editar_usuario(usuario_id: int, datos: UsuarioUpdate, db: Session = Depends(get_db), usuario_actual: models.Usuario = Depends(requerir_roles(["ADMIN", "DIRECTIVO"]))):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario: raise HTTPException(status_code=404, detail="No encontrado")
    if datos.nombre_completo is not None: usuario.nombre_completo = datos.nombre_completo
    if datos.rol is not None: usuario.rol = datos.rol.upper()
    if datos.activo is not None: usuario.activo = datos.activo
    db.commit()
    return {"mensaje": "Actualizado"}