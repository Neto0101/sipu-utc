from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
import textwrap


import io
import textwrap
import sqlite3
import pandas as pd
import os
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = "utc_secret_key"

modelo = joblib.load("modelo/modelo_riesgo.pkl")



DB_NAME = "sipu.db"

# --------------------------
# CONEXIÓN A BASE DE DATOS
# --------------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def obtener_factores_por_filtros(grado=None, carrera=None, grupo=None, plantel=None, matricula=None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT 
            pp.elemento AS etiqueta,
            AVG(o.peso) as impacto
        FROM respuestas_personales r
        JOIN opciones_personales o
            ON r.pregunta_id = o.pregunta_id 
            AND r.respuesta = o.etiqueta
        JOIN preguntas_personales pp ON r.pregunta_id = pp.id
        JOIN usuarios u ON r.matricula = u.matricula
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE pp.elemento IS NOT NULL AND pp.elemento != ''
    """
    params = []

    if matricula:
        query += " AND r.matricula=?"
        params.append(matricula)

    if grado and grado != "Todos":
        query += " AND a.grado=?"
        params.append(grado)

    if carrera and carrera != "Todos":
        query += " AND u.carrera=?"
        params.append(carrera)

    if grupo and grupo != "Todos":
        query += " AND a.grupo=?"
        params.append(grupo)

    if plantel and plantel != "Todos":
        query += " AND u.plantel=?"
        params.append(plantel)

    query += " GROUP BY pp.elemento ORDER BY impacto DESC"

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    labels = [d["etiqueta"] for d in datos]
    valores = [round(d["impacto"] * 100, 2) for d in datos]

    return labels, valores


def obtener_factores_habilidades_por_filtros(grado=None,carrera=None,grupo=None,plantel=None,matricula=None):
    conn=get_db()
    conn.row_factory=sqlite3.Row
    cursor=conn.cursor()

    query="""
        SELECT 
            p.elemento AS etiqueta,
            SUM(CASE WHEN r.respuesta!=p.respuesta_correcta THEN 1 ELSE 0 END)*1.0 /
            COUNT(r.id) AS impacto
        FROM respuestas r
        JOIN preguntas p ON r.pregunta_id=p.id
        JOIN usuarios u ON r.matricula=u.matricula
        JOIN alumnos_info a ON u.matricula=a.matricula
        WHERE p.elemento IS NOT NULL AND p.elemento!=''
    """
    params=[]

    if matricula:
        query+=" AND u.matricula=?"
        params.append(matricula)
    if grado and grado!="Todos":
        query+=" AND a.grado=?"
        params.append(grado)
    if carrera and carrera!="Todos":
        query+=" AND u.carrera=?"
        params.append(carrera)
    if grupo and grupo!="Todos":
        query+=" AND a.grupo=?"
        params.append(grupo)
    if plantel and plantel!="Todos":
        query+=" AND u.plantel=?"
        params.append(plantel)

    query+=" GROUP BY p.elemento ORDER BY impacto DESC"

    cursor.execute(query,params)
    datos=cursor.fetchall()
    conn.close()

    labels=[d["etiqueta"] for d in datos]
    valores=[round(d["impacto"]*100,2) for d in datos]

    return labels,valores

def calcular_promedio_riesgo_personal(grado=None,carrera=None,grupo=None,plantel=None,matricula=None):
    conn=get_db()
    conn.row_factory=sqlite3.Row
    cursor=conn.cursor()

    query="""
        SELECT AVG(riesgo) as promedio
        FROM (
            SELECT
                r.matricula,
                AVG(o.peso) as riesgo
            FROM respuestas_personales r
            JOIN opciones_personales o
                ON r.pregunta_id=o.pregunta_id
                AND r.respuesta=o.etiqueta
            JOIN usuarios u ON r.matricula=u.matricula
            JOIN alumnos_info a ON u.matricula=a.matricula
            WHERE 1=1
    """
    params=[]

    if matricula:
        query+=" AND r.matricula=?"
        params.append(matricula)
    if grado and grado!="Todos":
        query+=" AND a.grado=?"
        params.append(grado)
    if carrera and carrera!="Todos":
        query+=" AND u.carrera=?"
        params.append(carrera)
    if grupo and grupo!="Todos":
        query+=" AND a.grupo=?"
        params.append(grupo)
    if plantel and plantel!="Todos":
        query+=" AND u.plantel=?"
        params.append(plantel)

    query+=" GROUP BY r.matricula)"

    cursor.execute(query,params)
    row=cursor.fetchone()
    conn.close()

    if row and row["promedio"] is not None:
        return round(row["promedio"]*100,2)
    else:
        return 0
def calcular_promedio_riesgo_habilidades(grado=None,carrera=None,grupo=None,plantel=None,matricula=None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT AVG(riesgo) as promedio
        FROM (
            SELECT
                r.matricula,
                SUM(CASE WHEN r.respuesta != p.respuesta_correcta THEN 1 ELSE 0 END) * 1.0 
                / COUNT(r.id) AS riesgo
            FROM respuestas r
            JOIN preguntas p ON r.pregunta_id = p.id
            JOIN usuarios u ON r.matricula = u.matricula
            JOIN alumnos_info a ON u.matricula = a.matricula
            WHERE 1=1
    """
    params = []

    if matricula:
        query += " AND r.matricula=?"
        params.append(matricula)
    if grado and grado != "Todos":
        query += " AND a.grado=?"
        params.append(grado)
    if carrera and carrera != "Todos":
        query += " AND u.carrera=?"
        params.append(carrera)
    if grupo and grupo != "Todos":
        query += " AND a.grupo=?"
        params.append(grupo)
    if plantel and plantel != "Todos":
        query += " AND u.plantel=?"
        params.append(plantel)

    query += " GROUP BY r.matricula)"

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    if row and row["promedio"] is not None:
        return round(row["promedio"] * 100, 2)
    else:
        return 0
def obtener_datos_alumno(matricula):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.nombre,
            u.carrera,
            u.plantel,
            a.grado,
            a.grupo
        FROM usuarios u
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE u.matricula = ?
    """, (matricula,))

    alumno = cursor.fetchone()
    conn.close()
    return alumno







def calcular_riesgo_personal_por_matricula(matricula):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()


    cursor.execute("""
        SELECT o.peso
        FROM respuestas_personales r
        JOIN opciones_personales o
        ON r.pregunta_id = o.pregunta_id
        AND r.respuesta = o.etiqueta
        WHERE r.matricula = ?
    """, (matricula,))

    pesos = [row["peso"] for row in cursor.fetchall()]
    conn.close()

    if not pesos:
        return 0

    return sum(pesos) / len(pesos)

def obtener_alertas_desercion(grado, carrera, grupo, plantel):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT 
            u.matricula,
            u.nombre,
            u.carrera,
            u.plantel,
            a.grado,
            a.grupo
        FROM usuarios u
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE u.rol = 'alumno'
    """
    params = []

    if grado != "Todos":
        query += " AND a.grado=?"
        params.append(grado)
    if carrera != "Todos":
        query += " AND u.carrera=?"
        params.append(carrera)
    if grupo != "Todos":
        query += " AND a.grupo=?"
        params.append(grupo)
    if plantel != "Todos":
        query += " AND u.plantel=?"
        params.append(plantel)

    cursor.execute(query, params)
    alumnos = cursor.fetchall()

    alertas = []

    for a in alumnos:
        riesgo = calcular_riesgo_personal_por_matricula(a["matricula"]) * 100
        riesgo = round(riesgo, 2)

        if riesgo >= 70:  # 🔴 SOLO ALTO RIESGO
            alertas.append({
                "matricula": a["matricula"],
                "nombre": a["nombre"],
                "carrera": a["carrera"],
                "plantel": a["plantel"],
                "grado": a["grado"],
                "grupo": a["grupo"],
                "riesgo": riesgo
            })

    conn.close()
    return alertas

def calcular_riesgo_habilidades_por_matricula(matricula):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.respuesta, p.respuesta_correcta
        FROM respuestas r
        JOIN preguntas p ON r.pregunta_id = p.id
        WHERE r.matricula = ?
    """, (matricula,))

    datos = cursor.fetchall()
    conn.close()

    if not datos:
        return 0

    total = len(datos)
    correctas = sum(1 for d in datos if d["respuesta"] == d["respuesta_correcta"])

    return 1 - (correctas / total)

def predecir_desercion(matricula):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.carrera,
            u.plantel,
            a.grado,
            a.grupo,
            a.turno
        FROM usuarios u
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE u.matricula = ?
    """, (matricula,))
    
    data = cursor.fetchone()
    conn.close()

    if not data:
        return None

    # ⚠️ Debe coincidir con lo que usaste al entrenar
    X = np.array([[
        int(data["grado"]),
        int(data["turno"]),
        int(data["grupo"])
    ]])

    X = scaler.transform(X)
    pred = modelo.predict(X)[0]
    prob = modelo.predict_proba(X)[0][1]

    return {
        "prediccion": int(pred),
        "probabilidad": round(prob * 100, 2)
    }
