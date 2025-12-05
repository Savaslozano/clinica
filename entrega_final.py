import os
from datetime import date

# Imports opcionales para la interfaz gráfica
try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.messagebox as messagebox
except Exception:
    tk = None
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
    

# Archivos TXT
ARCH_PACIENTES = "pacientes.txt"
ARCH_ENFERMEDADES = "enfermedades.txt"
ARCH_TRATAMIENTOS = "tratamientos.txt"
ARCH_ALERGIAS = "alergias.txt"

# Asegurar existencia de archivos
for _f in [ARCH_PACIENTES, ARCH_ENFERMEDADES, ARCH_TRATAMIENTOS, ARCH_ALERGIAS]:
    if not os.path.exists(_f):
        with open(_f, "w", encoding="utf-8"): # Abre el archivo y lo cierra, para crearlo
            pass

# Normalizar el texto ingresado por el usuario, para no generar conflictos
def _norm(s):
    # Aca implementamos la corrección que se sugirio en la entrega 1
    caracteres = s.split() 

    # Comprobamos si el usuario ingreso números
    if s.replace(" ", "").isdigit():
        numero_completo = "".join(caracteres)
        return numero_completo.strip()
    
    texto_completo = " ".join(caracteres)
    return texto_completo.strip().lower()

# Validar que el nombre contenga solo caracteres alfabéticos
def validar_nombre(nombre):
    nombre = nombre.strip()
    if not nombre:
        return False, None, "El nombre no puede estar vacío."
    if not all(c.isalpha() or c.isspace() for c in nombre):
        return False, None, "El nombre debe contener solo caracteres alfabéticos."
    return True, nombre, ""

# Validar la fecha de nacimiento y calcular edad
def validar_fecha_nac(fecha_str):
    try:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hoy = date.today()
        if fecha >= hoy:
            return False, None, "La fecha de nacimiento debe ser anterior a hoy."
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 0:
            return False, None, "La fecha de nacimiento no es válida."
        return True, fecha.isoformat(), edad
    except ValueError:
        return False, None, "La fecha debe estar en formato AAAA-MM-DD."

# Validar género
def validar_genero(genero):
    genero = genero.strip().upper()
    opciones_validas = ["MASCULINO", "FEMENINO", "NO BINARIO", "PREFIERO NO DECIRLO"]
    if genero not in opciones_validas:
        return False, None, f"El género debe ser uno de: {', '.join(opciones_validas)}."
    return True, genero, ""

# Validar documento (número entero)
def validar_documento(documento):
    documento = _norm(documento)
    if not documento.isdigit():
        return False, None, "El documento debe contener solo números."
    if len(documento) < 5 or len(documento) > 15:
        return False, None, "El documento debe tener entre 5 y 15 dígitos."
    return True, documento, ""

# Validar celular (exactamente 10 dígitos)
def validar_celular(celular, documento=None):
    celular = _norm(celular)
    if not celular.isdigit():
        return False, None, "El celular debe contener solo números."
    if len(celular) != 10:
        return False, None, "El celular debe tener exactamente 10 dígitos."
    # Verificar que no sea igual al documento
    if documento and celular == _norm(documento):
        return False, None, "El celular no puede ser igual al número de documento de identidad."
    return True, celular, ""

# Validar correo electrónico
def validar_correo(correo):
    correo = correo.strip().lower()
    if correo == "":
        return False, None, "El correo no puede estar vacío."
    if "@" not in correo:
        return False, None, "El correo debe contener un '@'."
    partes = correo.split("@")
    if len(partes) != 2:
        return False, None, "El correo debe tener exactamente un '@'."
    usuario, dominio = partes
    if not usuario or not dominio:
        return False, None, "El usuario y dominio del correo no pueden estar vacíos."
    if "." not in dominio:
        return False, None, "El dominio debe contener al menos un punto '.'."
    return True, correo, ""

# Obtener fecha y hora actual en formato ISO
def hoy():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 2025-12-01 14:30:45

# Leer todas las líneas de un archivo como listas de campos separados por "|"
def leer_registros(ruta):
    regs = []
    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()  # Este .strip() es para eliminar el salto de linea invisible de python "\n"
            if linea == "":
                continue  # Esto hace que entre a la siguiente iteracion del for
            regs.append(linea.split("|"))  # El .split() parte un texto en pedacitos y devuelve una lista con esos pedacitos
    return regs

# Reescribir todos los registros a un archivo
def escribir_registros(ruta, registros):  # Registros debe de ser una lista de listas
    with open(ruta, "w", encoding="utf-8") as f:
        for reg in registros:  # Cada reg es por ejemplo ["Ana", "2001-01-01", "F", "10", "300123", "2025-11-04"]
            f.write("|".join(reg) + "\n")  # El .join lo convierte en Ana|2001-01-01|F|10|300123|2025-11-04

# Añadir un único registro (append)
def agregar_registro(ruta, campos):
    with open(ruta, "a", encoding="utf-8") as f:  # Cuando llamo el archivo en modo "a" me escribe justo despues del ultimo byte
        f.write("|".join(campos) + "\n")


# ---------------------------
#  BLOQUE: Pacientes (agregar, editar, consultar)
# ---------------------------

def existe_documento(documento):  # Verificamos si ya existe el documento del paciente en el archivo "ARCH_PACIENTES"
    documento = _norm(documento)
    for reg in leer_registros(ARCH_PACIENTES):
        if _norm(reg[3]) == documento:
            return True
    return False  # Esta función devuelve un True o False dependiendo si el documento del paciente existe o no

