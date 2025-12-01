import os
import shutil

def reset_project():
    # 1. Borrar la base de datos
    db_file = "local_medical_data.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✅ Base de datos '{db_file}' eliminada.")
        except Exception as e:
            print(f"❌ Error eliminando base de datos: {e}")
    else:
        print(f"ℹ️ No se encontró la base de datos '{db_file}'.")

    # 2. Borrar la carpeta de imágenes clasificadas
    # NOTA: Como ahora el programa COPIA las imágenes, borrar esta carpeta es seguro.
    # Las imágenes originales en tu carpeta de origen NO se tocarán.
    
    classified_dir = "Clasificadas"
    if os.path.exists(classified_dir):
        response = input(f"⚠️ ¿Estás seguro de que quieres borrar la carpeta '{classified_dir}' y todo su contenido? (s/n): ")
        if response.lower() == 's':
            try:
                shutil.rmtree(classified_dir)
                print(f"✅ Carpeta '{classified_dir}' eliminada.")
            except Exception as e:
                print(f"❌ Error eliminando carpeta: {e}")
        else:
            print("ℹ️ Operación cancelada para la carpeta de imágenes.")
    else:
        print(f"ℹ️ No se encontró la carpeta '{classified_dir}'.")

    print("\n✨ Proyecto limpio. Listo para entregar.")

if __name__ == "__main__":
    reset_project()