def generar_interpretacion(nombre, rp, rh):
    if rp >= 70 and rh >= 70:
        return f"{nombre} presenta un ALTO riesgo general de deserción debido tanto a problemas personales como a deficiencias en habilidades académicas."
    elif rp >= 70:
        return f"{nombre} presenta ALTO riesgo de deserción principalmente por factores personales como estrés, desmotivación o entorno familiar."
    elif rh >= 70:
        return f"{nombre} presenta ALTO riesgo de deserción principalmente por dificultades en habilidades académicas."
    elif rp >= 40 or rh >= 40:
        return f"{nombre} presenta RIESGO MODERADO de deserción, se recomienda seguimiento académico."
    else:
        return f"{nombre} presenta RIESGO BAJO de deserción."


# --------------------------
# INICIALIZAR BASE DE DATOS

# --------------------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    


    # -------------------------------------
    # TABLA USUARIOS (CON CAMPOS NUEVOS)
    # -------------------------------------
    cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT UNIQUE,
    nombre TEXT,
    a_paterno TEXT,
    a_materno TEXT,
    rol TEXT,
    carrera TEXT,
    plantel TEXT,
    nip TEXT
)
""")

    # -------------------------------------
    # TABLA INFO ALUMNOS
    # -------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula TEXT UNIQUE,
        grado TEXT,
        grupo TEXT,
        turno TEXT,
        FOREIGN KEY (matricula) REFERENCES usuarios(matricula)
    )
    """)

    # -------------------------------------
    # TABLAS PREGUNTAS
    # -------------------------------------
    cursor.execute("""
CREATE TABLE IF NOT EXISTS preguntas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto TEXT NOT NULL,
    carrera TEXT,
    tipo_pregunta TEXT CHECK(tipo_pregunta IN ('texto','opcion_multiple')) NOT NULL DEFAULT 'texto',
    opciones TEXT,
    respuesta_correcta TEXT
)
""")


    cursor.execute("""
CREATE TABLE IF NOT EXISTS preguntas_personales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto TEXT NOT NULL,
    tipo_pregunta TEXT NOT NULL,
    opciones TEXT
)
""")
    # -------------------------------------