def buscar_paciente_por_doc_o_nombre(clave): # Buscar paciente por nombre o documento
    clave_n = _norm(clave)
    lista = leer_registros(ARCH_PACIENTES)

    if not lista:
        return None

    # 1) Buscar por DOCUMENTO (es único y exacto)
    for reg in lista:
        doc = _norm(reg[3])  # documento
        if doc == clave_n:
            return reg

    # 2) Buscar por NOMBRE (búsqueda parcial - coincide si la clave está en el nombre)
    coincidencias = []
    for reg in lista:
        nombre = _norm(reg[0])  # Nombre completo normalizado
        # Dividimos el nombre en palabras para búsqueda flexible
        palabras_nombre = nombre.split()
        
        # Buscamos si la clave coincide exactamente con todo el nombre
        if nombre == clave_n:
            coincidencias.append(reg)
        # O si la clave coincide con alguna palabra individual (nombre o apellido)
        elif any(clave_n in palabra or palabra in clave_n for palabra in palabras_nombre):
            coincidencias.append(reg)

    # Si no hay nadie con ese nombre
    if not coincidencias:
        return None

    # Si solo hay uno con ese nombre, listo
    if len(coincidencias) == 1:
        return coincidencias[0]

    # Si hay varios con el mismo nombre: pedir que elija por documento
    print("\nHay varios pacientes que coinciden con tu búsqueda. Elige por documento:")
    for reg in coincidencias:
        print(f"- Nombre: {reg[0]} | Documento: {reg[3]} | Celular: {reg[4]}")

    doc_elegido = _norm(input("Escribe el documento exacto del paciente que quieres: "))

    for reg in coincidencias:  # Buscamos al paciente por numero de documento
        if _norm(reg[3]) == doc_elegido:
            return reg

    print(">>> Documento no coincide con la lista mostrada.")
    return None

def agregar_paciente():
    print("\n--- Agregar Paciente ---")
    
    # Validar nombre
    while True:
        nombre_input = input("Nombre completo: ")
        valido, resultado, error_msg = validar_nombre(nombre_input)
        if valido:
            nombre = _norm(resultado)
            break
        else:
            print(f">>> Error: {error_msg}")
    
    # Validar fecha de nacimiento
    while True:
        fecha_nac_input = input("Fecha de nacimiento (AAAA-MM-DD): ").strip()
        valido, fecha_nac, resultado_msg = validar_fecha_nac(fecha_nac_input)
        if valido:
            edad = resultado_msg
            break
        else:
            print(f">>> Error: {resultado_msg}")
    
    # Validar género
    while True:
        genero_input = input("Género (Masculino/Femenino/No binario/Prefiero no decirlo): ").strip()
        valido, genero, error_msg = validar_genero(genero_input)
        if valido:
            break
        else:
            print(f">>> Error: {error_msg}")
    
    # Validar documento
    while True:
        documento_input = input("Número de identificación: ")
        valido, documento, error_msg = validar_documento(documento_input)
        if valido:
            # Verificamos si el documento ya existe
            if existe_documento(documento):
                print(">>> Ya existe un paciente con ese documento.")
                continue
            break
        else:
            print(f">>> Error: {error_msg}")
    
    # Validar celular
    while True:
        celular_input = input("Celular de contacto (10 dígitos): ")
        valido, celular, error_msg = validar_celular(celular_input, documento)
        if valido:
            break
        else:
            print(f">>> Error: {error_msg}")
    
    # Validar correo
    while True:
        correo_input = input("Correo electrónico (usuario@dominio.com): ")
        valido, correo, error_msg = validar_correo(correo_input)
        if valido:
            break
        else:
            print(f">>> Error: {error_msg}")
    
    fecha_reg = hoy()

    # Guardar paciente con nuevo formato: nombre|fecha_nacimiento|genero|documento|celular|correo|edad|fecha_registro
    agregar_registro(ARCH_PACIENTES, [nombre, fecha_nac, genero, documento, celular, correo, str(edad), fecha_reg])
    print(">>> Paciente agregado correctamente.")

def editar_paciente():
    print("\n--- Editar Paciente ---")
    clave = input("Documento o nombre del paciente a editar: ").strip()
    reg = buscar_paciente_por_doc_o_nombre(clave)
    if reg is None:
        print(">>> Paciente no encontrado.")
        return

    doc_original = reg[3]

    print("\nDatos actuales:")
    print(f"Nombre: {reg[0]}")
    print(f"Fecha nac.: {reg[1]}")
    print(f"Género: {reg[2]}")
    print(f"Documento: {reg[3]}")
    print(f"Celular: {reg[4]}")
    print(f"Correo: {reg[5]}")
    print(f"Edad: {reg[6]}")
    print(f"Fecha registro: {reg[7]}")

    nuevo_nombre = input("Nuevo nombre (Enter para mantener): ").strip()
    if nuevo_nombre != "":
        valido, resultado, error_msg = validar_nombre(nuevo_nombre)
        if valido:
            reg[0] = _norm(resultado)
        else:
            print(f">>> Error: {error_msg}")
            return

    nueva_fecha = input("Nueva fecha nac. (Enter para mantener): ").strip()
    if nueva_fecha != "":
        valido, fecha, msg = validar_fecha_nac(nueva_fecha)
        if valido:
            reg[1] = fecha
            reg[6] = str(msg)  # Actualizar edad
        else:
            print(f">>> Error: {msg}")
            return

    nuevo_genero = input("Nuevo género (Enter para mantener): ").strip()
    if nuevo_genero != "":
        valido, genero, error_msg = validar_genero(nuevo_genero)
        if valido:
            reg[2] = genero
        else:
            print(f">>> Error: {error_msg}")
            return

    nuevo_doc = input("Nuevo documento (Enter para mantener): ").strip()
    if nuevo_doc != "":
        valido, documento, error_msg = validar_documento(nuevo_doc)
        if valido:
            if documento != doc_original and existe_documento(documento):
                print(">>> No se puede cambiar: el documento nuevo ya existe.")
                return
            reg[3] = documento
        else:
            print(f">>> Error: {error_msg}")
            return

    nuevo_cel = input("Nuevo celular (Enter para mantener): ").strip()
    if nuevo_cel != "":
        # Usar el documento actualizado si fue modificado, sino usar el original
        doc_para_validar = reg[3]
        valido, celular, error_msg = validar_celular(nuevo_cel, doc_para_validar)
        if valido:
            reg[4] = celular
        else:
            print(f">>> Error: {error_msg}")
            return

    nuevo_correo = input("Nuevo correo (Enter para mantener): ").strip()
    if nuevo_correo != "":
        valido, correo, error_msg = validar_correo(nuevo_correo)
        if valido:
            reg[5] = correo
        else:
            print(f">>> Error: {error_msg}")
            return

    todos = leer_registros(ARCH_PACIENTES)
    for i in range(len(todos)):
        if _norm(todos[i][3]) == _norm(doc_original):
            todos[i] = reg
            break

    escribir_registros(ARCH_PACIENTES, todos)
    print(">>> Paciente actualizado.")

