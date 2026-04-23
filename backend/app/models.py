from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# ==========================================
# 1. TABLA DE USUARIOS (El Catálogo)
# ==========================================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String)
    email = Column(String, unique=True, index=True) 
    password_hash = Column(String)
    rol = Column(String)
    activo = Column(Boolean, default=True)

    proyectos = relationship("UsuarioProyecto", back_populates="usuario", cascade="all, delete-orphan")


# ==========================================
# 2. TABLA PUENTE (El "Cadenero" de Permisos)
# ==========================================
class UsuarioProyecto(Base):
    __tablename__ = "usuarios_proyectos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    nombre_proyecto = Column(String, index=True)

    usuario = relationship("Usuario", back_populates="proyectos")


# ==========================================
# 3. TABLA DE REPORTES (La que ya tenías, intacta)
# ==========================================
class Reporte(Base):
    __tablename__ = "reportes"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, index=True) 
    hora_numerica = Column(Integer)
    horario_legible = Column(String)
    player = Column(String, index=True)
    estado = Column(String, index=True) 
    proyecto = Column(String, index=True)
    archivo_origen = Column(String)