# TABLA OPCIONES CON PESO (PERSONALES)
# -------------------------------------
    cursor.execute("""
CREATE TABLE IF NOT EXISTS opciones_personales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pregunta_id INTEGER,
    valor INTEGER,      -- 1,2,3,4,5
    etiqueta TEXT,      -- "Totalmente en desacuerdo", etc.
    peso REAL,          -- el peso real para el riesgo
    FOREIGN KEY (pregunta_id) REFERENCES preguntas_personales(id)
)
""")

   

    # -------------------------------------
    # TABLAS RESPUESTAS
    # -------------------------------------
    cursor.execute("""
CREATE TABLE IF NOT EXISTS respuestas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT,
    pregunta_id INTEGER,
    respuesta TEXT,
    FOREIGN KEY (pregunta_id) REFERENCES preguntas(id)
)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS respuestas_personales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT,
    pregunta_id INTEGER,
    respuesta TEXT
)
""")

    

    # -------------------------------------
    # TABLA PLANTELES
    # -------------------------------------
    cursor.execute("""
CREATE TABLE IF NOT EXISTS planteles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_plantel TEXT UNIQUE
)
""")

    # -------------------------------------
    # TABLA CARRERAS
    # -------------------------------------
    cursor.execute("""
CREATE TABLE IF NOT EXISTS carreras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_carrera TEXT UNIQUE
)
""")

    # -------------------------------------
    # INSERTAR LISTA DE CARRERAS
    # -------------------------------------
    lista_carreras = [
        "Administración y Liderazgo Empresarial",
        "Contaduría",
        "Derecho",
        "Diseño Gráfico",
        "Sistemas Computacionales",
        "Odontología by UVT (Toluca)",
        "Psicología",
        "Comunicación Digital",
        "Gastronomía y Gestión Restaurantera",
        "Arquitectura",
        "Turismo",
        "Administración de Negocios de Comunicación y Entretenimiento",
        "Pedagogía",
        "Nutrición",
        "Negocios Digitales",
        "Mercadotecnia",
        "Fisioterapia",
        "Administración de Recursos Humanos"
    ]

    for carrera in lista_carreras:
        cursor.execute("INSERT OR IGNORE INTO carreras (nombre_carrera) VALUES (?)", (carrera,))

    # -------------------------------------
    # INSERTAR PLANTELES
    # -------------------------------------
    lista_planteles = [
        "Aragón", "Iztapalapa", "Observatorio", "Tlalpan", "Toreo", "Zona Rosa",
        "Atizapán", "Chalco", "Coacalco", "Cuautitlán", "Ecatepec", "Huehuetoca",
        "Ixtapaluca", "Los Reyes", "Neza", "Puebla", "Tlalnepantla", "Toluca"
    ]

    for plantel in lista_planteles:
        cursor.execute("INSERT OR IGNORE INTO planteles (nombre_plantel) VALUES (?)", (plantel,))

    # -------------------------------------
    # ADMINISTRADORES
    # -------------------------------------
    cursor.execute("SELECT * FROM usuarios WHERE matricula='1998'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (matricula, nombre, rol, carrera, nip) VALUES (?, ?, ?, ?, ?)",
            ("1998", "Administrador UTC", "admin", None, None)
        )

    cursor.execute("SELECT * FROM usuarios WHERE matricula='1020'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (matricula, nombre, rol, carrera, nip) VALUES (?, ?, ?, ?, ?)",
            ("1020", "Administrador Cuestionarios", "admin", None, None)
        )

    # -------------------------------------
    # JEFES DESDE EXCEL
    # -------------------------------------
    if os.path.exists("registros_empleados_TES.xlsx"):
        try:
            df_jefes = pd.read_excel("registros_empleados_TES.xlsx")
            df_jefes.columns = [col.strip().upper() for col in df_jefes.columns]

            for _, row in df_jefes.iterrows():
                matricula = str(row.get("ID", "")).strip()
                nombre = str(row.get("NOMBRE", "")).strip()
                a_paterno = str(row.get("A_PATERNO", "")).strip()
                a_materno = str(row.get("A_MATERNO", "")).strip()
                carrera = str(row.get("CARRERA", "")).strip()

                if not matricula:
                    continue

                cursor.execute("SELECT * FROM usuarios WHERE matricula=?", (matricula,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO usuarios 
                        (matricula, nombre, a_paterno, a_materno, rol, carrera, plantel, nip)
                        VALUES (?, ?, ?, ?, 'jefe', ?, NULL, NULL)
                    """, (matricula, nombre, a_paterno, a_materno, carrera))

        except Exception as e:
            print("Error cargando registros_empleados_TES.xlsx:", e)

    # -------------------------------------
    # ALUMNOS DESDE EXCEL
    # -------------------------------------
    if os.path.exists("MATRICULA.xlsx"):
        try:
            df_alumnos = pd.read_excel("MATRICULA.xlsx")
            df_alumnos.columns = [col.strip().upper() for col in df_alumnos.columns]

            for _, row in df_alumnos.iterrows():
                matricula = str(row.get("MATRICULA","")).strip()
                nombre = str(row.get("NOMBRE","")).strip()
                a_paterno = str(row.get("A_PATERNO","")).strip()
                a_materno = str(row.get("A_MATERNO","")).strip()
                carrera = str(row.get("CARRERA","")).strip()
                plantel = str(row.get("PLANTEL","")).strip()
                grado = str(row.get("GRADO","") or "").strip()
                grupo = str(row.get("GRUPO","") or "").strip()
                turno = str(row.get("TURNO","") or "").strip()

                if not matricula:
                    continue

                cursor.execute("SELECT * FROM usuarios WHERE matricula=?", (matricula,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO usuarios
                        (matricula, nombre, a_paterno, a_materno, rol, carrera, plantel, nip)
                        VALUES (?, ?, ?, ?, 'alumno', ?, ?, NULL)
                    """, (matricula, nombre, a_paterno, a_materno, carrera, plantel))

                cursor.execute("SELECT * FROM alumnos_info WHERE matricula=?", (matricula,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO alumnos_info (matricula, grado, grupo, turno)
                        VALUES (?, ?, ?, ?)
                    """, (matricula, grado, grupo, turno))
                else:
                    cursor.execute("""
                        UPDATE alumnos_info 
                        SET grado=?, grupo=?, turno=? 
                        WHERE matricula=?
                    """, (grado, grupo, turno, matricula))

        except Exception as e:
            print("Error cargando MATRICULA.xlsx:", e)

            
    conn.commit()
    conn.close()





# --------------------------
# RUTAS
# --------------------------
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    matricula = request.form["matricula"]
    nip = request.form["nip"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE matricula=?", (matricula,))
    user = cursor.fetchone()
    conn.close()

    if user:
        if user["nip"] is None:
            # si no tiene nip, pedir que lo establezca
            session["matricula_temp"] = matricula
            return redirect(url_for("set_password"))
        elif user["nip"] == nip:
            # login OK
            session["usuario"] = user["nombre"]
            session["rol"] = user["rol"]
            session["matricula"] = user["matricula"]

            if user["rol"] in ["jefe", "alumno"]:
                session["carrera"] = user["carrera"]

            # --- Aquí agregamos el comportamiento especial ---
            if user["rol"] == "admin":
                if user["matricula"] == "1020":
                    # Admin cuestionarios → gestionar cuestionarios
                    return redirect(url_for("gestionar_cuestionarios"))
                elif user["matricula"] == "1998":
                    # Admin general → menú admin
                    return redirect(url_for("menu_admin"))
            elif user["rol"] == "jefe":
             return redirect(url_for("gestionar_preguntas"))

            elif user["rol"] == "alumno":
             return redirect(url_for("responder_personales", tipo="perfil"))


        else:
            return render_template("login.html", error="Usuario o NIP incorrecto")
    else:
        return render_template("login.html", error="Usuario no encontrado")

# --------------------------
# ESTABLECER NIP 
# --------------------------
@app.route("/set_password", methods=["GET", "POST"])
def set_password():
    matricula = session.get("matricula_temp")
    if not matricula:
        return redirect(url_for("index"))

    if request.method == "POST":
        nip = request.form["nip"]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET nip=? WHERE matricula=?", (nip, matricula))
        conn.commit()

        cursor.execute("SELECT * FROM usuarios WHERE matricula=?", (matricula,))
        user = cursor.fetchone()
        conn.close()

        session.pop("matricula_temp", None)

        session["usuario"] = user["nombre"]
        session["rol"] = user["rol"]
        session["matricula"] = user["matricula"]

        if user["rol"] in ["jefe", "alumno"]:
            session["carrera"] = user["carrera"]

        # ✅ REDIRECCIONES CORRECTAS POR USUARIO
        if user["rol"] == "admin":
            if user["matricula"] == "1020":
                return redirect(url_for("gestionar_cuestionarios"))  # Admin de cuestionarios
            elif user["matricula"] == "1998":
                return redirect(url_for("menu_admin"))  # Admin general

        elif user["rol"] == "jefe":
            return redirect(url_for("gestionar_preguntas"))

        elif user["rol"] == "alumno":
            return redirect(url_for("encuesta", tipo="perfil"))

    return render_template("set_admin_password.html")

# --------------------------
# MENÚS
# --------------------------
@app.route("/menu_admin")
def menu_admin():
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.matricula,
            u.nombre,
            u.a_paterno,
            u.a_materno,
            u.carrera,
            u.plantel,
            a.grado,
            a.turno,
            a.grupo
        FROM usuarios u
        LEFT JOIN alumnos_info a
            ON u.matricula = a.matricula
        WHERE u.rol = 'alumno'
    """)
    alumnos = cursor.fetchall()

    cursor.execute("""
        SELECT 
            matricula AS id,
            nombre,
            a_paterno,
            a_materno,
            carrera,
            plantel
        FROM usuarios
        WHERE rol = 'maestro' OR rol = 'jefe'
    """)
    maestros = cursor.fetchall()

    cursor.execute("SELECT id, nombre_plantel FROM planteles")
    planteles = cursor.fetchall()

    cursor.execute("SELECT id, nombre_carrera FROM carreras")
    carreras = cursor.fetchall()

    conn.close()

    return render_template(
        "menu_admin.html",
        alumnos=alumnos,
        maestros=maestros,
        planteles=planteles,
        carreras=carreras
    )

# --------------------------
# VER RESPUESTAS (Jefe) - lista, filtros y ver respuestas por alumno
# --------------------------
@app.route("/ver_respuestas_jefe", methods=["GET", "POST"])
def ver_respuestas_jefe():
    if session.get("rol") != "jefe":
        return redirect(url_for("index"))

    # ✅ REDIRECCIÓN DIRECTA AL DASHBOARD DEL JEFE
    return redirect(url_for("dashboard_jefe"))



@app.route("/ver_respuestas_alumno/<matricula>")
def ver_respuestas_alumno(matricula):
    # Solo jefes
    if session.get("rol") != "jefe":
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    # Info del alumno
    cursor.execute("""
        SELECT u.nombre, a.grado, a.grupo, a.turno 
        FROM usuarios u 
        JOIN alumnos_info a ON u.matricula = a.matricula 
        WHERE u.matricula=?
    """, (matricula,))
    alumno = cursor.fetchone()

    # Respuestas del alumno (perfil)
    cursor.execute("""
        SELECT p.texto AS pregunta, r.respuesta 
        FROM respuestas r 
        JOIN preguntas p ON r.pregunta_id = p.id 
        WHERE r.matricula=?
    """, (matricula,))
    respuestas = cursor.fetchall()

    cursor.execute("""
        SELECT p.texto AS pregunta, r.respuesta 
        FROM respuestas_personales r 
        JOIN preguntas_personales p ON r.pregunta_id = p.id 
        WHERE r.matricula=?
    """, (matricula,))
    resp_personales = cursor.fetchall()

    conn.close()

    return render_template(
        "ver_respuestas_alumno.html",
        alumno=alumno,
        respuestas=respuestas,
        resp_personales=resp_personales
    )

# --------------------------
# ENCUESTA ALUMNOS (perfil - las preguntas por carrera se toman de tabla 'preguntas' tipo perfil_licenciatura)
# --------------------------
@app.route("/encuesta/<tipo>", methods=["GET", "POST"])
def encuesta(tipo):
    if session.get("rol") != "alumno":
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    # Traer todas las preguntas de la carrera del alumno
    cursor.execute("SELECT * FROM preguntas WHERE carrera=?", (session.get("carrera"),))
    preguntas = cursor.fetchall()

    # Verificar si el alumno ya contestó este cuestionario
    cursor.execute("""
        SELECT * FROM respuestas
        WHERE matricula=? AND pregunta_id IN (
            SELECT id FROM preguntas WHERE carrera=?
        )
    """, (session["matricula"], session.get("carrera")))
    filas = cursor.fetchall()
    ya_contesto = len(filas) > 0

    # Guardar respuestas solo si no ha contestado
    if request.method == "POST" and not ya_contesto:
        for pregunta in preguntas:
            respuesta = request.form.get(f"pregunta_{pregunta['id']}")
            if respuesta:
                cursor.execute(
                    "INSERT INTO respuestas (matricula, pregunta_id, respuesta) VALUES (?, ?, ?)",
                    (session["matricula"], pregunta["id"], respuesta)
                )
        conn.commit()
        conn.close()
        return render_template("gracias.html")

    # Crear diccionario de respuestas existentes para mostrar
    respuestas = {fila['pregunta_id']: fila['respuesta'] for fila in filas}

    conn.close()
    return render_template("encuesta.html", preguntas=preguntas, tipo=tipo,
                           ya_contesto=ya_contesto, respuestas=respuestas)


  
# --------------------------
# VER RESPUESTAS DEL ALUMNO (mis respuestas, alumno logeado)
# --------------------------
@app.route("/ver_respuestas")
def ver_respuestas():
    if session.get("rol") != "alumno":
        return redirect(url_for("index"))

    matricula = session.get("matricula")
    conn = get_db()
    cursor = conn.cursor()

    # ✅ Respuestas del cuestionario de carrera
    cursor.execute("""
        SELECT p.texto, r.respuesta
        FROM respuestas r
        JOIN preguntas p ON r.pregunta_id = p.id
        WHERE r.matricula = ?
    """, (matricula,))
    respuestas = cursor.fetchall()

    # ✅ Respuestas del cuestionario de datos personales
    cursor.execute("""
        SELECT p.texto, r.respuesta
        FROM respuestas_personales r
        JOIN preguntas_personales p ON r.pregunta_id = p.id
        WHERE r.matricula = ?
    """, (matricula,))
    resp_personales = cursor.fetchall()

    conn.close()

    return render_template(
        "ver_respuestas.html",
        respuestas=respuestas,
        resp_personales=resp_personales
    )


# --------------------------
# GESTIÓN DE PREGUNTAS PARA JEFES (perfil)
# --------------------------
@app.route("/preguntas_admin", methods=["GET", "POST"])
def gestionar_preguntas():
    if session.get("rol") != "jefe":
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        # ============================
        # ✅ AGREGAR PREGUNTA (CON ELEMENTO MANUAL)
        # ============================
        if "agregar" in request.form:
            texto = request.form["texto"]
            tipo_pregunta = request.form["tipo_pregunta"]
            elemento = request.form.get("elemento")  # ✅ SOLO SE AGREGA ESTO

            opciones = ""
            respuesta_correcta = None

            if tipo_pregunta == "opcion_multiple":
                lista_opciones = request.form.getlist("opciones[]")
                opciones = ",".join(lista_opciones)
                respuesta_correcta = request.form.get("respuesta_correcta")

            cursor.execute("""
                INSERT INTO preguntas
                (texto, carrera, tipo_pregunta, opciones, respuesta_correcta, elemento)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (texto, session.get("carrera"), tipo_pregunta, opciones, respuesta_correcta, elemento))

            conn.commit()

        # ============================
        # ✅ EDITAR PREGUNTA (CON ELEMENTO)
        # ============================
        elif "editar_id" in request.form:
            pid = request.form["editar_id"]
            texto = request.form["editar_texto"]
            tipo_pregunta = request.form.get("editar_tipo", "texto")
            opciones = request.form.get("editar_opciones", "")
            respuesta_correcta = request.form.get("editar_respuesta_correcta")
            elemento = request.form.get("editar_elemento")  # ✅ SOLO SE AGREGA ESTO

            # Si la pregunta pasa a ser de texto, quitamos opciones y respuesta correcta
            if tipo_pregunta == "texto":
                opciones = ""
                respuesta_correcta = None

            cursor.execute("""
                UPDATE preguntas
                SET texto=?, tipo_pregunta=?, opciones=?, respuesta_correcta=?, elemento=?
                WHERE id=? AND carrera=?
            """, (texto, tipo_pregunta, opciones, respuesta_correcta, elemento, pid, session.get("carrera")))

            conn.commit()

        # ============================
        # ✅ ELIMINAR PREGUNTA
        # ============================
        elif "eliminar_id" in request.form:
            pid = request.form["eliminar_id"]
            cursor.execute(
                "DELETE FROM preguntas WHERE id=? AND carrera=?",
                (pid, session.get("carrera"))
            )
            conn.commit()

    # ============================
    # ✅ OBTENER PREGUNTAS
    # ============================
    cursor.execute("SELECT * FROM preguntas WHERE carrera=?", (session.get("carrera"),))
    preguntas = cursor.fetchall()
    conn.close()

    return render_template("preguntas_admin.html", preguntas=preguntas)

@app.route("/dashboard_jefe")
def dashboard_jefe():
    if session.get("rol") != "jefe":
        return redirect(url_for("index"))

    grado     = request.args.get("grado", "Todos")
    carrera   = request.args.get("carrera", "Todos")
    grupo     = request.args.get("grupo", "Todos")
    plantel   = request.args.get("plantel", "Todos")
    matricula = request.args.get("matricula", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    # =============================
    #  OBTENER ALUMNOS FILTRADOS
    # =============================
    query = """
        SELECT
            u.matricula,
            u.nombre,
            u.a_paterno,
            u.a_materno,
            u.carrera,
            u.plantel,
            a.grado,
            a.grupo,
            a.turno
        FROM usuarios u
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE u.rol = 'alumno'
    """
    params = []

    if grado != "Todos":
        query += " AND a.grado = ?"
        params.append(grado)

    if carrera != "Todos":
        query += " AND u.carrera = ?"
        params.append(carrera)

    if grupo != "Todos":
        query += " AND a.grupo = ?"
        params.append(grupo)

    if plantel != "Todos":
        query += " AND u.plantel = ?"
        params.append(plantel)

    if matricula:
        query += " AND u.matricula = ?"
        params.append(matricula)

    cursor.execute(query, params)
    alumnos = cursor.fetchall()

    # 🔢 TOTAL DE ALUMNOS EN EL FILTRO
    total_filtrados = len(alumnos)

    # =============================
    #  PROMEDIOS DE RIESGOS
    # =============================
    riesgos_personales = []
    riesgos_habilidades = []
    alumnos_alerta = []  # lista de alumnos con posible deserción

    for a in alumnos:
        rp = calcular_riesgo_personal_por_matricula(a["matricula"])      # 0–1
        rh = calcular_riesgo_habilidades_por_matricula(a["matricula"])   # 0–1

        porc_rp = round(rp * 100, 2)
        porc_rh = round(rh * 100, 2)

        riesgos_personales.append(porc_rp)
        riesgos_habilidades.append(porc_rh)

        # UMBRAL DE ALERTA (puedes cambiar 70 por otro valor)
        if porc_rp >= 70 or porc_rh >= 70:
            alumnos_alerta.append({
                "matricula": a["matricula"],
                "nombre": a["nombre"],
                "a_paterno": a["a_paterno"],
                "a_materno": a["a_materno"],
                "carrera": a["carrera"],
                "plantel": a["plantel"],
                "grado": a["grado"],
                "grupo": a["grupo"],
                "turno": a["turno"],
                "riesgo_personal": porc_rp,
                "riesgo_habilidades": porc_rh
            })

    prom_personal = round(sum(riesgos_personales) / len(riesgos_personales), 2) if riesgos_personales else 0
    prom_habilidad = round(sum(riesgos_habilidades) / len(riesgos_habilidades), 2) if riesgos_habilidades else 0

    # =============================
    #  CUÁNTOS HAN CONTESTADO (PERSONALES)
    # =============================
    query_personal = """
        SELECT COUNT(DISTINCT r.matricula) AS n
        FROM respuestas_personales r
        JOIN usuarios u ON r.matricula = u.matricula
        JOIN alumnos_info a ON r.matricula = a.matricula
        WHERE 1=1
    """
    params_personal = []

    if grado != "Todos":
        query_personal += " AND a.grado = ?"
        params_personal.append(grado)
    if carrera != "Todos":
        query_personal += " AND u.carrera = ?"
        params_personal.append(carrera)
    if grupo != "Todos":
        query_personal += " AND a.grupo = ?"
        params_personal.append(grupo)
    if plantel != "Todos":
        query_personal += " AND u.plantel = ?"
        params_personal.append(plantel)
    if matricula:
        query_personal += " AND r.matricula = ?"
        params_personal.append(matricula)

    cursor.execute(query_personal, params_personal)
    row_p = cursor.fetchone()
    contestaron_personal = row_p["n"] if row_p and row_p["n"] is not None else 0

    # =============================
    #  CUÁNTOS HAN CONTESTADO (HABILIDADES)
    # =============================
    query_hab = """
        SELECT COUNT(DISTINCT r.matricula) AS n
        FROM respuestas r
        JOIN usuarios u ON r.matricula = u.matricula
        JOIN alumnos_info a ON r.matricula = a.matricula
        WHERE 1=1
    """
    params_hab = []

    if grado != "Todos":
        query_hab += " AND a.grado = ?"
        params_hab.append(grado)
    if carrera != "Todos":
        query_hab += " AND u.carrera = ?"
        params_hab.append(carrera)
    if grupo != "Todos":
        query_hab += " AND a.grupo = ?"
        params_hab.append(grupo)
    if plantel != "Todos":
        query_hab += " AND u.plantel = ?"
        params_hab.append(plantel)
    if matricula:
        query_hab += " AND r.matricula = ?"
        params_hab.append(matricula)

    cursor.execute(query_hab, params_hab)
    row_h = cursor.fetchone()
    contestaron_habilidades = row_h["n"] if row_h and row_h["n"] is not None else 0

    # =============================
    #  OPCIONES PARA FILTROS
    # =============================
    cursor.execute("SELECT DISTINCT grado FROM alumnos_info")
    grados = [g["grado"] for g in cursor.fetchall()]

    cursor.execute("SELECT nombre_carrera FROM carreras")
    carreras = [c["nombre_carrera"] for c in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT grupo FROM alumnos_info")
    grupos = [g["grupo"] for g in cursor.fetchall()]

    cursor.execute("SELECT nombre_plantel FROM planteles")
    planteles = [p["nombre_plantel"] for p in cursor.fetchall()]

    # =============================
    #  FACTORES PERSONALES (POR ELEMENTO)
    # =============================
    labels_factores, valores_factores = obtener_factores_por_filtros(
        grado, carrera, grupo, plantel, matricula
    )

    # =============================
    #  FACTORES DE HABILIDADES (POR ELEMENTO)
    # =============================
    labels_hab, valores_hab = obtener_factores_habilidades_por_filtros(
        grado, carrera, grupo, plantel, matricula
    )

    conn.close()

    return render_template(
        "dashboard_jefe.html",

        # GRÁFICAS PRINCIPALES
        riesgo_personal=prom_personal,
        riesgo_habilidades=prom_habilidad,

        # FACTORES PERSONALES
        factores_labels=labels_factores,
        factores_valores=valores_factores,

        # FACTORES HABILIDADES
        factores_hab_labels=labels_hab,
        factores_hab_valores=valores_hab,

        # LISTA DE ALERTAS PARA EL JEFE/MAESTRO
        alumnos_alerta=alumnos_alerta,

        # CONTADORES
        total_filtrados=total_filtrados,
        contestaron_personal=contestaron_personal,
        contestaron_habilidades=contestaron_habilidades,

        # FILTROS (por si quieres mantener selección en el template)
        grados=grados,
        carreras=carreras,
        grupos=grupos,
        planteles=planteles,
        filtro_grado=grado,
        filtro_carrera=carrera,
        filtro_grupo=grupo,
        filtro_plantel=plantel,
        filtro_matricula=matricula
    )



@app.route("/reporte_individual_alumno")
def reporte_individual_alumno():
    matricula = request.args.get("matricula")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.matricula, u.nombre, u.carrera, u.plantel, 
               a.grado, a.grupo, a.turno
        FROM usuarios u
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE u.matricula = ?
    """, (matricula,))

    alumno = cursor.fetchone()
    conn.close()

    if not alumno:
        return "Alumno no encontrado"

    rp = round(calcular_riesgo_personal_por_matricula(matricula) * 100, 2)
    rh = round(calcular_riesgo_habilidades_por_matricula(matricula) * 100, 2)

    mensaje = generar_interpretacion(alumno["nombre"], rp, rh)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 11)

    pdf.drawString(50, 750, "REPORTE INDIVIDUAL DE RIESGO")
    pdf.drawString(50, 720, f"Nombre: {alumno['nombre']}")
    pdf.drawString(50, 705, f"Matrícula: {alumno['matricula']}")
    pdf.drawString(50, 690, f"Carrera: {alumno['carrera']}")
    pdf.drawString(50, 675, f"Plantel: {alumno['plantel']}")
    pdf.drawString(50, 660, f"Grado y grupo: {alumno['grado']} - {alumno['grupo']}")

    pdf.drawString(50, 630, f"Riesgo personal: {rp}%")
    pdf.drawString(50, 615, f"Riesgo por habilidades: {rh}%")

    pdf.drawString(50, 580, "INTERPRETACIÓN:")
    text = pdf.beginText(50, 560)
    text.textLine(mensaje)
    pdf.drawText(text)

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"reporte_{alumno['matricula']}.pdf",
        mimetype="application/pdf"
    )


