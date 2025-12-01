"""
Módulo para la gestión de la base de datos y definición de modelos ORM.
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class ImageRecord(Base):
    __tablename__ = 'image_records'

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    original_path = Column(String, nullable=False)
    
    # Campos de clasificación
    study_type = Column(String) # O.C.T, Foco principal, etc.
    quality = Column(String)    # Buena, Regular, Mala
    is_centered = Column(Boolean)
    
    # Campos adicionales sugeridos
    laterality = Column(String) # OD (Derecho), OS (Izquierdo)
    diagnosis = Column(String)  # Normal, Patológico, etc.
    diagnosis_detail = Column(String) # Detalle del diagnóstico (ej. Retinopatía Diabética)
    severity = Column(String) # Leve, Moderada, Severa
    artifacts = Column(String) # Lista de artefactos separados por coma
    
    validation_status = Column(String, default="Pending") # Pending, Validated
    created_at = Column(DateTime, default=datetime.utcnow)
    doctor_notes = Column(String)

def init_db(connection_string='sqlite:///local_data.db'):
    """
    Inicializa la base de datos.
    Para la nube, cambiar connection_string a algo como:
    'postgresql://user:password@host:port/dbname'
    """
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