def mostrar_historial(documento):
    print("\n--- Historial Médico ---")

    # Enfermedades
    enf = []
    for r in leer_registros(ARCH_ENFERMEDADES):  # Leemos todas las enfermedades y agregamos a la lista las que coinciden con el paciente
        if _norm(r[0]) == _norm(documento):
            enf.append(r)  # Agregamos a enf para poder mostrarlas en pantalla mas adelante

    print("\nEnfermedades:")
    if enf:  # Comprobamos que enf no este vacia
        for e in enf:
            print(f"- {e[3]} | {e[2]} (síntomas: {e[1]})")
    else:
        print("- Sin registros")

    # Tratamientos
    tra = []
    for r in leer_registros(ARCH_TRATAMIENTOS):
        if _norm(r[0]) == _norm(documento):
            tra.append(r)

    print("\nTratamientos:")
    if tra:
        for t in tra:
            print(f"- {t[3]} | {t[1]} (dosis: {t[2]})")
    else:
        print("- Sin registros")

    # Alergias
    ale = []
    for r in leer_registros(ARCH_ALERGIAS):
        if _norm(r[0]) == _norm(documento):
            ale.append(r)

    print("\nAlergias:")
    if ale:
        for a in ale:
            print(f"- {a[3]} | {a[1]} (síntomas: {a[2]})")
    else:
        print("- Sin registros")

def listar_pacientes():
    print("\n--- Listar Pacientes ---")
    pacientes = leer_registros(ARCH_PACIENTES)
    if not pacientes:
        print(">>> No hay pacientes registrados.")
        return
    
    print("\nOpciones de ordenamiento:")
    print("1. Ordenar por fecha de registro (más reciente primero)")
    print("2. Ordenar por documento de identidad (ascendente)")
    opcion = input("Selecciona una opción: ").strip()
    
    if opcion == "1":
        # Ordenar por fecha de registro (índice 7)
        pacientes.sort(key=lambda x: x[7], reverse=True)
    elif opcion == "2":
        # Ordenar por documento (índice 3)
        pacientes.sort(key=lambda x: x[3])
    else:
        print(">>> Opción inválida.")
        return
    
    print("\n" + "="*100)
    print(f"{'Documento':<15} {'Nombre':<30} {'Género':<15} {'Edad':<8} {'Celular':<12} {'Fecha Registro':<15}")
    print("="*100)
    for p in pacientes:
        documento = p[3]
        nombre = p[0]
        genero = p[2]
        edad = p[6]
        celular = p[4]
        fecha_reg = p[7]
        print(f"{documento:<15} {nombre:<30} {genero:<15} {edad:<8} {celular:<12} {fecha_reg:<15}")
    print("="*100)

def consultar_paciente():
    print("\n--- Consultar Paciente ---")
    clave = input("Documento o nombre del paciente: ").strip()
    reg = buscar_paciente_por_doc_o_nombre(clave)
    if reg is None:
        print(">>> Paciente no encontrado.")
        return

    print("\nDatos del paciente:")
    print(f"Nombre: {reg[0]}")
    print(f"Fecha nac.: {reg[1]}")
    print(f"Género: {reg[2]}")
    print(f"Documento: {reg[3]}")
    print(f"Celular: {reg[4]}")
    print(f"Correo: {reg[5]}")
    print(f"Edad: {reg[6]} años")
    print(f"Fecha registro: {reg[7]}")

    mostrar_historial(reg[3])

    # Submenú (5, 6, 7)
    while True:
        print("\n--- Opciones ---")
        print("5. Agregar Enfermedad (diagnóstico automático)")
        print("6. Agregar Tratamiento")
        print("7. Agregar Alergia")
        print("0. Volver")
        op = input("Opción: ").strip()
        if op == "5":
            agregar_enfermedad(reg[3])
        elif op == "6":
            agregar_tratamiento(reg[3])
        elif op == "7":
            agregar_alergia(reg[3])
        elif op == "0":
            break
        else:
            print(">>> Opción inválida.")


# ---------------------------
#  BLOQUE: Enfermedad / Tratamiento / Alergia
# ---------------------------

# Diccionario de sintomas -> enfermedad
recetas = {
    ("fiebre", "tos", "dificultad para respirar"): "COVID-19",
    ("dolor de cabeza", "rigidez en el cuello", "fiebre"): "Meningitis",
    ("nauseas", "vomitos", "dolor abdominal"): "Gastroenteritis",
    ("dolor de garganta", "tos", "congestion nasal"): "Resfriado común",
    ("fiebre", "sarpullido", "ojos rojos"): "Sarampión",
    ("dolor de pecho", "dificultad para respirar", "sudoracion excesiva"): "Ataque al corazón",
    ("dolor abdominal", "ictericia", "fatiga"): "Hepatitis",
    ("picazon", "erupcion", "hinchazon"): "Reacción alérgica",
    ("dolor de oido", "drenaje del oido", "perdida de audicion"): "Infección de oído",
    ("fiebre", "escalofrios", "dolor muscular"): "Gripe",
    ("dolor en el pecho", "mareos", "palpitaciones"): "Problema cardíaco",
    ("perdida de apetito", "perdida de peso", "fatiga extrema"): "Trastorno metabólico",
    ("dolor de espalda", "dolor en las piernas", "entumecimiento"): "Problema nervioso o muscular",
    ("perdida de memoria", "confusion", "dificultad para hablar"): "Derrame cerebral",
    ("fatiga", "depresion", "aumento de peso"): "Hipotiroidismo",
    ("sed excesiva", "frecuencia urinaria", "vision borrosa"): "Diabetes",
    ("tos persistente", "perdida de peso", "sudores nocturnos"): "Tuberculosis",
    ("dolor articular", "rigidez", "hinchazon"): "Artritis",
    ("fatiga extrema", "falta de aliento", "dolor en el pecho"): "Anemia",
    ("vision borrosa", "dolor ocular", "enrojecimiento"): "Infección ocular o Glaucoma",
}