@app.route("/reporte_riesgo_personal")
def reporte_riesgo_personal():
    grado     = request.args.get("grado")
    carrera   = request.args.get("carrera")
    grupo     = request.args.get("grupo")
    plantel   = request.args.get("plantel")
    matricula = request.args.get("matricula")

    # ========= INFO DEL ALUMNO =========
    nombre = grado_al = grupo_al = carrera_al = plantel_al = ""

    if matricula:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT u.nombre, u.carrera, u.plantel, a.grado, a.grupo
            FROM usuarios u
            JOIN alumnos_info a ON u.matricula = a.matricula
            WHERE u.matricula = ?
        """, (matricula,))
        alumno = cur.fetchone()
        conn.close()

        if alumno:
            nombre      = alumno["nombre"]
            grado_al    = alumno["grado"]
            grupo_al    = alumno["grupo"]
            carrera_al  = alumno["carrera"]
            plantel_al  = alumno["plantel"]

    # ========= RIESGOS =========
    prom_personal = calcular_promedio_riesgo_personal(None, None, None, None, matricula)
    prom_hab      = calcular_promedio_riesgo_habilidades(None, None, None, None, matricula)

    # ========= FACTORES =========
    fac_p_labels, fac_p_valores = obtener_factores_por_filtros(None, None, None, None, matricula)
    fac_h_labels, fac_h_valores = obtener_factores_habilidades_por_filtros(None, None, None, None, matricula)

    # ========= CLASIFICACIÓN =========
    if prom_personal >= 70 or prom_hab >= 70:
        clasificacion = "RIESGO ALTO"
        badge_color = colors.HexColor("#e74c3c")
    elif prom_personal >= 40 or prom_hab >= 40:
        clasificacion = "RIESGO MODERADO"
        badge_color = colors.HexColor("#f39c12")
    else:
        clasificacion = "RIESGO BAJO"
        badge_color = colors.HexColor("#27ae60")

    texto_interpretacion = (
        f"El alumno {nombre}, con matrícula {matricula}, presenta un nivel de riesgo "
        f"clasificado como {clasificacion}. Se recomienda seguimiento académico, tutorías "
        "y apoyo psicopedagógico según los factores detectados."
    )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # =========================
    # ENCABEZADO AZUL (IGUAL AL GENERAL)
    # =========================
    pdf.setFillColor(colors.HexColor("#003B85"))
    pdf.rect(0, height - 80, width, 70, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 45, "SIPU UTC")

    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 60, "Reporte Individual de Riesgo")

    pdf.setStrokeColor(colors.HexColor("#002552"))
    pdf.line(50, height - 82, width - 50, height - 82)

    pdf.setFillColor(colors.black)
    pdf.setStrokeColor(colors.black)

    y = height - 120

    # =========================
    # DATOS DEL ALUMNO
    # =========================
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Datos del alumno:")
    y -= 18

    pdf.setFont("Helvetica", 11)
    pdf.drawString(60, y, f"Nombre: {nombre}"); y -= 14
    pdf.drawString(60, y, f"Matrícula: {matricula}"); y -= 14
    pdf.drawString(60, y, f"Grado: {grado_al}"); y -= 14
    pdf.drawString(60, y, f"Grupo: {grupo_al}"); y -= 14
    pdf.drawString(60, y, f"Carrera: {carrera_al}"); y -= 14
    pdf.drawString(60, y, f"Plantel: {plantel_al}"); y -= 20

    pdf.setStrokeColor(colors.HexColor("#DDDDDD"))
    pdf.line(50, y, width - 50, y)
    pdf.setStrokeColor(colors.black)
    y -= 20

    # =========================
    # RESUMEN DE RIESGO
    # =========================
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Resumen de riesgos:")
    y -= 18

    pdf.setFont("Helvetica", 11)
    pdf.drawString(60, y, f"Riesgo personal: {prom_personal:.1f}%"); y -= 14
    pdf.drawString(60, y, f"Riesgo por habilidades: {prom_hab:.1f}%"); y -= 18

    # Badge de clasificación
    badge_width = 220
    badge_height = 20
    badge_x = 60
    badge_y = y - badge_height + 8

    pdf.setFillColor(badge_color)
    pdf.roundRect(badge_x, badge_y, badge_width, badge_height, 4, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(
        badge_x + badge_width / 2,
        badge_y + 6,
        f"Clasificación: {clasificacion}"
    )

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 11)
    y = badge_y - 25

    # =========================
    # INTERPRETACIÓN (CAJA GRIS)
    # =========================
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Interpretación:")
    y -= 18

    lineas = textwrap.wrap(texto_interpretacion, 95)
    alto_caja = 16 + 14 * len(lineas)
    caja_y = y - alto_caja + 8

    pdf.setFillColor(colors.HexColor("#f5f5f5"))
    pdf.rect(45, caja_y, width - 90, alto_caja, fill=1, stroke=0)

    pdf.setFillColor(colors.black)
    texto_y = y - 4
    for linea in lineas:
        pdf.drawString(55, texto_y, linea)
        texto_y -= 14

    y = texto_y - 25

    # =========================
    # FACTORES PERSONALES
    # =========================
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Factores personales asociados:")
    y -= 16

    pdf.setFont("Helvetica", 11)
    if fac_p_labels:
        for etiqueta, valor in zip(fac_p_labels, fac_p_valores):
            pdf.drawString(60, y, f"• {etiqueta}: {valor:.1f}%")
            y -= 14
    else:
        pdf.drawString(60, y, "• No hay datos suficientes")
        y -= 14

    # =========================
    # FACTORES DE HABILIDADES
    # =========================
    y -= 20
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Factores de habilidades asociados:")
    y -= 16

    pdf.setFont("Helvetica", 11)
    if fac_h_labels:
        for etiqueta, valor in zip(fac_h_labels, fac_h_valores):
            pdf.drawString(60, y, f"• {etiqueta}: {valor:.1f}%")
            y -= 14
    else:
        pdf.drawString(60, y, "• No hay datos suficientes")
        y -= 14

    # =========================
    # PIE DE PÁGINA
    # =========================
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.drawCentredString(width / 2, 40, "Reporte generado automáticamente por SIPU UTC")

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_riesgo_personal.pdf",
        mimetype="application/pdf"
    )


@app.route("/reporte_personalizado")
def reporte_personalizado():

    grado = request.args.get("grado")
    carrera = request.args.get("carrera")
    grupo = request.args.get("grupo")
    plantel = request.args.get("plantel")
    matricula = request.args.get("matricula")

    conn = get_db()
    cursor = conn.cursor()

    # ✅ DATOS DEL ALUMNO
    cursor.execute("""
        SELECT u.nombre, u.carrera, u.plantel, a.grado, a.grupo
        FROM usuarios u
        JOIN alumnos_info a ON u.matricula = a.matricula
        WHERE u.matricula = ?
    """, (matricula,))
    alumno = cursor.fetchone()

    nombre = alumno["nombre"]
    carrera_real = alumno["carrera"]
    plantel_real = alumno["plantel"]
    grado_real = alumno["grado"]
    grupo_real = alumno["grupo"]

    # ✅ RIESGOS
    riesgo_personal = round(calcular_riesgo_personal_por_matricula(matricula) * 100, 2)
    riesgo_hab = round(calcular_riesgo_habilidades_por_matricula(matricula) * 100, 2)

    # ✅ CLASIFICACIÓN
    if riesgo_personal >= 70:
        clasificacion = "RIESGO ALTO"
    elif riesgo_personal >= 40:
        clasificacion = "RIESGO MODERADO"
    else:
        clasificacion = "RIESGO BAJO"

    # ✅ FACTORES QUE MÁS AFECTAN
    labels, valores = obtener_factores_por_filtros(
        grado, carrera, grupo, plantel, matricula
    )

    factores_texto = ""
    for i in range(min(5, len(labels))):
        factores_texto += f"- {labels[i]}: {valores[i]}%\n"

    # ✅ INTERPRETACIÓN AUTOMÁTICA
    if riesgo_personal > riesgo_hab:
        causa = "factores personales"
    else:
        causa = "habilidades académicas"

    mensaje = f"""
