"""
Punto de entrada principal para la aplicación de clasificación de imágenes médicas.
"""
import tkinter as tk
from database import init_db
from gui import MedicalImageApp

def main():
    """
    Inicializa la base de datos y lanza la interfaz gráfica.
    """
    # Inicializar Base de Datos
    # Para usar PostgreSQL en la nube, cambia el string de conexión aquí.
    # Ejemplo: 'postgresql://usuario:password@host:5432/nombre_db'
    db_session = init_db('sqlite:///local_medical_data.db')

    # Iniciar GUI
    root = tk.Tk()
    _app = MedicalImageApp(root, db_session)
    root.mainloop()

if __name__ == "__main__":
    main()
