from database import SessionLocal
import models
from passlib.context import CryptContext

# Configuramos el motor de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def inicializar_llave_maestra():
    print("🛡️ Iniciando protocolo de Seguridad: Llave Maestra...")
    db = SessionLocal()
    
    EMAIL_ADMIN = "admin@admira.com"
    PASSWORD_ADMIN = "Admira2026!"
    NOMBRE_ADMIN = "Administrador Principal"
    
    try:
        # 1. Revisar si ya existe para actualizarlo, o crearlo si no existe
        admin_existente = db.query(models.Usuario).filter(models.Usuario.email == EMAIL_ADMIN).first()
        
        if admin_existente:
            # Usamos la variable PASSWORD_ADMIN aquí
            print("🔄 El usuario administrador ya existe. Actualizando contraseña...")
            admin_existente.password_hash = pwd_context.hash(PASSWORD_ADMIN)
            print("✅ Contraseña actualizada exitosamente.")
        else:
            # Usamos la variable PASSWORD_ADMIN aquí también
            print("Iniciando creación de SuperAdmin...")
            nuevo_admin = models.Usuario(
                nombre_completo=NOMBRE_ADMIN,
                email=EMAIL_ADMIN,
                password_hash=pwd_context.hash(PASSWORD_ADMIN),
                rol="ADMIN",
                activo=True
            )
            db.add(nuevo_admin)
            print("✅ ¡ÉXITO! SuperAdmin creado exitosamente.")
        
        db.commit()
        
        print("\n=========================================")
        print(" 🔐 CREDENCIALES LISTAS PARA INICIAR SESIÓN")
        print("=========================================")
        print(f" 👤 Correo:     {EMAIL_ADMIN}")
        print(f" 🔑 Contraseña: {PASSWORD_ADMIN}")
        print("=========================================\n")
        
    except Exception as e:
        print(f"❌ Ocurrió un error crítico: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    inicializar_llave_maestra()