El alumno {nombre}, con matrícula {matricula}, presenta un nivel de riesgo de deserción del {riesgo_personal}%.
Este riesgo se encuentra principalmente asociado a {causa}.
Se recomienda acompañamiento académico y orientación personal.
"""

    # ✅ CREAR PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 11)

    y = 750
    pdf.drawString(50, y, "REPORTE DE RIESGO PERSONAL"); y -= 30
    pdf.drawString(50, y, f"Alumno: {nombre}"); y -= 20
    pdf.drawString(50, y, f"Matrícula: {matricula}"); y -= 20
    pdf.drawString(50, y, f"Grado: {grado_real}"); y -= 20
    pdf.drawString(50, y, f"Grupo: {grupo_real}"); y -= 20
    pdf.drawString(50, y, f"Carrera: {carrera_real}"); y -= 20
    pdf.drawString(50, y, f"Plantel: {plantel_real}"); y -= 30

    pdf.drawString(50, y, f"Riesgo personal: {riesgo_personal}%"); y -= 20
    pdf.drawString(50, y, f"Riesgo por habilidades: {riesgo_hab}%"); y -= 20
    pdf.drawString(50, y, f"Clasificación: {clasificacion}"); y -= 40

    pdf.drawString(50, y, "Factores que más afectan:"); y -= 20
    text = pdf.beginText(50, y)
    text.textLines(factores_texto)
    pdf.drawText(text)
    y -= 120

    text2 = pdf.beginText(50, y)
    text2.textLines(mensaje)
    pdf.drawText(text2)

    pdf.save()
    buffer.seek(0)
    conn.close()

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_personalizado.pdf",
        mimetype="application/pdf"
    )

from textwrap import wrap

@app.route("/reporte_general_pdf")
def reporte_general_pdf():

    grado     = request.args.get("grado")
    carrera   = request.args.get("carrera")
    grupo     = request.args.get("grupo")
    plantel   = request.args.get("plantel")
    matricula = request.args.get("matricula")

    # PROMEDIOS
    prom_personal    = calcular_promedio_riesgo_personal(grado, carrera, grupo, plantel, matricula)
    prom_habilidades = calcular_promedio_riesgo_habilidades(grado, carrera, grupo, plantel, matricula)

    # FACTORES
    factores_pers_labels, factores_pers_valores = obtener_factores_por_filtros(
        grado, carrera, grupo, plantel, matricula
    )

    factores_hab_labels, factores_hab_valores = obtener_factores_habilidades_por_filtros(
        grado, carrera, grupo, plantel, matricula
    )

    # CLASIFICACIÓN GENERAL
    if prom_personal >= 70 or prom_habilidades >= 70:
        clasificacion = "RIESGO ALTO"
    elif prom_personal >= 40 or prom_habilidades >= 40:
        clasificacion = "RIESGO MODERADO"
    else:
        clasificacion = "RIESGO BAJO"

    texto_interpretacion = (
        f"El grupo filtrado presenta un nivel de riesgo general catalogado como {clasificacion}. "
        "Los factores personales y académicos muestran áreas de oportunidad que pueden estar influyendo "
        "en el desempeño y permanencia escolar. Se recomienda seguimiento académico, tutorías "
        "y orientación personalizada."
    )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # =========================
    # ENCABEZADO (BARRA AZUL)
    # =========================
    y = height - 60

    pdf.setFillColor(colors.HexColor("#003B85"))
    pdf.rect(0, height - 80, width, 70, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 45, "SIPU UTC")

    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 60, "Reporte General de Riesgos Académicos")

    # Línea inferior del encabezado
    pdf.setStrokeColor(colors.HexColor("#002552"))
    pdf.line(50, height - 82, width - 50, height - 82)

    # Volver a negro para el contenido
    pdf.setFillColor(colors.black)
    pdf.setStrokeColor(colors.black)

    y = height - 110

    # =========================
    # DATOS GENERALES
    # =========================
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Filtros aplicados:")
    y -= 18

    pdf.setFont("Helvetica", 11)
    if carrera and carrera != "Todos":
        pdf.drawString(60, y, f"• Carrera: {carrera}"); y -= 14
    if plantel and plantel != "Todos":
        pdf.drawString(60, y, f"• Plantel: {plantel}"); y -= 14
    if grado and grado != "Todos":
        pdf.drawString(60, y, f"• Grado: {grado}"); y -= 14
    if grupo and grupo != "Todos":
        pdf.drawString(60, y, f"• Grupo: {grupo}"); y -= 20
    else:
        y -= 10

    # Línea separadora
    pdf.setStrokeColor(colors.HexColor("#DDDDDD"))
    pdf.line(50, y, width - 50, y)
    pdf.setStrokeColor(colors.black)
    y -= 20

    # =========================
    # RESUMEN DE RIESGOS
    # =========================
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Resumen de riesgos:")
    y -= 18

    pdf.setFont("Helvetica", 11)
    pdf.drawString(60, y, f"Riesgo personal promedio: {prom_personal:.1f}%")
    y -= 14
    pdf.drawString(60, y, f"Riesgo por habilidades promedio: {prom_habilidades:.1f}%")
    y -= 18

    # Badge de clasificación con color según riesgo
    if clasificacion == "RIESGO ALTO":
        badge_color = colors.HexColor("#e74c3c")
    elif clasificacion == "RIESGO MODERADO":
        badge_color = colors.HexColor("#f39c12")
    else:
        badge_color = colors.HexColor("#27ae60")

    badge_width = 220
    badge_height = 20
    badge_x = 60
    badge_y = y - badge_height + 8

    pdf.setFillColor(badge_color)
    pdf.roundRect(badge_x, badge_y, badge_width, badge_height, 4, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(
        badge_x + badge_width / 2,
        badge_y + 6,
        f"Clasificación general: {clasificacion}"
    )

    # Regresar al estilo normal
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 11)
    y = badge_y - 25

    # =========================
    # INTERPRETACIÓN (CAJA GRIS)
    # =========================
    if y < 140:
        pdf.showPage()
        pdf.setFont("Helvetica", 11)
        width, height = letter
        y = height - 80

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Interpretación:")
    y -= 18

    lineas_interpretacion = textwrap.wrap(texto_interpretacion, 95)

    # Calculamos alto de la caja
    alto_caja = 16 + 14 * len(lineas_interpretacion)
    caja_y = y - alto_caja + 8

    pdf.setFillColor(colors.HexColor("#f5f5f5"))
    pdf.rect(45, caja_y, width - 90, alto_caja, fill=1, stroke=0)

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 11)

    texto_y = y - 4
    for linea in lineas_interpretacion:
        if texto_y < 80:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            width, height = letter
            texto_y = height - 80
        pdf.drawString(55, texto_y, linea)
        texto_y -= 14

    y = texto_y - 20

    # =========================
    # FACTORES PERSONALES
    # =========================
    if y < 120:
        pdf.showPage()
        pdf.setFont("Helvetica", 11)
        width, height = letter
        y = height - 80

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Factores personales asociados:")
    y -= 16

    pdf.setFont("Helvetica", 11)
    if factores_pers_labels:
        for etiqueta, valor in zip(factores_pers_labels, factores_pers_valores):
            if y < 80:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                width, height = letter
                y = height - 80
            pdf.drawString(60, y, f"• {etiqueta}: {valor:.1f}%")
            y -= 14
    else:
        pdf.drawString(60, y, "• No hay datos suficientes")
        y -= 14

    # =========================
    # FACTORES DE HABILIDADES
    # =========================
    y -= 20
    if y < 120:
        pdf.showPage()
        pdf.setFont("Helvetica", 11)
        width, height = letter
        y = height - 80

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Factores de habilidades asociados:")
    y -= 16

    pdf.setFont("Helvetica", 11)
    if factores_hab_labels:
        for etiqueta, valor in zip(factores_hab_labels, factores_hab_valores):
            if y < 80:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                width, height = letter
                y = height - 80
            pdf.drawString(60, y, f"• {etiqueta}: {valor:.1f}%")
            y -= 14
    else:
        pdf.drawString(60, y, "• No hay datos suficientes")
        y -= 14

    # =========================
    # PIE DE PÁGINA
    # =========================
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColor(colors.HexColor("#555555"))
    pdf.drawCentredString(width / 2, 40, "Reporte generado automáticamente por SIPU UTC")

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_general_riesgos.pdf",
        mimetype="application/pdf"
    )




@app.route("/reporte_riesgo_habilidades")
def reporte_riesgo_habilidades():
    grado=request.args.get("grado")
    carrera=request.args.get("carrera")
    grupo=request.args.get("grupo")
    plantel=request.args.get("plantel")
    matricula=request.args.get("matricula")

    prom = calcular_promedio_riesgo_habilidades(grado,carrera,grupo,plantel,matricula)

    buffer=io.BytesIO()
    pdf=canvas.Canvas(buffer,pagesize=letter)
    pdf.setFont("Helvetica",10)

    pdf.drawString(50,750,"REPORTE DE RIESGO POR HABILIDADES")
    pdf.drawString(50,720,f"Porcentaje: {prom}%")

    if prom>=70:
        txt="DEFICIENCIA CRÍTICA"
    elif prom>=40:
        txt="DEFICIENCIA MEDIA"
    else:
        txt="HABILIDADES ACEPTABLES"

    pdf.drawString(50,690,f"Interpretación: {txt}")

    pdf.save()
    buffer.seek(0)

    return send_file(buffer,as_attachment=True,download_name="reporte_riesgo_habilidades.pdf",mimetype="application/pdf")
@app.route("/reporte_factores_personales")
def reporte_factores_personales():
    grado=request.args.get("grado")
    carrera=request.args.get("carrera")
    grupo=request.args.get("grupo")
    plantel=request.args.get("plantel")
    matricula=request.args.get("matricula")

    labels,valores=obtener_factores_por_filtros(grado,carrera,grupo,plantel,matricula)

    buffer=io.BytesIO()
    pdf=canvas.Canvas(buffer,pagesize=letter)
    pdf.setFont("Helvetica",10)

    pdf.drawString(50,750,"FACTORES PERSONALES")

    y=720
    for i in range(len(labels)):
        pdf.drawString(50,y,f"{labels[i]} : {valores[i]}%")
        y-=20

    pdf.save()
    buffer.seek(0)

    return send_file(buffer,as_attachment=True,download_name="factores_personales.pdf",mimetype="application/pdf")
@app.route("/reporte_factores_habilidades")
def reporte_factores_habilidades():
    grado=request.args.get("grado")
    carrera=request.args.get("carrera")
    grupo=request.args.get("grupo")
    plantel=request.args.get("plantel")
    matricula=request.args.get("matricula")

    labels,valores=obtener_factores_habilidades_por_filtros(grado,carrera,grupo,plantel,matricula)

    buffer=io.BytesIO()
    pdf=canvas.Canvas(buffer,pagesize=letter)
    pdf.setFont("Helvetica",10)

    pdf.drawString(50,750,"FACTORES DE HABILIDADES")

    y=720
    for i in range(len(labels)):
        pdf.drawString(50,y,f"{labels[i]} : {valores[i]}%")
        y-=20

    pdf.save()
    buffer.seek(0)

    return send_file(buffer,as_attachment=True,download_name="factores_habilidades.pdf",mimetype="application/pdf")


# --------------------------
# CUESTIONARIOS PERSONALES
# --------------------------
@app.route("/responder_personales", methods=["GET", "POST"])
def responder_personales():
    if session.get("rol") != "alumno":
        return redirect(url_for("index"))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ✅ TRAER PREGUNTAS
    cursor.execute("SELECT * FROM preguntas_personales")
    preguntas_raw = cursor.fetchall()

    preguntas = []
    for p in preguntas_raw:
        cursor.execute("""
            SELECT etiqueta, peso
            FROM opciones_personales
            WHERE pregunta_id=?
        """, (p["id"],))

        opciones = [dict(row) for row in cursor.fetchall()]

        preguntas.append({
            "id": p["id"],
            "texto": p["texto"],
            "tipo_pregunta": p["tipo_pregunta"],
            "opciones": opciones
        })

    # ✅ VERIFICAR SI YA CONTESTÓ
    cursor.execute(
        "SELECT * FROM respuestas_personales WHERE matricula = ?",
        (session["matricula"],)
    )
    respuestas_usuario = cursor.fetchall()
    ya_contesto = len(respuestas_usuario) > 0

    respuestas = {r["pregunta_id"]: r["respuesta"] for r in respuestas_usuario}

    if request.method == "POST":
        if ya_contesto:
            flash("Ya has respondido este cuestionario.")
            return redirect(url_for("encuesta", tipo="perfil_ingreso"))

        for p in preguntas:
            respuesta = request.form.get(f"pregunta_{p['id']}")
            if respuesta:
                cursor.execute(
                    "INSERT INTO respuestas_personales (matricula, pregunta_id, respuesta) VALUES (?, ?, ?)",
                    (session["matricula"], p["id"], respuesta)
                )

        conn.commit()
        conn.close()

        flash("Cuestionario enviado correctamente.")
        return redirect(url_for("encuesta", tipo="perfil_ingreso"))

    conn.close()
    return render_template(
        "responder_personales.html",
        preguntas=preguntas,
        ya_contesto=ya_contesto,
        respuestas=respuestas
    )







# -----------------------------------
# GESTIONAR CUESTIONARIOS PERSONALES Y HABILIDADES s
# -----------------------------------
@app.route("/gestionar_cuestionarios", methods=["GET", "POST"])
def gestionar_cuestionarios():
    if session.get("matricula") != "1020":
        return redirect(url_for("index"))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # =========================
    # ✅ AGREGAR
    # =========================
    if request.method == "POST" and "pregunta" in request.form:
        texto = request.form["pregunta"]
        tipo = request.form["tipo_pregunta"]
        elemento = request.form.get("elemento")   # ✅ AHORA VIENE DEL FORM
        opciones = request.form.getlist("opciones[]")
        pesos = request.form.getlist("pesos[]")

        cursor.execute("""
            INSERT INTO preguntas_personales (texto, tipo_pregunta, elemento)
            VALUES (?, ?, ?)
        """, (texto, tipo, elemento))

        pid = cursor.lastrowid

        if tipo == "opcion_multiple":
            for i in range(len(opciones)):
                cursor.execute("""
                    INSERT INTO opciones_personales
                    (pregunta_id, valor, etiqueta, peso)
                    VALUES (?, ?, ?, ?)
                """, (pid, i+1, opciones[i], float(pesos[i])))

        conn.commit()

    # =========================
    # ✅ ELIMINAR
    # =========================
    elif request.method == "POST" and "eliminar_id" in request.form:
        pid = request.form["eliminar_id"]
        cursor.execute("DELETE FROM opciones_personales WHERE pregunta_id=?", (pid,))
        cursor.execute("DELETE FROM preguntas_personales WHERE id=?", (pid,))
        conn.commit()

    # =========================
    # ✅ EDITAR (YA GUARDA ELEMENTO)
    # =========================
    elif request.method == "POST" and "editar_id" in request.form:
        pid = request.form["editar_id"]
        texto = request.form["editar_texto"]
        tipo = request.form.get("editar_tipo", "opcion_multiple")
        elemento = request.form.get("editar_elemento")   # ✅ NUEVO

        cursor.execute("""
            UPDATE preguntas_personales
            SET texto=?, tipo_pregunta=?, elemento=?
            WHERE id=?
        """, (texto, tipo, elemento, pid))

        cursor.execute("DELETE FROM opciones_personales WHERE pregunta_id=?", (pid,))

        opciones = request.form.getlist("editar_opciones[]")
        pesos = request.form.getlist("editar_pesos[]")

        for i in range(len(opciones)):
            cursor.execute("""
                INSERT INTO opciones_personales
                (pregunta_id, valor, etiqueta, peso)
                VALUES (?, ?, ?, ?)
            """, (pid, i+1, opciones[i], float(pesos[i])))

        conn.commit()

    # =========================
    # ✅ MOSTRAR
    # =========================
    cursor.execute("SELECT * FROM preguntas_personales")
    preguntas_raw = cursor.fetchall()

    preguntas = []
    for p in preguntas_raw:
        cursor.execute("""
            SELECT valor, etiqueta, peso
            FROM opciones_personales
            WHERE pregunta_id=?
        """, (p["id"],))

        opciones = [dict(row) for row in cursor.fetchall()]

        preguntas.append({
            "id": p["id"],
            "texto": p["texto"],
            "tipo_pregunta": p["tipo_pregunta"],
            "elemento": p["elemento"],   # ✅ YA VIENE BIEN
            "opciones": opciones
        })

    conn.close()

    return render_template("gestionar_cuestionarios.html", preguntas=preguntas)



# ---------------- ALUMNOS CRUD (admin)
@app.route("/agregar_alumno", methods=["POST"])
def agregar_alumno():
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    matricula = request.form["matricula"]
    nombre = request.form["nombre"]
    a_paterno = request.form["a_paterno"]
    a_materno = request.form["a_materno"]
    carrera = request.form["carrera"]
    plantel = request.form["plantel"]

    grado = request.form.get("grado", "")
    grupo = request.form.get("grupo", "")
    turno = request.form.get("turno", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usuarios 
        (matricula, nombre, a_paterno, a_materno, rol, carrera, plantel, nip)
        VALUES (?, ?, ?, ?, 'alumno', ?, ?, NULL)
    """, (matricula, nombre, a_paterno, a_materno, carrera, plantel))

    cursor.execute("""
        INSERT INTO alumnos_info (matricula, grado, grupo, turno)
        VALUES (?, ?, ?, ?)
    """, (matricula, grado, grupo, turno))

    conn.commit()
    conn.close()

    flash("Alumno agregado correctamente", "success")
    return redirect(url_for("menu_admin"))


