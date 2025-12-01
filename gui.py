"""
Módulo que define la interfaz gráfica de usuario (GUI) para la aplicación.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import random
from database import ImageRecord
from utils import load_image_for_display, copy_file_based_on_quality

class ToolTip:
    """
    Clase para mostrar tooltips (mensajes emergentes) al pasar el mouse sobre un widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        """Muestra el tooltip."""
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        """Oculta el tooltip."""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class MedicalImageApp:
    """
    Clase principal de la interfaz gráfica para la clasificación de imágenes.
    """
    def __init__(self, root, db_session):
        self.root = root
        self.session = db_session
        self.root.title("Clasificador de Imágenes Oftalmológicas")
        self.root.geometry("1000x700")
        
        self.current_image_path = None
        self.photo_image = None # Referencia para evitar garbage collection
        
        # Variables para manejo de carpetas
        self.image_list = []
        self.current_index = -1
        self.folder_path = None
        self.pending_changes = {} # Diccionario para guardar cambios en memoria antes de guardar en DB

        self._setup_ui()

    def _setup_ui(self):
        # Frame principal dividido en dos: Imagen (Izquierda) y Controles (Derecha)
        left_frame = tk.Frame(self.root, width=600, bg="gray")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = tk.Frame(self.root, width=400, padx=20, pady=20)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Área de Imagen ---
        self.image_label = tk.Label(left_frame, text="Cargar una carpeta para comenzar", bg="gray", fg="white")
        self.image_label.pack(expand=True)
        
        # Panel de navegación
        nav_frame = tk.Frame(left_frame, bg="gray")
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Button(nav_frame, text="<< Anterior", command=self.prev_image).pack(side=tk.LEFT, padx=20)
        self.btn_load = tk.Button(nav_frame, text="Seleccionar Carpeta", command=self.load_folder)
        self.btn_load.pack(side=tk.LEFT, expand=True)
        tk.Button(nav_frame, text="Siguiente >>", command=self.next_image).pack(side=tk.RIGHT, padx=20)
        
        self.lbl_progress = tk.Label(left_frame, text="0 / 0", bg="gray", fg="white")
        self.lbl_progress.pack(side=tk.BOTTOM)

        # --- Controles ---
        tk.Label(right_frame, text="Validación de Estudio", font=("Arial", 14, "bold")).pack(pady=(0, 20))

        # Tipo de Estudio
        tk.Label(right_frame, text="Tipo de Estudio:").pack(anchor="w")
        self.study_var = tk.StringVar()
        # Corregido según términos médicos estándar
        self.cb_study = ttk.Combobox(right_frame, textvariable=self.study_var, 
                                     values=[
                                         "Fondo de Ojo (Centrado en Papila)",
                                         "Fondo de Ojo (Centrado en Mácula)",
                                         "OCT Macular",
                                         "OCT Nervio Óptico",
                                         "Angiografía",
                                         "Angio OCT"
                                     ])
        self.cb_study.pack(fill=tk.X, pady=5)
        ToolTip(self.cb_study, "Seleccione la técnica de imagen utilizada (ej. OCT, Fondo de Ojo).")

        # Calidad
        tk.Label(right_frame, text="Calidad de Imagen:").pack(anchor="w")
        self.quality_var = tk.StringVar()
        self.cb_quality = ttk.Combobox(right_frame, textvariable=self.quality_var, 
                                       values=["Buena", "Regular", "Mala"])
        self.cb_quality.pack(fill=tk.X, pady=5)
        ToolTip(self.cb_quality, "Evalúe si la imagen es clara y útil para el diagnóstico.")

        # Centrado
        self.centered_var = tk.BooleanVar()
        chk_centered = tk.Checkbutton(right_frame, text="¿Imagen Centrada?", variable=self.centered_var)
        chk_centered.pack(anchor="w", pady=10)
        ToolTip(chk_centered, "Marque si la estructura de interés (mácula/papila) está en el centro.")

        # Lateralidad (Extra)
        tk.Label(right_frame, text="Lateralidad:").pack(anchor="w")
        self.laterality_var = tk.StringVar()
        self.cb_laterality = ttk.Combobox(right_frame, textvariable=self.laterality_var, 
                                          values=["OD (Derecho)", "OS (Izquierdo)", "Desconocido"])
        self.cb_laterality.pack(fill=tk.X, pady=5)
        ToolTip(self.cb_laterality, "Indique si la imagen corresponde al ojo derecho (OD) o izquierdo (OS).")

        # Diagnóstico Presuntivo
        tk.Label(right_frame, text="Diagnóstico Presuntivo:").pack(anchor="w")
        self.diagnosis_var = tk.StringVar()
        self.cb_diagnosis = ttk.Combobox(right_frame, textvariable=self.diagnosis_var,
                                         values=["Normal", "Retinopatía Diabética", "Glaucoma", "Degeneración Macular", "Catarata", "Otro"])
        self.cb_diagnosis.pack(fill=tk.X, pady=5)
        ToolTip(self.cb_diagnosis, "Seleccione la patología principal identificada o 'Normal'.")

        # Severidad
        tk.Label(right_frame, text="Severidad / Grado:").pack(anchor="w")
        self.severity_var = tk.StringVar()
        self.cb_severity = ttk.Combobox(right_frame, textvariable=self.severity_var,
                                        values=["N/A", "Leve", "Moderada", "Severa", "Proliferativa"])
        self.cb_severity.pack(fill=tk.X, pady=5)
        ToolTip(self.cb_severity, "Indique el grado de avance de la patología.")

        # Artefactos (Checkboxes)
        tk.Label(right_frame, text="Artefactos / Problemas:").pack(anchor="w", pady=(10, 0))
        self.artifact_blur = tk.BooleanVar()
        self.artifact_illumination = tk.BooleanVar()
        self.artifact_obstruction = tk.BooleanVar()
        
        chk_blur = tk.Checkbutton(right_frame, text="Borrosa / Desenfocada", variable=self.artifact_blur)
        chk_blur.pack(anchor="w")
        ToolTip(chk_blur, "Marque si la imagen está desenfocada o movida.")
        
        chk_illum = tk.Checkbutton(right_frame, text="Mala Iluminación", variable=self.artifact_illumination)
        chk_illum.pack(anchor="w")
        ToolTip(chk_illum, "Marque si la imagen está muy oscura o quemada (sobreexpuesta).")
        
        chk_obs = tk.Checkbutton(right_frame, text="Obstrucción (Pestañas/Polvo)", variable=self.artifact_obstruction)
        chk_obs.pack(anchor="w")
        ToolTip(chk_obs, "Marque si hay elementos externos bloqueando la visión.")

        # Notas Adicionales
        tk.Label(right_frame, text="Notas Adicionales:").pack(anchor="w", pady=(10, 0))
        self.txt_notes = tk.Text(right_frame, height=3, width=30)
        self.txt_notes.pack(fill=tk.X, pady=5)
        ToolTip(self.txt_notes, "Espacio para observaciones clínicas adicionales.")

        # Botones de Acción
        self.btn_save_batch = tk.Button(
            right_frame,
            text="Guardar Todo el Lote",
            command=self.process_batch,
            bg="blue",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.btn_save_batch.pack(fill=tk.X, pady=20)

        self.lbl_status = tk.Label(right_frame, text="Esperando...", fg="blue")
        self.lbl_status.pack(side=tk.BOTTOM)

    def load_folder(self):
        folder_selected = filedialog.askdirectory()
        if not folder_selected:
            return
            
        self.folder_path = folder_selected
        self.image_list = []
        
        # Escanear carpeta
        valid_extensions = ('.jpg', '.jpeg', '.png', '.dcm', '.dicom')
        for f in os.listdir(self.folder_path):
            if f.lower().endswith(valid_extensions):
                self.image_list.append(os.path.join(self.folder_path, f))
        
        self.image_list.sort()
        
        if not self.image_list:
            messagebox.showwarning("Carpeta vacía", "No se encontraron imágenes válidas en la carpeta.")
            return
            
        self.current_index = 0
        self.load_current_image()

    def load_current_image(self):
        if not self.image_list or self.current_index < 0 or self.current_index >= len(self.image_list):
            return
            
        file_path = self.image_list[self.current_index]
        self.current_image_path = file_path
        
        # Actualizar progreso
        self.lbl_progress.config(text=f"Imagen {self.current_index + 1} de {len(self.image_list)}")
        
        # Mostrar imagen
        img = load_image_for_display(file_path)
        if img:
            self.photo_image = img
            self.image_label.config(image=img, text="")
            self.restore_selection() # Cargar datos guardados o predecir
        else:
            self.image_label.config(image="", text="Error cargando imagen")

    def next_image(self):
        self.save_current_selection() # Guardar en memoria
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_current_image()
        else:
            messagebox.showinfo("Fin", "Has llegado a la última imagen de la carpeta.")

    def prev_image(self):
        self.save_current_selection() # Guardar en memoria
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()

    def save_current_selection(self):
        """Guarda la selección actual en el diccionario de memoria."""
        if not self.current_image_path:
            return

        # Recolectar artefactos
        artifacts_list = []
        if self.artifact_blur.get():
            artifacts_list.append("Blur")
        if self.artifact_illumination.get():
            artifacts_list.append("Illumination")
        if self.artifact_obstruction.get():
            artifacts_list.append("Obstruction")
        artifacts_str = ",".join(artifacts_list)

        data = {
            'study_type': self.study_var.get(),
            'quality': self.quality_var.get(),
            'is_centered': self.centered_var.get(),
            'laterality': self.laterality_var.get(),
            'diagnosis_detail': self.diagnosis_var.get(),
            'severity': self.severity_var.get(),
            'artifacts': artifacts_str,
            'doctor_notes': self.txt_notes.get("1.0", tk.END).strip()
        }
        self.pending_changes[self.current_image_path] = data
        self.lbl_status.config(text="Cambios guardados en memoria")

    def restore_selection(self):
        """Restaura la selección desde memoria si existe, sino predice."""
        if self.current_image_path in self.pending_changes:
            data = self.pending_changes[self.current_image_path]
            
            self.study_var.set(data['study_type'])
            self.quality_var.set(data['quality'])
            self.centered_var.set(data['is_centered'])
            self.laterality_var.set(data['laterality'])
            self.diagnosis_var.set(data['diagnosis_detail'])
            self.severity_var.set(data['severity'])
            self.txt_notes.delete("1.0", tk.END)
            self.txt_notes.insert("1.0", data['doctor_notes'])
            
            # Restaurar checkboxes de artefactos
            artifacts = data['artifacts'].split(',')
            self.artifact_blur.set("Blur" in artifacts)
            self.artifact_illumination.set("Illumination" in artifacts)
            self.artifact_obstruction.set("Obstruction" in artifacts)
            
            self.lbl_status.config(text="Datos recuperados de memoria")
        else:
            self.predict_values()

    def predict_values(self):
        """
        Simula el autocompletado por IA.
        Aquí es donde conectarías tu modelo de Machine Learning.
        """
        self.lbl_status.config(text="IA analizando imagen...")
        
        # --- LÓGICA DUMMY (A reemplazar por modelo real) ---
        # En el futuro, aquí cargarías tu modelo y harías model.predict(imagen)
        predicted_study = random.choice([
            "Fondo de Ojo (Centrado en Papila)",
            "Fondo de Ojo (Centrado en Mácula)",
            "OCT Macular",
            "OCT Nervio Óptico"
        ])
        predicted_quality = "Buena" # Asumimos buena por defecto
        is_centered = True
        
        # Autocompletar GUI
        self.study_var.set(predicted_study)
        self.quality_var.set(predicted_quality)
        self.centered_var.set(is_centered)
        self.laterality_var.set("Desconocido")
        self.diagnosis_var.set("Normal")
        self.severity_var.set("N/A")
        self.txt_notes.delete("1.0", tk.END)
        self.artifact_blur.set(False)
        self.artifact_illumination.set(False)
        self.artifact_obstruction.set(False)
        
        self.lbl_status.config(text="Sugerencias de IA cargadas. Por favor revise.")

    def process_batch(self):
        """Guarda todos los cambios pendientes en la BD y mueve archivos."""
        self.save_current_selection() # Asegurar que la actual se guarde
        
        if not self.pending_changes:
            messagebox.showinfo("Info", "No hay cambios pendientes para guardar.")
            return
            
        if not messagebox.askyesno("Confirmar", f"¿Deseas procesar {len(self.pending_changes)} imágenes?"):
            return

        session = self.session()
        count = 0
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        try:
            for file_path, data in self.pending_changes.items():
                # 1. Guardar en BD
                new_record = ImageRecord(
                    filename=os.path.basename(file_path),
                    original_path=file_path,
                    study_type=data['study_type'],
                    quality=data['quality'],
                    is_centered=data['is_centered'],
                    laterality=data['laterality'],
                    diagnosis_detail=data['diagnosis_detail'],
                    severity=data['severity'],
                    artifacts=data['artifacts'],
                    doctor_notes=data['doctor_notes'],
                    validation_status="Validated"
                )
                session.add(new_record)
                
                # 2. Copiar archivo
                copy_file_based_on_quality(file_path, data['quality'], base_dir)
                count += 1
            
            session.commit()
            messagebox.showinfo("Éxito", f"Se procesaron {count} imágenes correctamente.")
            
            # Limpiar
            self.pending_changes.clear()
            self.image_list = [] # Vaciar lista porque los archivos se movieron
            self.image_label.config(image="", text="Lote procesado. Cargar nueva carpeta.")
            self.current_image_path = None
            
        except Exception as e:
            session.rollback()
            messagebox.showerror("Error", f"Ocurrió un error guardando el lote: {e}")
        finally:
            session.close()
