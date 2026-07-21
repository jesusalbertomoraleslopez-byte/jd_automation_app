"""
database.py — Motor de Base de Datos para J&D Automation Industries
Gestiona todas las tablas: proyectos, cuentas, gastos, backorder_oc, usuarios, clasificaciones.
"""
import sqlite3
import os
import pandas as pd
import bcrypt

# Directorio de datos persistentes
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'jd_finanzas.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols

def _table_exists(cursor, table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

def init_db():
    """Crea y migra las tablas de la base de datos si es necesario."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Migración automática: detectar esquema antiguo de gastos ---
    if _table_exists(cursor, 'gastos') and (not _column_exists(cursor, 'gastos', 'subrubro') or not _column_exists(cursor, 'gastos', 'comprobante_img_filename')):
        cursor.execute("DROP TABLE gastos;")
        conn.commit()

    # --- Migración automática: detectar esquema antiguo de usuarios (columna email o password_plain) ---
    if _table_exists(cursor, 'usuarios') and (not _column_exists(cursor, 'usuarios', 'email') or not _column_exists(cursor, 'usuarios', 'password_plain')):
        cursor.execute("DROP TABLE usuarios;")
        conn.commit()

    # --- Migración automática: detectar esquema antiguo de proyectos (columna codigo) ---
    if _table_exists(cursor, 'proyectos') and not _column_exists(cursor, 'proyectos', 'codigo'):
        cursor.execute("DROP TABLE proyectos;")
        conn.commit()

    # 1. Proyectos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        monto_ingreso REAL DEFAULT 0.0,
        activo INTEGER DEFAULT 1
    );''')

    # 2. Cuentas/Tarjetas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        tipo TEXT NOT NULL CHECK(tipo IN ('Tarjeta de Crédito', 'Transferencia Bancaria', 'Efectivo'))
    );''')

    # 3. Clasificaciones (dinámicas, manejadas desde Mantenimiento)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clasificaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rubro TEXT NOT NULL,
        subrubro TEXT NOT NULL,
        concepto TEXT NOT NULL,
        UNIQUE(rubro, subrubro, concepto)
    );''')

    # 4. Gastos (con 3 niveles jerárquicos opcionales)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        concepto TEXT NOT NULL,
        monto_neto REAL NOT NULL,
        rubro TEXT,
        subrubro TEXT,
        concepto_detallado TEXT,
        proyecto_id INTEGER,
        deducible TEXT NOT NULL CHECK(deducible IN ('Sí', 'No')),
        estado_facturacion TEXT NOT NULL CHECK(estado_facturacion IN ('Pendiente', 'Facturado')),
        metodo_pago TEXT NOT NULL CHECK(metodo_pago IN ('Tarjeta de Crédito', 'Transferencia Bancaria', 'Efectivo')),
        cuenta_id INTEGER,
        rfc_proveedor TEXT,
        uuid_fiscal TEXT,
        xml_filename TEXT,
        pdf_filename TEXT,
        comprobante_img_filename TEXT,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE SET NULL,
        FOREIGN KEY (cuenta_id) REFERENCES cuentas(id) ON DELETE SET NULL
    );''')

    # 5. Backorder OC
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS backorder_oc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_oc TEXT NOT NULL UNIQUE,
        proveedor TEXT NOT NULL,
        fecha_compromiso TEXT NOT NULL,
        monto_oc REAL NOT NULL,
        proyecto_id INTEGER,
        estado TEXT NOT NULL CHECK(estado IN ('Pendiente', 'Pagado')),
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE SET NULL
    );''')

    # 6. Usuarios con roles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        password_plain TEXT,
        nombre_completo TEXT,
        email TEXT,
        rol TEXT NOT NULL CHECK(rol IN ('Administrador', 'Capturista', 'Consultor')),
        activo INTEGER DEFAULT 1
    );''')

    # 7. Gastos programados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gastos_programados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        monto REAL NOT NULL,
        fecha_compromiso TEXT NOT NULL,
        categoria TEXT NOT NULL,
        recurrente INTEGER DEFAULT 0,
        frecuencia TEXT CHECK(frecuencia IN ('Mensual', 'Bimestral', 'Única')),
        estado TEXT CHECK(estado IN ('Pendiente', 'Pagado')) DEFAULT 'Pendiente'
    );''')

    # 8. Ingresos programados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ingresos_programados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        concepto TEXT NOT NULL,
        monto REAL NOT NULL,
        fecha_esperada TEXT NOT NULL,
        estado TEXT CHECK(estado IN ('Pendiente', 'Cobrado')) DEFAULT 'Pendiente',
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE SET NULL
    );''')

    conn.commit()
    seed_demo_data(conn)
    conn.close()

# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────
def seed_demo_data(conn):
    cursor = conn.cursor()

    # Proyectos
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    if cursor.fetchone()[0] == 0:
        proyectos = [
            ("26010", "Proyecto Alfa (Línea de Ensamble)", "Instalación de línea automatizada en Querétaro", 1500000.0, 1),
            ("26011", "Proyecto Beta (Celdas Robotizadas)", "Instalación de 3 brazos robóticos KUKA", 2400000.0, 1),
            ("26012", "Mantenimiento Planta Toluca", "Mantenimiento preventivo anual de prensas", 450000.0, 1),
            ("26013", "Proyecto Gamma (Modernización CNC)", "Retrofitting de fresadoras industriales", 850000.0, 0),
        ]
        cursor.executemany("INSERT INTO proyectos (codigo, nombre, descripcion, monto_ingreso, activo) VALUES (?, ?, ?, ?, ?)", proyectos)

    # Cuentas
    cursor.execute("SELECT COUNT(*) FROM cuentas")
    if cursor.fetchone()[0] == 0:
        cuentas = [
            ("Banamex PyME *1234", "Tarjeta de Crédito"),
            ("BBVA Operativa *8829", "Transferencia Bancaria"),
            ("Caja Chica Gral", "Efectivo"),
        ]
        cursor.executemany("INSERT INTO cuentas (nombre, tipo) VALUES (?, ?)", cuentas)

    # Clasificaciones (catálogo base)
    cursor.execute("SELECT COUNT(*) FROM clasificaciones")
    if cursor.fetchone()[0] == 0:
        clasifs = [
            ("Mano de Obra y Personal", "Carga Social y Obligaciones Fiscales", "Pago IMSS/INFONAVIT"),
            ("Mano de Obra y Personal", "Carga Social y Obligaciones Fiscales", "Retención ISR Salarios"),
            ("Mano de Obra y Personal", "Carga Social y Obligaciones Fiscales", "Impuesto Sobre Nómina (ISN)"),
            ("Mano de Obra y Personal", "Carga Social y Obligaciones Fiscales", "Aportaciones a la AFORE"),
            ("Mano de Obra y Personal", "Nómina Interna Operativa", "Sueldo Base Técnicos"),
            ("Mano de Obra y Personal", "Nómina Interna Operativa", "Horas Extra"),
            ("Mano de Obra y Personal", "Nómina Interna Operativa", "Primas Vacacionales y Aguinaldos"),
            ("Mano de Obra y Personal", "Nómina Interna Operativa", "Bonos de Proyecto"),
            ("Mano de Obra y Personal", "Subcontrataciones y Destajos (Con IVA)", "Ingenieros Externos (PLC/CAD)"),
            ("Mano de Obra y Personal", "Subcontrataciones y Destajos (Con IVA)", "Contratistas de Montaje"),
            ("Mano de Obra y Personal", "Subcontrataciones y Destajos (Con IVA)", "Maquila/Torneado Externo"),
            ("Mano de Obra y Personal", "Subcontrataciones y Destajos (Con IVA)", "Agencias REPSE"),
            ("Mano de Obra y Personal", "Sueldos Administrativos y Supervisión", "Nómina Project Managers"),
            ("Mano de Obra y Personal", "Sueldos Administrativos y Supervisión", "Sueldos Dirección y Administración"),
            ("Materiales y Suministros", "Componentes del Proyecto", "Relevadores y Cableado"),
            ("Materiales y Suministros", "Componentes del Proyecto", "Pistones y Neumática"),
            ("Materiales y Suministros", "Componentes del Proyecto", "Gabinete Eléctrico"),
            ("Materiales y Suministros", "Consumibles de Taller", "Soldadura y Tornillería"),
            ("Materiales y Suministros", "Consumibles de Taller", "Cintas y EPP Menor"),
            ("Herramientas y Maquinaria", "Equipo Mayor y Renta", "Renta de Grúa Industrial"),
            ("Herramientas y Maquinaria", "Equipo Mayor y Renta", "Renta de Andamios y Plataformas"),
            ("Herramientas y Maquinaria", "Equipo Mayor y Renta", "Compra de Equipos CNC/Grandes"),
            ("Herramientas y Maquinaria", "Herramienta Menor", "Pinzas, Destornilladores, Brocas"),
            ("Herramientas y Maquinaria", "Herramienta Menor", "Multímetros y Calibradores"),
            ("Gastos Indirectos y Operación", "Logística y Viáticos de Campo", "Gasolina y Casetas"),
            ("Gastos Indirectos y Operación", "Logística y Viáticos de Campo", "Hoteles y Viáticos de Viaje"),
            ("Gastos Indirectos y Operación", "Logística y Viáticos de Campo", "Fletes y Envíos"),
            ("Gastos Indirectos y Operación", "Servicios y Oficina", "Renta de Oficina / Taller"),
            ("Gastos Indirectos y Operación", "Servicios y Oficina", "Luz, Agua e Internet"),
            ("Gastos Indirectos y Operación", "Servicios y Oficina", "Papelería y Artículos de Oficina"),
        ]
        cursor.executemany("INSERT OR IGNORE INTO clasificaciones (rubro, subrubro, concepto) VALUES (?, ?, ?)", clasifs)

    # Gastos demo
    cursor.execute("SELECT COUNT(*) FROM gastos")
    if cursor.fetchone()[0] == 0:
        gastos = [
            ('2026-07-01', 'Compra de Sensores OMRON', 45000.0, 'Materiales y Suministros', 'Componentes del Proyecto', 'Relevadores y Cableado', 1, 'Sí', 'Facturado', 'Transferencia Bancaria', 2, 'OMR900101AA1', 'E80F9C7D-8B41-4770-983C-AA0FBD452771', None, None),
            ('2026-07-03', 'Pago Técnico Soldadura', 12000.0, 'Mano de Obra y Personal', 'Nómina Interna Operativa', 'Sueldo Base Técnicos', 1, 'No', 'Pendiente', 'Efectivo', 3, None, None, None, None),
            ('2026-07-05', 'Renta de Grúa Industrial', 35000.0, 'Herramientas y Maquinaria', 'Equipo Mayor y Renta', 'Renta de Grúa Industrial', 2, 'Sí', 'Facturado', 'Tarjeta de Crédito', 1, 'ALQ881122BB2', '34BA22E8-E647-49CF-80CE-7E812D3A1BFA', None, None),
            ('2026-07-10', 'Viáticos supervisión Querétaro', 8500.0, 'Gastos Indirectos y Operación', 'Logística y Viáticos de Campo', 'Hoteles y Viáticos de Viaje', 1, 'Sí', 'Facturado', 'Tarjeta de Crédito', 1, 'HOT121212XX1', 'F29B273A-98C1-4D02-A8BD-D2690BEE77A2', None, None),
            ('2026-07-12', 'Consumibles y Tornillería', 4200.0, 'Materiales y Suministros', 'Consumibles de Taller', 'Soldadura y Tornillería', 3, 'No', 'Pendiente', 'Efectivo', 3, None, None, None, None),
            ('2026-07-14', 'Compra de Osciloscopio Digital', 28000.0, 'Herramientas y Maquinaria', 'Herramienta Menor', 'Multímetros y Calibradores', 2, 'Sí', 'Facturado', 'Transferencia Bancaria', 2, 'TEC050505TT5', '8A7C99F1-2B4A-483A-BA11-19B1A0022B8C', None, None),
            ('2026-07-15', 'Servicios de Papelería', 3100.0, 'Gastos Indirectos y Operación', 'Servicios y Oficina', 'Papelería y Artículos de Oficina', 2, 'Sí', 'Facturado', 'Tarjeta de Crédito', 1, 'PAP950818AA3', '1C1C8DFA-A31C-4B9F-8419-756E1F41A6CC', None, None),
        ]
        cursor.executemany("""INSERT INTO gastos
            (fecha, concepto, monto_neto, rubro, subrubro, concepto_detallado, proyecto_id, deducible,
             estado_facturacion, metodo_pago, cuenta_id, rfc_proveedor, uuid_fiscal, xml_filename, pdf_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", gastos)

    # Backorders demo
    cursor.execute("SELECT COUNT(*) FROM backorder_oc")
    if cursor.fetchone()[0] == 0:
        backorders = [
            ("OC-2026-001", "Siemens S.A. de C.V.", "2026-08-15", 185000.0, 1, "Pendiente"),
            ("OC-2026-002", "Pneumatics & Automation", "2026-07-28", 45000.0, 2, "Pendiente"),
            ("OC-2026-003", "Herramientas de Corte Monterrey", "2026-09-10", 67000.0, 1, "Pendiente"),
            ("OC-2026-004", "Estructuras Querétaro S.A.", "2026-07-15", 120000.0, 1, "Pagado"),
        ]
        cursor.executemany("INSERT INTO backorder_oc (numero_oc, proveedor, fecha_compromiso, monto_oc, proyecto_id, estado) VALUES (?, ?, ?, ?, ?, ?)", backorders)

    # Usuario admin por defecto
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        pwd_hash = bcrypt.hashpw("JD2024Admin".encode(), bcrypt.gensalt()).decode()
        cursor.execute("INSERT INTO usuarios (username, password_hash, password_plain, nombre_completo, email, rol, activo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("admin", pwd_hash, "JD2024Admin", "Administrador J&D", "admin@jd-automation.com", "Administrador", 1))
        # Usuario demo capturista
        pwd_c = bcrypt.hashpw("captura123".encode(), bcrypt.gensalt()).decode()
        cursor.execute("INSERT INTO usuarios (username, password_hash, password_plain, nombre_completo, email, rol, activo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       ("capturista", pwd_c, "captura123", "Capturista Demo", "captura@jd-automation.com", "Capturista", 1))

    # Gastos programados por defecto
    cursor.execute("SELECT COUNT(*) FROM gastos_programados")
    if cursor.fetchone()[0] == 0:
        gastos = [
            ("Renta Oficinas J&D", 25000.0, "2026-07-28", "Servicios", 1, "Mensual", "Pendiente"),
            ("Renta Oficinas J&D", 25000.0, "2026-08-28", "Servicios", 1, "Mensual", "Pendiente"),
            ("Renta Oficinas J&D", 25000.0, "2026-09-28", "Servicios", 1, "Mensual", "Pendiente"),
            ("Pago IMSS / Infonavit", 48500.0, "2026-07-17", "IMSS", 1, "Mensual", "Pagado"),
            ("Pago IMSS / Infonavit", 48500.0, "2026-08-17", "IMSS", 1, "Mensual", "Pendiente"),
            ("Pago IMSS / Infonavit", 48500.0, "2026-09-17", "IMSS", 1, "Mensual", "Pendiente"),
            ("SAT - Declaración Mensual", 75000.0, "2026-07-17", "SAT", 1, "Mensual", "Pagado"),
            ("SAT - Declaración Mensual", 82000.0, "2026-08-17", "SAT", 1, "Mensual", "Pendiente"),
            ("SAT - Declaración Mensual", 78000.0, "2026-09-17", "SAT", 1, "Mensual", "Pendiente"),
            ("Nómina Operativa J&D", 120000.0, "2026-07-30", "Nómina", 1, "Mensual", "Pendiente"),
            ("Nómina Operativa J&D", 120000.0, "2026-08-15", "Nómina", 1, "Mensual", "Pendiente"),
            ("Nómina Operativa J&D", 120000.0, "2026-08-30", "Nómina", 1, "Mensual", "Pendiente"),
            ("Nómina Operativa J&D", 120000.0, "2026-09-15", "Nómina", 1, "Mensual", "Pendiente"),
            ("Nómina Operativa J&D", 120000.0, "2026-09-30", "Nómina", 1, "Mensual", "Pendiente"),
        ]
        cursor.executemany("INSERT INTO gastos_programados (concepto, monto, fecha_compromiso, categoria, recurrente, frecuencia, estado) VALUES (?, ?, ?, ?, ?, ?, ?)", gastos)

    # Ingresos programados por defecto
    cursor.execute("SELECT COUNT(*) FROM ingresos_programados")
    if cursor.fetchone()[0] == 0:
        ingresos = [
            (1, "Anticipo 50% - Proyecto Alfa", 750000.0, "2026-07-15", "Cobrado"),
            (1, "Hito 30% Diseño - Proyecto Alfa", 450000.0, "2026-08-15", "Pendiente"),
            (2, "Anticipo 50% - Proyecto Beta", 1200000.0, "2026-07-20", "Cobrado"),
            (2, "Entrega de Materiales 30% - Proyecto Beta", 720000.0, "2026-09-05", "Pendiente"),
            (3, "Hito Preventivo Completo - Toluca", 450000.0, "2026-08-20", "Pendiente"),
        ]
        cursor.executemany("INSERT INTO ingresos_programados (proyecto_id, concepto, monto, fecha_esperada, estado) VALUES (?, ?, ?, ?, ?)", ingresos)

    conn.commit()

# ─────────────────────────────────────────────
# FUNCIONES DE CLASIFICACIONES (CRUD Dinámico)
# ─────────────────────────────────────────────
def get_clasificaciones_dict():
    """Retorna el diccionario jerárquico {rubro: {subrubro: [conceptos]}} desde la BD."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT rubro, subrubro, concepto FROM clasificaciones ORDER BY rubro, subrubro, concepto", conn)
    conn.close()
    result = {}
    for _, row in df.iterrows():
        r, s, c = row['rubro'], row['subrubro'], row['concepto']
        result.setdefault(r, {}).setdefault(s, []).append(c)
    return result

def get_clasificaciones_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM clasificaciones ORDER BY rubro, subrubro, concepto", conn)
    conn.close()
    return df

def add_clasificacion(rubro, subrubro, concepto):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clasificaciones (rubro, subrubro, concepto) VALUES (?, ?, ?)", (rubro, subrubro, concepto))
        conn.commit()
        return True, "Clasificación agregada correctamente."
    except sqlite3.IntegrityError:
        return False, "Esta combinación Rubro / Subrubro / Concepto ya existe."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_clasificacion(clasif_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM clasificaciones WHERE id = ?", (clasif_id,))
        conn.commit()
        return True, "Clasificación eliminada."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_rubros():
    conn = get_db_connection()
    rows = conn.execute("SELECT DISTINCT rubro FROM clasificaciones ORDER BY rubro").fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_subrubros(rubro):
    conn = get_db_connection()
    rows = conn.execute("SELECT DISTINCT subrubro FROM clasificaciones WHERE rubro=? ORDER BY subrubro", (rubro,)).fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_conceptos(rubro, subrubro):
    conn = get_db_connection()
    rows = conn.execute("SELECT concepto FROM clasificaciones WHERE rubro=? AND subrubro=? ORDER BY concepto", (rubro, subrubro)).fetchall()
    conn.close()
    return [r[0] for r in rows]

# ─────────────────────────────────────────────
# FUNCIONES DE USUARIOS
# ─────────────────────────────────────────────
def verificar_login(username, password):
    """Verifica credenciales. Retorna (nombre_completo, rol, email) o None si falla."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM usuarios WHERE username=? AND activo=1", (username,)).fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row['password_hash'].encode()):
        return {'username': row['username'], 'nombre_completo': row['nombre_completo'], 'rol': row['rol'], 'email': row['email']}
    return None

def get_usuarios_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, username, password_plain, nombre_completo, email, rol, activo FROM usuarios", conn)
    conn.close()
    return df

def add_usuario(username, password, nombre_completo, email, rol):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("INSERT INTO usuarios (username, password_hash, password_plain, nombre_completo, email, rol, activo) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                       (username, pwd_hash, password, nombre_completo, email, rol))
        conn.commit()
        return True, f"Usuario '{username}' creado con éxito."
    except sqlite3.IntegrityError:
        return False, f"El usuario '{username}' ya existe."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def cambiar_password(username, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        pwd_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("UPDATE usuarios SET password_hash=?, password_plain=? WHERE username=?", (pwd_hash, new_password, username))
        conn.commit()
        return True, "Contraseña actualizada."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_usuario_detalles(username, nombre_completo, email, rol):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE usuarios SET nombre_completo=?, email=?, rol=? WHERE username=?",
                       (nombre_completo, email, rol, username))
        conn.commit()
        return True, "Datos del usuario actualizados con éxito."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def toggle_usuario_activo(user_id, activo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE usuarios SET activo=? WHERE id=?", (activo, user_id))
        conn.commit()
        return True, "Estado de usuario actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ─────────────────────────────────────────────
# FUNCIONES DE FLUJO DE CAJA & PROGRAMACIÓN
# ─────────────────────────────────────────────
def get_gastos_programados_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, concepto, monto, fecha_compromiso, categoria, recurrente, frecuencia, estado FROM gastos_programados", conn)
    conn.close()
    return df

def insert_gasto_programado(concepto, monto, fecha_compromiso, categoria, recurrente=0, frecuencia='Única', estado='Pendiente'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO gastos_programados (concepto, monto, fecha_compromiso, categoria, recurrente, frecuencia, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (concepto, monto, fecha_compromiso, categoria, recurrente, frecuencia, estado)
        )
        conn.commit()
        return True, "Gasto programado registrado con éxito."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_gasto_programado_row(gasto_id, concepto, monto, fecha_compromiso, categoria, recurrente, frecuencia, estado):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE gastos_programados SET concepto=?, monto=?, fecha_compromiso=?, categoria=?, recurrente=?, frecuencia=?, estado=? WHERE id=?",
            (concepto, monto, fecha_compromiso, categoria, recurrente, frecuencia, estado, gasto_id)
        )
        conn.commit()
        return True, "Gasto programado actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_gasto_programado(gasto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM gastos_programados WHERE id=?", (gasto_id,))
        conn.commit()
        return True, "Gasto programado eliminado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_ingresos_programados_df():
    conn = get_db_connection()
    # Include project name and code
    query = """
    SELECT ip.id, ip.proyecto_id, p.codigo || ' - ' || p.nombre as proyecto, ip.concepto, ip.monto, ip.fecha_esperada, ip.estado
    FROM ingresos_programados ip
    LEFT JOIN proyectos p ON ip.proyecto_id = p.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def insert_ingreso_programado(proyecto_id, concepto, monto, fecha_esperada, estado='Pendiente'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO ingresos_programados (proyecto_id, concepto, monto, fecha_esperada, estado) VALUES (?, ?, ?, ?, ?)",
            (proyecto_id, concepto, monto, fecha_esperada, estado)
        )
        conn.commit()
        return True, "Ingreso programado registrado con éxito."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_ingreso_programado_row(ingreso_id, proyecto_id, concepto, monto, fecha_esperada, estado):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE ingresos_programados SET proyecto_id=?, concepto=?, monto=?, fecha_esperada=?, estado=? WHERE id=?",
            (proyecto_id, concepto, monto, fecha_esperada, estado, ingreso_id)
        )
        conn.commit()
        return True, "Ingreso programado actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_ingreso_programado(ingreso_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM ingresos_programados WHERE id=?", (ingreso_id,))
        conn.commit()
        return True, "Ingreso programado eliminado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ─────────────────────────────────────────────
# FUNCIONES DE PROYECTOS
# ─────────────────────────────────────────────
def get_proyectos(only_active=False):
    conn = get_db_connection()
    if only_active:
        df = pd.read_sql_query("SELECT * FROM proyectos WHERE activo=1 ORDER BY codigo", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM proyectos ORDER BY codigo", conn)
    conn.close()
    return df

def add_proyecto(nombre, descripcion, monto_ingreso, activo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Autogenerar código de 5 dígitos (empezando en 26010)
        cursor.execute("SELECT MAX(CAST(codigo AS INTEGER)) FROM proyectos")
        max_cod = cursor.fetchone()[0]
        if max_cod is None:
            new_codigo = 26010
        else:
            new_codigo = max_cod + 1
            
        codigo_str = str(new_codigo)
        
        cursor.execute("INSERT INTO proyectos (codigo, nombre, descripcion, monto_ingreso, activo) VALUES (?, ?, ?, ?, ?)",
                       (codigo_str, nombre, descripcion, monto_ingreso, activo))
        conn.commit()
        return True, f"Proyecto '{nombre}' creado con código {codigo_str}."
    except sqlite3.IntegrityError:
        return False, f"Ya existe un proyecto con el nombre '{nombre}' o código duplicado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_proyecto(proyecto_id, nombre, descripcion, monto_ingreso, activo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE proyectos SET nombre=?, descripcion=?, monto_ingreso=?, activo=? WHERE id=?",
                       (nombre, descripcion, monto_ingreso, activo, proyecto_id))
        conn.commit()
        return True, "Proyecto actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ─────────────────────────────────────────────
# FUNCIONES DE CUENTAS
# ─────────────────────────────────────────────
def get_cuentas():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM cuentas", conn)
    conn.close()
    return df

def add_cuenta(nombre, tipo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO cuentas (nombre, tipo) VALUES (?, ?)", (nombre, tipo))
        conn.commit()
        return True, "Cuenta creada con éxito."
    except sqlite3.IntegrityError:
        return False, f"Ya existe una cuenta con el nombre '{nombre}'."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ─────────────────────────────────────────────
# FUNCIONES DE GASTOS
# ─────────────────────────────────────────────
def get_gastos_df():
    conn = get_db_connection()
    query = """
        SELECT g.id, g.fecha, g.concepto, g.monto_neto,
               COALESCE(g.rubro, '') as rubro,
               COALESCE(g.subrubro, '') as subrubro,
               COALESCE(g.concepto_detallado, '') as concepto_detallado,
               p.nombre as proyecto_nombre, g.proyecto_id,
               g.deducible, g.estado_facturacion, g.metodo_pago,
               c.nombre as cuenta_nombre, g.cuenta_id,
               g.rfc_proveedor, g.uuid_fiscal, g.xml_filename, g.pdf_filename, g.comprobante_img_filename
        FROM gastos g
        LEFT JOIN proyectos p ON g.proyecto_id = p.id
        LEFT JOIN cuentas c ON g.cuenta_id = c.id
        ORDER BY g.fecha DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_gasto(fecha, concepto, monto_neto, proyecto_id, deducible, estado_facturacion,
              metodo_pago, cuenta_id, rubro=None, subrubro=None, concepto_detallado=None,
              rfc_proveedor=None, uuid_fiscal=None, xml_filename=None, pdf_filename=None, comprobante_img_filename=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO gastos
            (fecha, concepto, monto_neto, rubro, subrubro, concepto_detallado, proyecto_id,
             deducible, estado_facturacion, metodo_pago, cuenta_id, rfc_proveedor, uuid_fiscal, xml_filename, pdf_filename, comprobante_img_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fecha, concepto, monto_neto, rubro or None, subrubro or None, concepto_detallado or None,
             proyecto_id, deducible, estado_facturacion, metodo_pago, cuenta_id,
             rfc_proveedor, uuid_fiscal, xml_filename, pdf_filename, comprobante_img_filename))
        conn.commit()
        return True, cursor.lastrowid
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_gasto(gasto_id, **kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        fields = ", ".join([f"{k}=?" for k in kwargs])
        values = list(kwargs.values()) + [gasto_id]
        cursor.execute(f"UPDATE gastos SET {fields} WHERE id=?", values)
        conn.commit()
        return True, "Registro actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_gasto(gasto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))
        conn.commit()
        return True, "Gasto eliminado correctamente."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def limpiar_tabla(tabla):
    """Vacía completamente una tabla. Solo para Administrador."""
    tablas_permitidas = ['gastos', 'backorder_oc', 'proyectos', 'cuentas', 'clasificaciones']
    if tabla not in tablas_permitidas:
        return False, "Tabla no permitida."
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {tabla}")
        conn.commit()
        return True, f"Tabla '{tabla}' vaciada correctamente."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ─────────────────────────────────────────────
# FUNCIONES DE BACKORDER OC
# ─────────────────────────────────────────────
def get_backorders_df():
    conn = get_db_connection()
    query = """
        SELECT b.id, b.numero_oc, b.proveedor, b.fecha_compromiso, b.monto_oc,
               p.nombre as proyecto_nombre, b.proyecto_id, b.estado
        FROM backorder_oc b
        LEFT JOIN proyectos p ON b.proyecto_id = p.id
        ORDER BY b.fecha_compromiso ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_backorder(numero_oc, proveedor, fecha_compromiso, monto_oc, proyecto_id, estado='Pendiente'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO backorder_oc (numero_oc, proveedor, fecha_compromiso, monto_oc, proyecto_id, estado) VALUES (?, ?, ?, ?, ?, ?)",
                       (numero_oc, proveedor, fecha_compromiso, monto_oc, proyecto_id, estado))
        conn.commit()
        return True, "Orden de compra agregada al backorder."
    except sqlite3.IntegrityError:
        return False, f"Ya existe la orden de compra '{numero_oc}'."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_backorder_status(oc_id, estado):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE backorder_oc SET estado=? WHERE id=?", (estado, oc_id))
        conn.commit()
        return True, "Estado de OC actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# Ejecutar inicialización al importar
init_db()