@app.route("/modificar_alumno/<matricula>", methods=["POST"])
def modificar_alumno(matricula):
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    nombre = request.form["nombre"]
    a_paterno = request.form["a_paterno"]
    a_materno = request.form["a_materno"]
    carrera = request.form["carrera"]
    plantel = request.form["plantel"]

    grado = request.form.get("grado", "")
    grupo = request.form.get("grupo", "")
    turno = request.form.get("turno", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios 
        SET nombre=?, a_paterno=?, a_materno=?, carrera=?, plantel=?
        WHERE matricula=?
    """, (nombre, a_paterno, a_materno, carrera, plantel, matricula))

    cursor.execute("""
        UPDATE alumnos_info 
        SET grado=?, grupo=?, turno=?
        WHERE matricula=?
    """, (grado, grupo, turno, matricula))

    conn.commit()
    conn.close()

    flash("Alumno modificado correctamente", "success")
    return redirect(url_for("menu_admin"))


@app.route("/eliminar_alumno/<matricula>", methods=["POST"])
def eliminar_alumno(matricula):
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM respuestas WHERE matricula=?", (matricula,))
        cursor.execute("DELETE FROM respuestas_personales WHERE matricula=?", (matricula,))
        cursor.execute("DELETE FROM alumnos_info WHERE matricula=?", (matricula,))
        cursor.execute("DELETE FROM usuarios WHERE matricula=?", (matricula,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("ERROR AL ELIMINAR ALUMNO:", e)
        flash("Ocurrió un error al eliminar el alumno", "danger")

    finally:
        conn.close()

    flash("Alumno eliminado correctamente", "info")
    return redirect(url_for("menu_admin"))


# -------------------- JEFES DE CARRERA / MAESTROS CRUD (admin)
@app.route("/agregar_maestro", methods=["POST"])
def agregar_maestro():
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    id_ = request.form["id"]
    nombre = request.form["nombre"]
    a_paterno = request.form["a_paterno"]
    a_materno = request.form["a_materno"]
    carrera = request.form["carrera"]   # viene del <select>

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usuarios
        (matricula, nombre, a_paterno, a_materno, rol, carrera, plantel, nip)
        VALUES (?, ?, ?, ?, 'jefe', ?, NULL, NULL)
    """, (id_, nombre, a_paterno, a_materno, carrera))

    conn.commit()
    conn.close()

    flash("✅ Maestro agregado correctamente", "success")
    return redirect(url_for("menu_admin"))


