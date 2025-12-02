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
                         background="#a6d0f2", relief=tk.SOLID, borderwidth=1,
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
        self.root.geometry("1200x800")  # Aumentado para mostrar todos los controles
        
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
        left_frame = tk.Frame(self.root, width=550, bg="gray")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # --- Configuración del Scroll para el panel derecho ---
        right_container = tk.Frame(self.root, width=380)
        right_container.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(right_container, width=350)
        scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=canvas.yview)
        
        # Frame interno que contendrá los controles (este es el que usamos como 'right_frame' abajo)
        right_frame = tk.Frame(canvas, padx=20, pady=20)

        # Configurar el scroll
        right_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=right_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Habilitar scroll con rueda del mouse cuando el mouse está sobre el panel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        right_container.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        right_container.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))

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
        self.cb_study = ttk.Combobox(right_frame, textvariable=self.study_var, 
                                     values=[
                                         "Retinografía",
                                         "OCT",
                                         "OCTA",
                                         "Campimetría",
                                         "Fotografía estereoscópica",
                                         "Segmento anterior"
                                     ])
        self.cb_study.pack(fill=tk.X, pady=5)
        ToolTip(self.cb_study, "Seleccione la técnica de imagen utilizada.")

        # Lateralidad
        tk.Label(right_frame, text="Lateralidad:").pack(anchor="w")
        self.laterality_var = tk.StringVar()
        self.cb_laterality = ttk.Combobox(right_frame, textvariable=self.laterality_var, 
                                          values=["OD (Derecho)", "OS (Izquierdo)", "No identificado"])
        self.cb_laterality.pack(fill=tk.X, pady=5)
        ToolTip(self.cb_laterality, "Indique si la imagen corresponde al ojo derecho (OD) o izquierdo (OS).")

        # --- Evaluación Técnica ---
        tk.Label(right_frame, text="Evaluación Técnica", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        # Nitidez
        tk.Label(right_frame, text="Nitidez:").pack(anchor="w")
        self.sharpness_var = tk.StringVar()
        self.cb_sharpness = ttk.Combobox(right_frame, textvariable=self.sharpness_var,
                                         values=["Excelente nitidez", "Buena nitidez", "Borroso leve", "Borroso severo / No útil"])
        self.cb_sharpness.pack(fill=tk.X, pady=2)
        ToolTip(self.cb_sharpness, "Evalúa si los detalles relevantes están bien enfocados.")

        # Iluminación
        tk.Label(right_frame, text="Iluminación:").pack(anchor="w")
        self.illumination_var = tk.StringVar()
        self.cb_illumination = ttk.Combobox(right_frame, textvariable=self.illumination_var,
                                            values=["Bien iluminada", "Sobreexpuesta", "Subexpuesta", "Iluminación irregular"])
        self.cb_illumination.pack(fill=tk.X, pady=2)
        ToolTip(self.cb_illumination, "Confirma si la imagen tiene la exposición correcta.")

        # Centrado
        tk.Label(right_frame, text="Centrado:").pack(anchor="w")
        self.centering_var = tk.StringVar()
        self.cb_centering = ttk.Combobox(right_frame, textvariable=self.centering_var,
                                         values=["Correctamente centrada", "Descentrada hacia nasal", "Descentrada hacia temporal", "Mala composición"])
        self.cb_centering.pack(fill=tk.X, pady=2)
        ToolTip(self.cb_centering, "Valora si la zona relevante está centrada.")

        # Campo de Visión
        tk.Label(right_frame, text="Campo de Visión:").pack(anchor="w")
        self.fov_var = tk.StringVar()
        self.cb_fov = ttk.Combobox(right_frame, textvariable=self.fov_var,
                                   values=["Campo adecuado", "Campo incompleto", "Demasiado cercano", "Demasiado lejano"])
        self.cb_fov.pack(fill=tk.X, pady=2)
        ToolTip(self.cb_fov, "Indica si abarca lo necesario.")

        # --- Problemas ---
        tk.Label(right_frame, text="Problemas", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        # Artefactos (Multi-select simulado con Listbox o Checkboxes)
        # Para simplificar en Tkinter, usaremos checkboxes para los más comunes
        self.art_reflejos = tk.BooleanVar()
        self.art_sombras = tk.BooleanVar()
        self.art_pestanas = tk.BooleanVar()
        self.art_parpadeo = tk.BooleanVar()
        self.art_rota = tk.BooleanVar()

        frame_art = tk.Frame(right_frame)
        frame_art.pack(fill=tk.X)
        tk.Checkbutton(frame_art, text="Reflejos", variable=self.art_reflejos).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(frame_art, text="Sombras", variable=self.art_sombras).grid(row=0, column=1, sticky="w")
        tk.Checkbutton(frame_art, text="Pestañas", variable=self.art_pestanas).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(frame_art, text="Parpadeo", variable=self.art_parpadeo).grid(row=1, column=1, sticky="w")
        tk.Checkbutton(frame_art, text="Img Rota", variable=self.art_rota).grid(row=2, column=0, sticky="w")

        # Obstrucciones
        tk.Label(right_frame, text="Obstrucciones:").pack(anchor="w")
        self.obstruction_var = tk.StringVar()
        self.cb_obstruction = ttk.Combobox(right_frame, textvariable=self.obstruction_var,
                                           values=["Ninguna", "Opacidad de medios", "Miodesopsias", "Sangrado/Hemorragia"])
        self.cb_obstruction.pack(fill=tk.X, pady=2)
        ToolTip(self.cb_obstruction, "Causadas por opacidades, flotadores o sangrado.")

        # --- Conclusión ---
        tk.Label(right_frame, text="Conclusión", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        # Gradabilidad (Calidad Global)
        tk.Label(right_frame, text="Gradabilidad Clínica:").pack(anchor="w")
        self.quality_var = tk.StringVar()
        self.cb_quality = ttk.Combobox(right_frame, textvariable=self.quality_var, 
                                       values=["Grado A (Alta calidad)", "Grado B (Limitada)", "No gradable"])
        self.cb_quality.pack(fill=tk.X, pady=2)
        ToolTip(self.cb_quality, "Clasificación global de la calidad de la imagen.")

        # Utilidad Diagnóstica
        tk.Label(right_frame, text="Utilidad Diagnóstica:").pack(anchor="w")
        self.utility_var = tk.StringVar()
        self.cb_utility = ttk.Combobox(right_frame, textvariable=self.utility_var,
                                       values=["Útil para diagnóstico", "Útil con limitaciones", "No útil"])
        self.cb_utility.pack(fill=tk.X, pady=2)
        ToolTip(self.cb_utility, "El criterio más importante: ¿Sirve para diagnosticar?")

        # Notas Adicionales
        tk.Label(right_frame, text="Notas Adicionales (Opcional):").pack(anchor="w", pady=(10, 0))
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
        if self.art_reflejos.get(): artifacts_list.append("Reflejos")
        if self.art_sombras.get(): artifacts_list.append("Sombras")
        if self.art_pestanas.get(): artifacts_list.append("Pestañas")
        if self.art_parpadeo.get(): artifacts_list.append("Parpadeo")
        if self.art_rota.get(): artifacts_list.append("Img Rota")
        artifacts_str = ",".join(artifacts_list)

        data = {
            'study_type': self.study_var.get(),
            'laterality': self.laterality_var.get(),
            'sharpness': self.sharpness_var.get(),
            'illumination': self.illumination_var.get(),
            'centering': self.centering_var.get(),
            'field_of_view': self.fov_var.get(),
            'artifacts': artifacts_str,
            'obstructions': self.obstruction_var.get(),
            'quality': self.quality_var.get(),
            'diagnostic_utility': self.utility_var.get(),
            'doctor_notes': self.txt_notes.get("1.0", tk.END).strip()
        }
        self.pending_changes[self.current_image_path] = data
        self.lbl_status.config(text="Cambios guardados en memoria")

    def restore_selection(self):
        """Restaura la selección desde memoria si existe, sino predice."""
        if self.current_image_path in self.pending_changes:
            data = self.pending_changes[self.current_image_path]
            
            self.study_var.set(data['study_type'])
            self.laterality_var.set(data['laterality'])
            self.sharpness_var.set(data['sharpness'])
            self.illumination_var.set(data['illumination'])
            self.centering_var.set(data['centering'])
            self.fov_var.set(data['field_of_view'])
            self.obstruction_var.set(data['obstructions'])
            self.quality_var.set(data['quality'])
            self.utility_var.set(data['diagnostic_utility'])
            
            self.txt_notes.delete("1.0", tk.END)
            self.txt_notes.insert("1.0", data['doctor_notes'])
            
            # Restaurar checkboxes de artefactos
            artifacts = data['artifacts'].split(',')
            self.art_reflejos.set("Reflejos" in artifacts)
            self.art_sombras.set("Sombras" in artifacts)
            self.art_pestanas.set("Pestañas" in artifacts)
            self.art_parpadeo.set("Parpadeo" in artifacts)
            self.art_rota.set("Img Rota" in artifacts)
            
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
        
        # Autocompletar GUI con valores por defecto "ideales"
        self.study_var.set(predicted_study)
        self.laterality_var.set("Desconocido")
        
        self.sharpness_var.set("Adecuada")
        self.illumination_var.set("Adecuada")
        self.centering_var.set("Centrada")
        self.fov_var.set("Completo")
        self.obstruction_var.set("Ninguna")
        self.quality_var.set("Aceptable")
        self.utility_var.set("Util")
        
        self.txt_notes.delete("1.0", tk.END)
        
        # Resetear checkboxes
        self.art_reflejos.set(False)
        self.art_sombras.set(False)
        self.art_pestanas.set(False)
        self.art_parpadeo.set(False)
        self.art_rota.set(False)
        
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
                    laterality=data['laterality'],
                    
                    # Nuevos campos técnicos
                    sharpness=data['sharpness'],
                    illumination=data['illumination'],
                    centering=data['centering'],
                    field_of_view=data['field_of_view'],
                    obstructions=data['obstructions'],
                    artifacts=data['artifacts'],
                    
                    # Valoración global
                    quality=data['quality'],
                    diagnostic_utility=data['diagnostic_utility'],
                    
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
