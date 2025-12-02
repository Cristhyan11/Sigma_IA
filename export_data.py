import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import ImageRecord

def export_csv():
    db_path = 'local_medical_data.db'
    if not os.path.exists(db_path):
        print(f"❌ No se encontró la base de datos: {db_path}")
        return

    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        records = session.query(ImageRecord).all()
        
        filename = 'dataset_labels.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                'filename', 'study_type', 'laterality', 
                'sharpness', 'illumination', 'centering', 'field_of_view',
                'obstructions', 'artifacts', 
                'quality', 'diagnostic_utility', 'doctor_notes'
            ])
            
            for r in records:
                writer.writerow([
                    r.filename, r.study_type, r.laterality,
                    r.sharpness, r.illumination, r.centering, r.field_of_view,
                    r.obstructions, r.artifacts,
                    r.quality, r.diagnostic_utility, r.doctor_notes
                ])
                
        print(f"✅ Exportado exitosamente a {filename}")
        print(f"Total registros: {len(records)}")
        
    except Exception as e:
        print(f"❌ Error exportando datos: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    export_csv()