@app.route("/modificar_maestro/<id_>", methods=["POST"])
def modificar_maestro(id_):
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    nombre = request.form["nombre"]
    a_paterno = request.form["a_paterno"]
    a_materno = request.form["a_materno"]
    carrera = request.form["carrera"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET nombre=?, a_paterno=?, a_materno=?, carrera=?
        WHERE matricula=? AND rol='jefe'
    """, (nombre, a_paterno, a_materno, carrera, id_))

    conn.commit()
    conn.close()

    flash("✏️ Maestro modificado correctamente", "success")
    return redirect(url_for("menu_admin"))


# ✅ ✅ AHORA ESTA ES LA CORRECTA PARA MAESTROS
@app.route("/eliminar_maestro/<id_>", methods=["POST"])
def eliminar_maestro(id_):
    if session.get("rol") != "admin":
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    try:
        # ✅ SOLO BORRA USUARIOS CON ROL = 'jefe'
        cursor.execute("""
            DELETE FROM usuarios
            WHERE matricula=? AND rol='jefe'
        """, (id_,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("ERROR AL ELIMINAR MAESTRO:", e)
        flash("Ocurrió un error al eliminar el maestro", "danger")

    finally:
        conn.close()

    flash("✅ Maestro eliminado correctamente", "info")
    return redirect(url_for("menu_admin"))



# --------------------------
# LOGOUT
# --------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# --------------------------
# INICIO DE LA APP
# --------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)





