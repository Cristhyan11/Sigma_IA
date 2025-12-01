"""
Funciones de utilidad para el procesamiento y manejo de imágenes médicas.
"""
import os
import shutil
import pydicom
from PIL import Image, ImageTk
import numpy as np

def load_image_for_display(file_path, max_size=(500, 500)):
    """
    Carga una imagen (JPG o DICOM) y la convierte a un objeto compatible con Tkinter.
    """
    try:
        ext = os.path.splitext(file_path)[1].lower()

        if ext in ['.dcm', '.dicom']:
            ds = pydicom.dcmread(file_path)
            # Normalizar a 8-bit para visualización
            pixel_array = ds.pixel_array
            pixel_array = pixel_array - np.min(pixel_array)
            pixel_array = pixel_array / np.max(pixel_array)
            pixel_array = (pixel_array * 255).astype(np.uint8)
            image = Image.fromarray(pixel_array)
        else:
            image = Image.open(file_path)

        image.thumbnail(max_size)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error cargando imagen: {e}")
        return None

def copy_file_based_on_quality(file_path, quality, base_dir):
    """
    Copia el archivo a una carpeta basada en su calidad.
    """
    target_dir = os.path.join(base_dir, "Clasificadas", quality)
    os.makedirs(target_dir, exist_ok=True)

    filename = os.path.basename(file_path)
    destination = os.path.join(target_dir, filename)

    try:
        shutil.copy2(file_path, destination)
        return destination
    except Exception as e:
        print(f"Error copiando archivo: {e}")
        return None