# Función de consulta (se mantiene igual que en la Entrega 1, cambiando los print por return)
def diagnosticar(sintoma1, sintoma2, sintoma3):
    clave1 = (sintoma1, sintoma2, sintoma3)
    clave2 = (sintoma1, sintoma3, sintoma2)
    clave3 = (sintoma2, sintoma1, sintoma3)
    clave4 = (sintoma2, sintoma3, sintoma1)
    clave5 = (sintoma3, sintoma1, sintoma2)
    clave6 = (sintoma3, sintoma2, sintoma1)

    if clave1 in recetas:
        return recetas[clave1]
    elif clave2 in recetas:
        return recetas[clave2]
    elif clave3 in recetas:
        return recetas[clave3]
    elif clave4 in recetas:
        return recetas[clave4]
    elif clave5 in recetas:
        return recetas[clave5]
    elif clave6 in recetas:
        return recetas[clave6]
    else:
        return "No determinada"

def agregar_enfermedad(documento):
    print("\n--- Agregar Enfermedad (síntomas sin tildes) ---")
    s1 = _norm(input("Síntoma 1: "))
    s2 = _norm(input("Síntoma 2: "))
    s3 = _norm(input("Síntoma 3: "))

    nombre_enf = diagnosticar(s1, s2, s3)
    fecha_reg = hoy()
    sintomas_str = f"{s1},{s2},{s3}"

    agregar_registro(ARCH_ENFERMEDADES, [documento, sintomas_str, nombre_enf, fecha_reg])
    print(f">>> Enfermedad registrada: {nombre_enf}")

def agregar_tratamiento(documento):
    print("\n--- Agregar Tratamiento ---")
    meds = input("Medicamentos (separados por comas): ").strip()
    dosis = input("Dosis de cada medicamento (mismo orden, separadas por comas): ").strip()
    fecha_reg = hoy()
    agregar_registro(ARCH_TRATAMIENTOS, [documento, meds, dosis, fecha_reg])
    print(">>> Tratamiento registrado.")

def agregar_alergia(documento):
    print("\n--- Agregar Alergia ---")
    alergeno = input("Alérgeno: ").strip()
    sintomas = input("Síntomas (separados por comas, sin tildes): ").strip().lower()
    fecha_reg = hoy()
    agregar_registro(ARCH_ALERGIAS, [documento, alergeno, sintomas, fecha_reg])
    print(">>> Alergia registrada.")


# ---------------------------
#  BLOQUE: Menú principal
# ---------------------------
def menu_principal():
    while True:
        print("\n========================================")
        print("      SISTEMA MÉDICO - CENTRO SALUD     ")
        print("========================================")
        print("1. Listar pacientes")
        print("2. Agregar paciente")
        print("3. Editar paciente")
        print("4. Consultar paciente")
        print("0. Salir")
        op = input("Opción: ").strip()

        if op == "1":
            listar_pacientes()
        elif op == "2":
            agregar_paciente()
        elif op == "3":
            editar_paciente()
        elif op == "4":
            consultar_paciente()
        elif op == "0":
            print(">>> Saliendo. Gracias por usar el sistema.")
            break
        else:
            print(">>> Opción inválida. Intente de nuevo.")

