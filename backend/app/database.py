import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# 1. Cargamos las variables del archivo .env
load_dotenv()

# 2. Obtenemos la URL de Supabase que guardamos en el .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Creamos el motor de conexión para PostgreSQL (Supabase)
# Ya no necesitamos el "connect_args" de SQLite
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()