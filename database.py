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
    study_type = Column(String) 
    laterality = Column(String) 

    # Evaluación Técnica
    sharpness = Column(String) # Nitidez
    illumination = Column(String) # Iluminación
    centering = Column(String) # Centrado
    field_of_view = Column(String) # Campo de visión
    
    # Problemas
    artifacts = Column(String) # Artefactos
    obstructions = Column(String) # Obstrucciones
    
    # Conclusión
    quality = Column(String) # Gradabilidad (Grado A, B, No gradable)
    diagnostic_utility = Column(String) # Útil, Limitada, No útil
    
    validation_status = Column(String, default="Pending") # Pending, Validated
    created_at = Column(DateTime, default=datetime.utcnow)
    doctor_notes = Column(String)

def init_db(connection_string='sqlite:///local_medical_data.db'):
    """
    Inicializa la base de datos.
    Para la nube, cambiar connection_string a algo como:
    'postgresql://user:password@host:port/dbname'
    """
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