# Punto de entrada: preferir interfaz gráfica si está disponible
if __name__ == "__main__":
    # Si tkinter no está disponible, usar menú de consola
    if tk is None:
        menu_principal()
    else:
        try:
            root = tk.Tk()
            root.title("Sistema de Almacenamiento de Pacientes")
            root.iconbitmap(default='icono.ico')
            root.geometry("500x400")
            root.resizable(False, False)
            

            # Funciones de los botones
            def on_agregar():
                # Evitar abrir más de una ventana de agregar paciente
                if getattr(root, "_agregar_open", False):
                    messagebox.showwarning("Atención", "La ventana de 'Agregar Paciente' ya está abierta.")
                    return
                root._agregar_open = True

                # Ventana para agregar paciente (formulario)
                win = tk.Toplevel(root)
                win.title("Agregar Paciente")
                win.geometry("600x520")

                def on_close_agregar():
                    root._agregar_open = False
                    win.destroy()

                win.protocol("WM_DELETE_WINDOW", on_close_agregar)

                frm = tk.Frame(win, padx=20, pady=10)
                frm.pack(fill="both", expand=True)

                # Campos
                lbl_nombres = tk.Label(frm, text="Nombres")
                lbl_nombres.grid(row=0, column=0, sticky="w", pady=6)
                ent_nombres = tk.Entry(frm, width=40)
                ent_nombres.grid(row=0, column=1, pady=6)

                lbl_apellidos = tk.Label(frm, text="Apellidos")
                lbl_apellidos.grid(row=1, column=0, sticky="w", pady=6)
                ent_apellidos = tk.Entry(frm, width=40)
                ent_apellidos.grid(row=1, column=1, pady=6)

                lbl_documento = tk.Label(frm, text="Documento")
                lbl_documento.grid(row=2, column=0, sticky="w", pady=6)
                ent_documento = tk.Entry(frm, width=40)
                ent_documento.grid(row=2, column=1, pady=6)

                lbl_fecha = tk.Label(frm, text="Fecha de nacimiento (AAAA-MM-DD)")
                lbl_fecha.grid(row=3, column=0, sticky="w", pady=6)
                ent_fecha = tk.Entry(frm, width=40)
                ent_fecha.grid(row=3, column=1, pady=6)

                lbl_genero = tk.Label(frm, text="Género")
                lbl_genero.grid(row=4, column=0, sticky="w", pady=6)
                cb_genero = ttk.Combobox(frm, values=["Masculino", "Femenino", "No binario", "Prefiero no decirlo"], state="readonly", width=37)
                cb_genero.grid(row=4, column=1, pady=6)
                cb_genero.current(0)

                lbl_celular = tk.Label(frm, text="Celular")
                lbl_celular.grid(row=5, column=0, sticky="w", pady=6)
                ent_celular = tk.Entry(frm, width=40)
                ent_celular.grid(row=5, column=1, pady=6)

                lbl_correo = tk.Label(frm, text="Correo electrónico")
                lbl_correo.grid(row=6, column=0, sticky="w", pady=6)
                ent_correo = tk.Entry(frm, width=40)
                ent_correo.grid(row=6, column=1, pady=6)

                def guardar_paciente():
                    # Reunir valores
                    nombres = ent_nombres.get().strip()
                    apellidos = ent_apellidos.get().strip()
                    documento_raw = ent_documento.get().strip()
                    fecha_raw = ent_fecha.get().strip()
                    genero_sel = cb_genero.get().strip()
                    celular_raw = ent_celular.get().strip()
                    correo_raw = ent_correo.get().strip()

                    # Validaciones
                    nombre_completo = f"{nombres} {apellidos}".strip()
                    valido, resultado_nombre, msg = validar_nombre(nombre_completo)
                    if not valido:
                        # msg ahora contiene el texto de error (alineado con otras validaciones)
                        messagebox.showerror("Error", msg)
                        return
                    nombre_final = _norm(resultado_nombre)

                    valido, fecha_nac, edad = validar_fecha_nac(fecha_raw)
                    if not valido:
                        messagebox.showerror("Error", fecha_nac if fecha_nac else edad)
                        return

                    # Mapear género a formato esperado
                    mapa_genero = {
                        "Masculino": "MASCULINO",
                        "Femenino": "FEMENINO",
                        "No binario": "NO BINARIO",
                        "Prefiero no decirlo": "PREFIERO NO DECIRLO",
                    }
                    genero_mapped = mapa_genero.get(genero_sel, genero_sel)
                    valido, genero_final, msg = validar_genero(genero_mapped)
                    if not valido:
                        messagebox.showerror("Error", msg)
                        return

                    valido, documento_final, msg = validar_documento(documento_raw)
                    if not valido:
                        messagebox.showerror("Error", msg)
                        return
                    if existe_documento(documento_final):
                        messagebox.showerror("Error", "Ya existe un paciente con ese documento.")
                        return

                    valido, celular_final, msg = validar_celular(celular_raw, documento_final)
                    if not valido:
                        messagebox.showerror("Error", msg)
                        return

                    valido, correo_final, msg = validar_correo(correo_raw)
                    if not valido:
                        messagebox.showerror("Error", msg)
                        return

                    fecha_reg = hoy()
                    agregar_registro(ARCH_PACIENTES, [nombre_final, fecha_nac, genero_final, documento_final, celular_final, correo_final, str(edad), fecha_reg])
                    messagebox.showinfo("Éxito", "Paciente agregado correctamente.")
                    # marcar que ya no está abierta antes de cerrar
                    root._agregar_open = False
                    win.destroy()

                btn_guardar = tk.Button(frm, text="Botón Guardar Paciente", bg="#2A6F9E", fg="white", width=25, height=2, command=guardar_paciente)
                btn_guardar.grid(row=7, column=1, pady=20, sticky="e")

            def on_consultar():
                win = tk.Toplevel(root)
                win.title("Consultar Paciente")
                win.geometry("640x420")

                frm = tk.Frame(win, padx=20, pady=10)
                frm.pack(fill="both", expand=True)

                lbl_doc = tk.Label(frm, text="Buscar por documento")
                lbl_doc.grid(row=0, column=0, sticky="w", pady=8)
                ent_doc = tk.Entry(frm, width=40)
                ent_doc.grid(row=0, column=1, pady=8)

                lbl_nom = tk.Label(frm, text="Buscar por nombre")
                lbl_nom.grid(row=1, column=0, sticky="w", pady=8)
                ent_nom = tk.Entry(frm, width=40)
                ent_nom.grid(row=1, column=1, pady=8)

                lbl_ape = tk.Label(frm, text="Buscar por apellido")
                lbl_ape.grid(row=2, column=0, sticky="w", pady=8)
                ent_ape = tk.Entry(frm, width=40)
                ent_ape.grid(row=2, column=1, pady=8)

                # Area para mostrar resultados
                result_frame = tk.Frame(frm)
                result_frame.grid(row=4, column=0, columnspan=2, pady=12, sticky="nsew")
                frm.rowconfigure(4, weight=1)
                frm.columnconfigure(1, weight=1)

                tree = ttk.Treeview(result_frame, columns=("doc","nombre","genero","edad"), show="headings", height=6)
                tree.heading("doc", text="Documento")
                tree.heading("nombre", text="Nombre completo")
                tree.heading("genero", text="Género")
                tree.heading("edad", text="Edad")
                tree.column("doc", width=100, anchor="center")
                tree.column("nombre", width=260)
                tree.column("genero", width=120, anchor="center")
                tree.column("edad", width=60, anchor="center")
                tree.pack(side="left", fill="both", expand=True)

                scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
                tree.configure(yscroll=scrollbar.set)
                scrollbar.pack(side="right", fill="y")

                def mostrar_detalle_seleccion(event=None):
                    sel = tree.selection()
                    if not sel:
                        return
                    item = tree.item(sel[0])
                    doc = item["values"][0]
                    # Buscar registro completo
                    detalle = None
                    for p in leer_registros(ARCH_PACIENTES):
                        if _norm(p[3]) == _norm(str(doc)):
                            detalle = p
                            break
                    if detalle is None:
                        messagebox.showerror("Error", "Paciente no encontrado")
                        return

                    det_win = tk.Toplevel(win)
                    det_win.title("Detalle del paciente")
                    det_win.geometry("560x620")
                    # Separar nombre en nombres y apellidos si es posible
                    parts = detalle[0].split()
                    if len(parts) > 1:
                        apellidos = parts[-1]
                        nombres = " ".join(parts[:-1])
                    else:
                        nombres = detalle[0]
                        apellidos = ""
                    df = tk.Frame(det_win, padx=12, pady=12)
                    df.pack(fill="both", expand=True)
                    info_frame = tk.Frame(df)
                    info_frame.pack(pady=8)
                    labels = [
                        ("Documento:", detalle[3]),
                        ("Nombres:", nombres),
                        ("Apellidos:", apellidos),
                        ("Fecha de nacimiento:", detalle[1]),
                        ("Edad:", f"{detalle[6]}"),
                        ("Género:", detalle[2]),
                        ("Celular:", detalle[4]),
                        ("Correo electrónico:", detalle[5]),
                    ]
                    for i, (lab, val) in enumerate(labels):
                        tk.Label(info_frame, text=lab, font=(None, 10, 'bold')).grid(row=i, column=0, sticky='e', padx=(0,8), pady=6)
                        tk.Label(info_frame, text=val).grid(row=i, column=1, sticky='w', pady=6)
                    # Historial
                    hist_frame = tk.Frame(df)
                    hist_frame.pack(fill='both', expand=True, pady=(12,6))
                    # Enfermedades
                    tk.Label(hist_frame, text="Enfermedades:", font=(None, 10, 'bold')).pack(anchor='w')
                    enf_list = tk.Frame(hist_frame)
                    enf_list.pack(fill='x', pady=(2,8))
                    enf = [r for r in leer_registros(ARCH_ENFERMEDADES) if _norm(r[0]) == _norm(detalle[3])]
                    if enf:
                        for e in enf:
                            tk.Label(enf_list, text=f"{e[3]}    {e[2]}").pack(anchor='w')
                    else:
                        tk.Label(enf_list, text="Sin registros").pack(anchor='w')
                    # Tratamientos
                    tk.Label(hist_frame, text="Tratamientos:", font=(None, 10, 'bold')).pack(anchor='w')
                    tra_list = tk.Frame(hist_frame)
                    tra_list.pack(fill='x', pady=(2,8))
                    tra = [r for r in leer_registros(ARCH_TRATAMIENTOS) if _norm(r[0]) == _norm(detalle[3])]
                    if tra:
                        for t in tra:
                            tk.Label(tra_list, text=f"{t[3]}    {t[1]}").pack(anchor='w')
                    else:
                        tk.Label(tra_list, text="Sin registros").pack(anchor='w')
                    # Alergias
                    tk.Label(hist_frame, text="Alergias:", font=(None, 10, 'bold')).pack(anchor='w')
                    ale_list = tk.Frame(hist_frame)
                    ale_list.pack(fill='x', pady=(2,8))
                    ale = [r for r in leer_registros(ARCH_ALERGIAS) if _norm(r[0]) == _norm(detalle[3])]
                    if ale:
                        for a in ale:
                            tk.Label(ale_list, text=f"{a[3]}    {a[1]}").pack(anchor='w')
                    else:
                        tk.Label(ale_list, text="Sin registros").pack(anchor='w')
                    # Botones inferiores
                    btns = tk.Frame(df)
                    btns.pack(fill='x', pady=(12,0))
                    def open_edit():
                        edit_win = tk.Toplevel(det_win)
                        edit_win.title("Editar Paciente")
                        edit_win.geometry("540x420")
                        ef = tk.Frame(edit_win, padx=12, pady=12)
                        ef.pack(fill='both', expand=True)
                        # Campos prefijados
                        tk.Label(ef, text="Nombres").grid(row=0, column=0, sticky='w')
                        e_nombres = tk.Entry(ef, width=40)
                        e_nombres.grid(row=0, column=1, pady=6)
                        e_nombres.insert(0, nombres)
                        tk.Label(ef, text="Apellidos").grid(row=1, column=0, sticky='w')
                        e_apellidos = tk.Entry(ef, width=40)
                        e_apellidos.grid(row=1, column=1, pady=6)
                        e_apellidos.insert(0, apellidos)
                        tk.Label(ef, text="Documento").grid(row=2, column=0, sticky='w')
                        e_documento = tk.Entry(ef, width=40)
                        e_documento.grid(row=2, column=1, pady=6)
                        e_documento.insert(0, detalle[3])
                        tk.Label(ef, text="Fecha de nacimiento (AAAA-MM-DD)").grid(row=3, column=0, sticky='w')
                        e_fecha = tk.Entry(ef, width=40)
                        e_fecha.grid(row=3, column=1, pady=6)
                        e_fecha.insert(0, detalle[1])
                        tk.Label(ef, text="Género").grid(row=4, column=0, sticky='w')
                        e_genero = ttk.Combobox(ef, values=["Masculino", "Femenino", "No binario", "Prefiero no decirlo"], state='readonly', width=37)
                        e_genero.grid(row=4, column=1, pady=6)
                        # map back to readable
                        gen_map_rev = {"MASCULINO":"Masculino","FEMENINO":"Femenino","NO BINARIO":"No binario","PREFIERO NO DECIRLO":"Prefiero no decirlo"}
                        e_genero.set(gen_map_rev.get(detalle[2], detalle[2]))
                        tk.Label(ef, text="Celular").grid(row=5, column=0, sticky='w')
                        e_cel = tk.Entry(ef, width=40)
                        e_cel.grid(row=5, column=1, pady=6)
                        e_cel.insert(0, detalle[4])
                        tk.Label(ef, text="Correo electrónico").grid(row=6, column=0, sticky='w')
                        e_cor = tk.Entry(ef, width=40)
                        e_cor.grid(row=6, column=1, pady=6)
                        e_cor.insert(0, detalle[5])
                        def guardar_edicion():
                            nuevo_nombres = e_nombres.get().strip()
                            nuevo_apellidos = e_apellidos.get().strip()
                            nuevo_doc_raw = e_documento.get().strip()
                            nuevo_fecha = e_fecha.get().strip()
                            nuevo_genero_sel = e_genero.get().strip()
                            nuevo_cel = e_cel.get().strip()
                            nuevo_correo = e_cor.get().strip()
                            nombre_completo = f"{nuevo_nombres} {nuevo_apellidos}".strip()
                            valido, res_nom, msg = validar_nombre(nombre_completo)
                            if not valido:
                                messagebox.showerror("Error", msg)
                                return
                            nombre_final = _norm(res_nom)
                            valido, fecha_iso, edad_calc = validar_fecha_nac(nuevo_fecha)
                            if not valido:
                                messagebox.showerror("Error", fecha_iso if fecha_iso else edad_calc)
                                return
                            mapa_genero = {
                                "Masculino": "MASCULINO",
                                "Femenino": "FEMENINO",
                                "No binario": "NO BINARIO",
                                "Prefiero no decirlo": "PREFIERO NO DECIRLO",
                            }
                            genero_mapped = mapa_genero.get(nuevo_genero_sel, nuevo_genero_sel)
                            valido, genero_final, msg = validar_genero(genero_mapped)
                            if not valido:
                                messagebox.showerror("Error", msg)
                                return
                            valido, documento_final, msg = validar_documento(nuevo_doc_raw)
                            if not valido:
                                messagebox.showerror("Error", msg)
                                return
                            # comprobar conflicto si cambia documento
                            if documento_final != detalle[3] and existe_documento(documento_final):
                                messagebox.showerror("Error", "Ya existe un paciente con ese documento.")
                                return
                            valido, celular_final, msg = validar_celular(nuevo_cel, documento_final)
                            if not valido:
                                messagebox.showerror("Error", msg)
                                return
                            valido, correo_final, msg = validar_correo(nuevo_correo)
                            if not valido:
                                messagebox.showerror("Error", msg)
                                return
                            # Actualizar registro
                            todos = leer_registros(ARCH_PACIENTES)
                            for i in range(len(todos)):
                                if _norm(todos[i][3]) == _norm(detalle[3]):
                                    todos[i] = [nombre_final, fecha_iso, genero_final, documento_final, celular_final, correo_final, str(edad_calc), todos[i][7]]
                                    break
                            escribir_registros(ARCH_PACIENTES, todos)
                            messagebox.showinfo("Éxito", "Paciente actualizado.")
                            edit_win.destroy()
                            det_win.destroy()
                        tk.Button(ef, text="Guardar cambios", bg="#2A6F9E", fg="white", command=guardar_edicion).grid(row=7, column=1, sticky='e', pady=12)
                    def add_enfermedad_gui():
                        ae = tk.Toplevel(det_win)
                        ae.title("Nueva enfermedad")
                        ae.geometry("560x220")
                        f = tk.Frame(ae, padx=12, pady=12)
                        f.pack(fill='both', expand=True)

                        tk.Label(f, text="Fecha").grid(row=0, column=0, sticky='w')
                        ent_fecha = tk.Entry(f, width=20)
                        ent_fecha.grid(row=0, column=1, pady=6, sticky='w')
                        from datetime import date as _date
                        ent_fecha.insert(0, _date.today().isoformat())

                        tk.Label(f, text="Síntoma 1").grid(row=0, column=2, sticky='w')
                        s1 = tk.Entry(f, width=30); s1.grid(row=0, column=3, pady=6)
                        tk.Label(f, text="Síntoma 2").grid(row=1, column=2, sticky='w')
                        s2 = tk.Entry(f, width=30); s2.grid(row=1, column=3, pady=6)
                        tk.Label(f, text="Síntoma 3").grid(row=2, column=2, sticky='w')
                        s3 = tk.Entry(f, width=30); s3.grid(row=2, column=3, pady=6)

                        diag_lbl = tk.Label(f, text="El diagnóstico es: No determinada")
                        diag_lbl.grid(row=3, column=0, columnspan=4, sticky='w', pady=(8,0))

                        def diagnosticar_y_mostrar():
                            q1 = _norm(s1.get().strip())
                            q2 = _norm(s2.get().strip())
                            q3 = _norm(s3.get().strip())
                            nombre_enf = diagnosticar(q1, q2, q3)
                            diag_lbl.config(text=f"El diagnóstico es: {nombre_enf}")
                            return nombre_enf

                        def guardar_enf():
                            nombre_enf = diagnosticar_y_mostrar()
                            fecha_reg = ent_fecha.get().strip() or hoy()
                            sintomas_str = f"{_norm(s1.get().strip())},{_norm(s2.get().strip())},{_norm(s3.get().strip())}"
                            agregar_registro(ARCH_ENFERMEDADES, [detalle[3], sintomas_str, nombre_enf, fecha_reg])
                            messagebox.showinfo("Éxito", "Enfermedad registrada.")
                            ae.destroy()

                        tk.Button(f, text="Diagnosticar", bg="#2A6F9E", fg='white', command=diagnosticar_y_mostrar).grid(row=2, column=0, sticky='w', pady=6)
                        tk.Button(f, text="Agregar Enfermedad", bg="#2A6F9E", fg='white', command=guardar_enf).grid(row=4, column=3, sticky='e', pady=8)

                    def add_tratamiento_gui():
                        at = tk.Toplevel(det_win)
                        at.title("Nuevo tratamiento")
                        at.geometry("560x200")
                        f = tk.Frame(at, padx=12, pady=12)
                        f.pack(fill='both', expand=True)

                        tk.Label(f, text="Fecha").grid(row=0, column=0, sticky='w')
                        ent_fecha = tk.Entry(f, width=20); ent_fecha.grid(row=0, column=1, pady=6, sticky='w')
                        from datetime import date as _date
                        ent_fecha.insert(0, _date.today().isoformat())

                        tk.Label(f, text="Nombre tratamiento").grid(row=1, column=0, sticky='w')
                        nombre = tk.Entry(f, width=40); nombre.grid(row=1, column=1, columnspan=3, pady=6, sticky='w')

                        tk.Label(f, text="Medicamentos (opcional)").grid(row=2, column=0, sticky='w')
                        meds = tk.Entry(f, width=40); meds.grid(row=2, column=1, pady=6, sticky='w')

                        def guardar_tra():
                            fecha_reg = ent_fecha.get().strip() or hoy()
                            med_str = nombre.get().strip() or meds.get().strip()
                            dosis_str = ""
                            agregar_registro(ARCH_TRATAMIENTOS, [detalle[3], med_str, dosis_str, fecha_reg])
                            messagebox.showinfo("Éxito", "Tratamiento registrado.")
                            at.destroy()

                        tk.Button(f, text="Agregar Tratamiento", bg="#2A6F9E", fg='white', command=guardar_tra).grid(row=3, column=2, sticky='e', pady=8)

                    def add_alergia_gui():
                        aa = tk.Toplevel(det_win)
                        aa.title("Nueva alergia")
                        aa.geometry("520x180")
                        f = tk.Frame(aa, padx=12, pady=12)
                        f.pack(fill='both', expand=True)

                        tk.Label(f, text="Fecha").grid(row=0, column=0, sticky='w')
                        ent_fecha = tk.Entry(f, width=20); ent_fecha.grid(row=0, column=1, pady=6, sticky='w')
                        from datetime import date as _date
                        ent_fecha.insert(0, _date.today().isoformat())

                        tk.Label(f, text="Nombre alergia").grid(row=1, column=0, sticky='w')
                        alerg = tk.Entry(f, width=40); alerg.grid(row=1, column=1, pady=6)

                        tk.Label(f, text="Síntomas (separados por comas)").grid(row=2, column=0, sticky='w')
                        sint = tk.Entry(f, width=40); sint.grid(row=2, column=1, pady=6)

                        def guardar_al():
                            fecha_reg = ent_fecha.get().strip() or hoy()
                            agregar_registro(ARCH_ALERGIAS, [detalle[3], alerg.get().strip(), sint.get().strip().lower(), fecha_reg])
                            messagebox.showinfo("Éxito", "Alergia registrada.")
                            aa.destroy()

                        tk.Button(f, text="Agregar alergia", bg="#2A6F9E", fg='white', command=guardar_al).grid(row=3, column=1, sticky='e', pady=8)
                    tk.Button(btns, text="Editar Paciente", bg="#2A6F9E", fg='white', command=open_edit).pack(side='right', padx=6)
                    tk.Button(btns, text="Agregar Enfermedad", bg="#2A6F9E", fg='white', command=add_enfermedad_gui).pack(side='left', padx=6)
                    tk.Button(btns, text="Agregar Tratamiento", bg="#2A6F9E", fg='white', command=add_tratamiento_gui).pack(side='left', padx=6)
                    tk.Button(btns, text="Agregar Alergia", bg="#2A6F9E", fg='white', command=add_alergia_gui).pack(side='left', padx=6)
                    

                def buscar():
                    # Limpiar tree
                    for i in tree.get_children():
                        tree.delete(i)

                    clave_doc = ent_doc.get().strip()
                    clave_nom = ent_nom.get().strip()
                    clave_ape = ent_ape.get().strip()

                    resultados = []
                    for p in leer_registros(ARCH_PACIENTES):
                        if clave_doc and _norm(p[3]) == _norm(clave_doc):
                            resultados.append(p)
                            continue
                        nombre_norm = _norm(p[0])
                        if clave_nom and clave_nom.strip() != "" and _norm(clave_nom) in nombre_norm:
                            resultados.append(p)
                            continue
                        if clave_ape and clave_ape.strip() != "" and _norm(clave_ape) in nombre_norm:
                            resultados.append(p)
                            continue

                    if not resultados:
                        messagebox.showinfo("Resultado", "No se encontraron pacientes.")
                        return

                    for r in resultados:
                        tree.insert('', 'end', values=(r[3], r[0], r[2], r[6]))

                btn_buscar = tk.Button(frm, text="Botón Consultar Paciente", bg="#2A6F9E", fg="white", width=25, height=2, command=buscar)
                btn_buscar.grid(row=3, column=1, pady=8, sticky="e")

                tree.bind('<Double-1>', mostrar_detalle_seleccion)

            def on_listar():
                win = tk.Toplevel(root)
                win.title("Lista de pacientes")
                win.geometry("800x420")

                frm = tk.Frame(win, padx=12, pady=12)
                frm.pack(fill="both", expand=True)

                lbl = tk.Label(frm, text="Lista de pacientes", font=("Segoe UI", 14))
                lbl.pack(anchor="nw")

                tree = ttk.Treeview(frm, columns=("doc","nombre","genero","edad","celular","fecha"), show="headings", height=12)
                tree.heading("doc", text="Documento")
                tree.heading("nombre", text="Nombres")
                tree.heading("genero", text="Género")
                tree.heading("edad", text="Edad")
                tree.heading("celular", text="Celular")
                tree.heading("fecha", text="Fecha Registro")
                tree.column("doc", width=90, anchor="center")
                tree.column("nombre", width=220)
                tree.column("genero", width=110, anchor="center")
                tree.column("edad", width=60, anchor="center")
                tree.column("celular", width=110, anchor="center")
                tree.column("fecha", width=140)
                tree.pack(fill="both", expand=True, pady=(10,8))

                pacientes = leer_registros(ARCH_PACIENTES)
                for p in pacientes:
                    tree.insert('', 'end', values=(p[3], p[0], p[2], p[6], p[4], p[7]))

                btn_volver = tk.Button(frm, text="Volver al menú", bg="#2A6F9E", fg="white", width=18, height=2, command=win.destroy)
                btn_volver.pack(anchor="e", pady=6)

            # Cabecera de bienvenida
            lbl_welcome = tk.Label(root, text="Bienvenido al sistema de\nalmacenamiento de pacientes!", font=("Segoe UI", 18), justify="left")
            lbl_welcome.pack(anchor="nw", padx=20, pady=20)

            # Marco principal
            main_frame = tk.Frame(root)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Panel izquierdo: logo
            left = tk.Frame(main_frame, width=220)
            left.pack(side="left", fill="y")
            canvas = tk.Canvas(left, width=200, height=200)
            canvas.pack(pady=5)
            try:
                if PIL_AVAILABLE:
                    img = Image.open("logo.png").resize((160, 160), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                else:
                    photo = tk.PhotoImage(file="logo.png")
                canvas.create_image(100, 100, image=photo)
                # Guardar referencia para evitar que sea recolectada
                canvas.image = photo
            except Exception:
                canvas.create_text(100, 100, text="LOGO", font=("Arial", 16))

            # Panel derecho: botones
            right = tk.Frame(main_frame)
            right.pack(side="right", fill="y", expand=True, padx=40)
            btn_ag = tk.Button(right, text="Botón Agregar Paciente", width=25, height=2, bg="#2A6F9E", fg="white", command=on_agregar)
            btn_ag.pack(pady=10)
            btn_cons = tk.Button(right, text="Botón Consultar Paciente", width=25, height=2, bg="#2A6F9E", fg="white", command=on_consultar)
            btn_cons.pack(pady=10)
            btn_list = tk.Button(right, text="Botón Listar Pacientes", width=25, height=2, bg="#2A6F9E", fg="white", command=on_listar)
            btn_list.pack(pady=10)

            root.mainloop()
        except Exception:
            # Si ocurre cualquier error con la GUI, volver al menú de consola
            menu_principal()
