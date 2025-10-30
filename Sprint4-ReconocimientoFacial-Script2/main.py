import cv2
import face_recognition as fr
import os
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import subprocess
import platform

class SistemaAsistencia:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Asistencia con Reconocimiento Facial")
        self.root.geometry("1200x700")
        self.root.configure(bg="#2c3e50")
        
        # Variables
        self.ruta_empleados = "empleados"
        self.archivo_asistencia = "asistencia.csv"
        self.tiempo_espera = 30
        
        self.captura = None
        self.sistema_activo = False
        self.codificaciones_conocidas = []
        self.nombres_empleados = []
        self.ultimo_registro = {}
        
        # Crear carpeta empleados si no existe
        if not os.path.exists(self.ruta_empleados):
            os.makedirs(self.ruta_empleados)
        
        # Crear archivo CSV con encabezado si no existe
        if not os.path.exists(self.archivo_asistencia):
            with open(self.archivo_asistencia, "w") as f:
                f.write("Nombre,Fecha y Hora\n")
        
        self.crear_interfaz()
        self.cargar_base_datos()
    
    def crear_interfaz(self):
        # Frame principal dividido en dos columnas
        frame_izquierdo = tk.Frame(self.root, bg="#34495e", width=300)
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        frame_izquierdo.pack_propagate(False)
        
        frame_derecho = tk.Frame(self.root, bg="#2c3e50")
        frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === PANEL IZQUIERDO (BOTONES) ===
        
        # Título
        titulo = tk.Label(frame_izquierdo, text="CONTROL DE\nASISTENCIA", 
                         font=("Arial", 18, "bold"), bg="#34495e", fg="white")
        titulo.pack(pady=20)
        
        # Estilo de botones
        estilo_boton = {
            "font": ("Arial", 11, "bold"),
            "width": 22,
            "height": 2,
            "relief": tk.RAISED,
            "bd": 3,
            "cursor": "hand2"
        }
        
        # Botón Cargar Alumno
        self.btn_cargar = tk.Button(frame_izquierdo, text="📷 CARGAR ALUMNO", 
                                    bg="#3498db", fg="white",
                                    command=self.cargar_alumno, **estilo_boton)
        self.btn_cargar.pack(pady=10)
        
        # Botón Iniciar/Detener Asistencia
        self.btn_asistencia = tk.Button(frame_izquierdo, text="▶️ INICIAR ASISTENCIA", 
                                       bg="#27ae60", fg="white",
                                       command=self.toggle_asistencia, **estilo_boton)
        self.btn_asistencia.pack(pady=10)
        
        # Botón Ver Registro
        self.btn_registro = tk.Button(frame_izquierdo, text="📊 VER REGISTRO", 
                                     bg="#f39c12", fg="white",
                                     command=self.abrir_registro, **estilo_boton)
        self.btn_registro.pack(pady=10)
        
        # Botón Eliminar Alumno
        self.btn_eliminar = tk.Button(frame_izquierdo, text="🗑️ ELIMINAR ALUMNO", 
                                     bg="#e74c3c", fg="white",
                                     command=self.eliminar_alumno, **estilo_boton)
        self.btn_eliminar.pack(pady=10)
        
        # Botón Recargar Base de Datos
        self.btn_recargar = tk.Button(frame_izquierdo, text="🔄 RECARGAR BASE", 
                                     bg="#9b59b6", fg="white",
                                     command=self.cargar_base_datos, **estilo_boton)
        self.btn_recargar.pack(pady=10)
        
        # Separador
        ttk.Separator(frame_izquierdo, orient='horizontal').pack(fill='x', pady=20)
        
        # Lista de alumnos registrados
        label_alumnos = tk.Label(frame_izquierdo, text="Alumnos Registrados:", 
                                font=("Arial", 10, "bold"), bg="#34495e", fg="white")
        label_alumnos.pack()
        
        self.lista_alumnos = tk.Listbox(frame_izquierdo, height=8, font=("Arial", 9),
                                       bg="#ecf0f1", fg="#2c3e50")
        self.lista_alumnos.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # Botón Salir
        btn_salir = tk.Button(frame_izquierdo, text="❌ SALIR", 
                            bg="#c0392b", fg="white",
                            command=self.salir, **estilo_boton)
        btn_salir.pack(side=tk.BOTTOM, pady=10)
        
        # === PANEL DERECHO (CÁMARA) ===
        
        # Título de la cámara
        titulo_cam = tk.Label(frame_derecho, text="VISTA DE CÁMARA", 
                            font=("Arial", 16, "bold"), bg="#2c3e50", fg="white")
        titulo_cam.pack(pady=10)
        
        # Canvas para mostrar la cámara
        self.canvas = tk.Label(frame_derecho, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Etiqueta de estado
        self.label_estado = tk.Label(frame_derecho, text="Sistema detenido", 
                                    font=("Arial", 12), bg="#2c3e50", fg="#ecf0f1")
        self.label_estado.pack(pady=10)
    
    def cargar_base_datos(self):
        """Carga todas las imágenes de empleados y codifica sus rostros."""
        self.codificaciones_conocidas = []
        self.nombres_empleados = []
        imagenes = []
        
        archivos = [f for f in os.listdir(self.ruta_empleados) 
                   if f.endswith((".jpg", ".png", ".jpeg"))]
        
        if not archivos:
            messagebox.showwarning("Advertencia", "No hay alumnos registrados en la carpeta 'empleados'")
            self.actualizar_lista_alumnos()
            return
        
        for archivo in archivos:
            try:
                img = fr.load_image_file(os.path.join(self.ruta_empleados, archivo))
                imagenes.append(img)
                self.nombres_empleados.append(os.path.splitext(archivo)[0])
            except Exception as e:
                print(f"Error cargando {archivo}: {e}")
        
        # Codificar rostros
        for img in imagenes:
            codigos = fr.face_encodings(img)
            if codigos:
                self.codificaciones_conocidas.append(codigos[0])
        
        self.actualizar_lista_alumnos()
        messagebox.showinfo("Éxito", f"Base de datos cargada: {len(self.nombres_empleados)} alumnos")
    
    def actualizar_lista_alumnos(self):
        """Actualiza la lista visual de alumnos."""
        self.lista_alumnos.delete(0, tk.END)
        for nombre in self.nombres_empleados:
            self.lista_alumnos.insert(tk.END, nombre)
    
    def cargar_alumno(self):
        """Permite seleccionar una imagen y agregarla a la carpeta empleados."""
        archivo = filedialog.askopenfilename(
            title="Seleccionar foto del alumno",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png")]
        )
        
        if archivo:
            nombre = tk.simpledialog.askstring("Nombre", "Ingrese el nombre del alumno:")
            if nombre:
                # Copiar imagen a carpeta empleados
                extension = os.path.splitext(archivo)[1]
                destino = os.path.join(self.ruta_empleados, f"{nombre}{extension}")
                
                # Verificar que la imagen contenga un rostro
                try:
                    img = fr.load_image_file(archivo)
                    encodings = fr.face_encodings(img)
                    
                    if not encodings:
                        messagebox.showerror("Error", "No se detectó ningún rostro en la imagen")
                        return
                    
                    # Copiar archivo
                    import shutil
                    shutil.copy(archivo, destino)
                    
                    messagebox.showinfo("Éxito", f"Alumno '{nombre}' agregado correctamente")
                    self.cargar_base_datos()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al procesar la imagen: {e}")
    
    def eliminar_alumno(self):
        """Elimina un alumno seleccionado de la lista."""
        seleccion = self.lista_alumnos.curselection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un alumno de la lista")
            return
        
        nombre = self.lista_alumnos.get(seleccion[0])
        respuesta = messagebox.askyesno("Confirmar", 
                                       f"¿Está seguro de eliminar a '{nombre}'?")
        
        if respuesta:
            # Buscar y eliminar archivo
            for archivo in os.listdir(self.ruta_empleados):
                if os.path.splitext(archivo)[0] == nombre:
                    os.remove(os.path.join(self.ruta_empleados, archivo))
                    messagebox.showinfo("Éxito", f"Alumno '{nombre}' eliminado")
                    self.cargar_base_datos()
                    break
    
    def toggle_asistencia(self):
        """Inicia o detiene el sistema de asistencia."""
        if not self.sistema_activo:
            if not self.nombres_empleados:
                messagebox.showerror("Error", "Primero debe cargar alumnos a la base de datos")
                return
            
            self.sistema_activo = True
            self.btn_asistencia.config(text="⏸️ DETENER ASISTENCIA", bg="#e74c3c")
            self.label_estado.config(text="Sistema ACTIVO - Reconociendo rostros...", fg="#2ecc71")
            
            # Iniciar cámara en un hilo separado
            self.captura = cv2.VideoCapture(0)
            threading.Thread(target=self.procesar_video, daemon=True).start()
        else:
            self.sistema_activo = False
            self.btn_asistencia.config(text="▶️ INICIAR ASISTENCIA", bg="#27ae60")
            self.label_estado.config(text="Sistema DETENIDO", fg="#e74c3c")
            
            if self.captura:
                self.captura.release()
                self.captura = None
            
            # Limpiar canvas
            self.canvas.config(image='')
    
    def procesar_video(self):
        """Procesa el video de la cámara y detecta rostros."""
        while self.sistema_activo:
            exito, frame = self.captura.read()
            if not exito:
                break
            
            # Procesar reconocimiento facial
            frame_peq = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            frame_rgb = cv2.cvtColor(frame_peq, cv2.COLOR_BGR2RGB)
            
            rostros_frame = fr.face_locations(frame_rgb)
            codificaciones_frame = fr.face_encodings(frame_rgb, rostros_frame)
            
            for cod_rostro, ubicacion in zip(codificaciones_frame, rostros_frame):
                coincidencias = fr.compare_faces(self.codificaciones_conocidas, cod_rostro)
                distancias = fr.face_distance(self.codificaciones_conocidas, cod_rostro)
                
                if len(distancias) > 0:
                    indice_mejor = np.argmin(distancias)
                    nombre = "DESCONOCIDO"
                    
                    if coincidencias[indice_mejor]:
                        nombre = self.nombres_empleados[indice_mejor].upper()
                        
                        # Registrar asistencia
                        ahora = datetime.now()
                        if nombre not in self.ultimo_registro or \
                           (ahora - self.ultimo_registro[nombre]).total_seconds() >= self.tiempo_espera:
                            self.registrar_asistencia(nombre)
                            self.ultimo_registro[nombre] = ahora
                        
                        color = (0, 255, 0)
                    else:
                        color = (0, 0, 255)
                    
                    # Escalar coordenadas
                    y1, x2, y2, x1 = ubicacion
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    
                    # Dibujar
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, nombre, (x1 + 6, y2 - 6), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Convertir frame a formato Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.canvas.imgtk = imgtk
            self.canvas.config(image=imgtk)
    
    def registrar_asistencia(self, nombre):
        """Registra la asistencia en el archivo CSV."""
        with open(self.archivo_asistencia, "a") as f:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{nombre},{ahora}\n")
        print(f"✓ Asistencia registrada: {nombre} - {ahora}")
    
    def abrir_registro(self):
        """Abre el archivo CSV de asistencia."""
        if not os.path.exists(self.archivo_asistencia):
            messagebox.showwarning("Advertencia", "No hay registros de asistencia aún")
            return
        
        sistema = platform.system()
        try:
            if sistema == "Windows":
                os.startfile(self.archivo_asistencia)
            elif sistema == "Darwin":  # macOS
                subprocess.call(["open", self.archivo_asistencia])
            else:  # Linux
                subprocess.call(["xdg-open", self.archivo_asistencia])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
    
    def salir(self):
        """Cierra la aplicación."""
        if self.sistema_activo:
            self.toggle_asistencia()
        
        respuesta = messagebox.askyesno("Salir", "¿Está seguro de salir del sistema?")
        if respuesta:
            self.root.quit()
            self.root.destroy()

# Importar librería de diálogo
import tkinter.simpledialog

# Ejecutar aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaAsistencia(root)
    root.protocol("WM_DELETE_WINDOW", app.salir)
    root.mainloop()