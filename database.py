import sqlite3
import os
import pandas as pd

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'jd_finanzas.db')

def get_db_connection():
    """Establece conexión a la base de datos y activa soporte para llaves foráneas."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Crea las tablas de la base de datos si no existen y siembra datos iniciales."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Detectar y migrar esquema antiguo si la columna 'subrubro' no existe en 'gastos'
    try:
        cursor.execute("SELECT subrubro FROM gastos LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gastos'")
        if cursor.fetchone():
            cursor.execute("DROP TABLE gastos;")
            conn.commit()

    # 1. Tabla de Proyectos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        monto_ingreso REAL DEFAULT 0.0,
        activo INTEGER DEFAULT 1
    );
    ''')

    # 2. Tabla de Cuentas/Tarjetas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        tipo TEXT NOT NULL CHECK(tipo IN ('Tarjeta de Crédito', 'Transferencia Bancaria', 'Efectivo'))
    );
    ''')

    # 3. Tabla de Gastos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        concepto TEXT NOT NULL,
        monto_neto REAL NOT NULL,
        rubro TEXT NOT NULL CHECK(rubro IN ('Mano de Obra y Personal', 'Materiales y Suministros', 'Herramientas y Maquinaria', 'Gastos Indirectos y Operación')),
        subrubro TEXT NOT NULL,
        concepto_detallado TEXT NOT NULL,
        proyecto_id INTEGER,
        deducible TEXT NOT NULL CHECK(deducible IN ('Sí', 'No')),
        estado_facturacion TEXT NOT NULL CHECK(estado_facturacion IN ('Pendiente', 'Facturado')),
        metodo_pago TEXT NOT NULL CHECK(metodo_pago IN ('Tarjeta de Crédito', 'Transferencia Bancaria', 'Efectivo')),
        cuenta_id INTEGER,
        rfc_proveedor TEXT,
        uuid_fiscal TEXT,
        xml_filename TEXT,
        pdf_filename TEXT,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE SET NULL,
        FOREIGN KEY (cuenta_id) REFERENCES cuentas(id) ON DELETE SET NULL
    );
    ''')

    # 4. Tabla de Backorders (Órdenes de Compra)
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
    );
    ''')

    conn.commit()
    
    # Sembrar datos de demostración si las tablas están vacías
    seed_demo_data(conn)
    
    conn.close()

def seed_demo_data(conn):
    cursor = conn.cursor()
    
    # Comprobar si hay proyectos
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    if cursor.fetchone()[0] == 0:
        proyectos = [
            ("Proyecto Alfa (Línea de Ensamble)", "Instalación de línea automatizada en Querétaro", 1500000.0, 1),
            ("Proyecto Beta (Celdas Robotizadas)", "Integración de 3 brazos robóticos KUKA", 2400000.0, 1),
            ("Mantenimiento Planta Toluca", "Mantenimiento preventivo anual de prensas", 450000.0, 1),
            ("Proyecto Gamma (Modernización CNC)", "Retrofitting de fresadoras industriales", 850000.0, 0) # Inactivo
        ]
        cursor.executemany(
            "INSERT INTO proyectos (nombre, descripcion, monto_ingreso, activo) VALUES (?, ?, ?, ?)",
            proyectos
        )
        
    # Comprobar si hay cuentas
    cursor.execute("SELECT COUNT(*) FROM cuentas")
    if cursor.fetchone()[0] == 0:
        cuentas = [
            ("Banamex PyME *1234", "Tarjeta de Crédito"),
            ("BBVA Operativa *8829", "Transferencia Bancaria"),
            ("Caja Chica Gral", "Efectivo")
        ]
        cursor.executemany(
            "INSERT INTO cuentas (nombre, tipo) VALUES (?, ?)",
            cuentas
        )
        
    # Comprobar si hay gastos
    cursor.execute("SELECT COUNT(*) FROM gastos")
    if cursor.fetchone()[0] == 0:
        # Gastos iniciales adaptados al nuevo esquema de 3 niveles
        gastos = [
            ('2026-07-01', 'Compra de Sensores OMRON', 45000.0, 'Materiales y Suministros', 'Componentes del Proyecto', 'Relevadores y Cableado', 1, 'Sí', 'Facturado', 'Transferencia Bancaria', 2, 'OMR900101AA1', 'E80F9C7D-8B41-4770-983C-AA0FBD452771', 'factura_omron.xml', None),
            ('2026-07-03', 'Pago Técnico Soldadura Especializada', 12000.0, 'Mano de Obra y Personal', 'Nómina Interna Operativa', 'Sueldo Base Técnicos', 1, 'No', 'Pendiente', 'Efectivo', 3, None, None, None, None),
            ('2026-07-05', 'Renta de Grúa Industrial', 35000.0, 'Herramientas y Maquinaria', 'Equipo Mayor y Renta', 'Renta de Grúa Industrial', 2, 'Sí', 'Facturado', 'Tarjeta de Crédito', 1, 'ALQ881122BB2', '34BA22E8-E647-49CF-80CE-7E812D3A1BFA', 'grúa_renta.xml', None),
            ('2026-07-10', 'Viáticos supervisión Querétaro', 8500.0, 'Gastos Indirectos y Operación', 'Logística y Viáticos de Campo', 'Hoteles y Viáticos de Viaje', 1, 'Sí', 'Facturado', 'Tarjeta de Crédito', 1, 'HOT121212XX1', 'F29B273A-98C1-4D02-A8BD-D2690BEE77A2', 'hotel_qro.xml', None),
            ('2026-07-12', 'Consumibles y Tornillería', 4200.0, 'Materiales y Suministros', 'Consumibles de Taller', 'Soldadura y Tornillería', 3, 'No', 'Pendiente', 'Efectivo', 3, None, None, None, None),
            ('2026-07-14', 'Compra de Osciloscopio Digital', 28000.0, 'Herramientas y Maquinaria', 'Herramienta Menor', 'Multímetros y Calibradores', 2, 'Sí', 'Facturado', 'Transferencia Bancaria', 2, 'TEC050505TT5', '8A7C99F1-2B4A-483A-BA11-19B1A0022B8C', 'tec_osc.xml', None),
            ('2026-07-15', 'Servicios de Papelería y Oficina', 3100.0, 'Gastos Indirectos y Operación', 'Servicios y Oficina', 'Papelería y Artículos de Oficina', 2, 'Sí', 'Facturado', 'Tarjeta de Crédito', 1, 'PAP950818AA3', '1C1C8DFA-A31C-4B9F-8419-756E1F41A6CC', 'papeleria.xml', None)
        ]
        cursor.executemany(
            """INSERT INTO gastos 
               (fecha, concepto, monto_neto, rubro, subrubro, concepto_detallado, proyecto_id, deducible, estado_facturacion, metodo_pago, cuenta_id, rfc_proveedor, uuid_fiscal, xml_filename, pdf_filename)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            gastos
        )

    # Comprobar si hay órdenes de compra (backorder)
    cursor.execute("SELECT COUNT(*) FROM backorder_oc")
    if cursor.fetchone()[0] == 0:
        backorders = [
            ("OC-2026-001", "Siemens S.A. de C.V.", "2026-08-15", 185000.0, 1, "Pendiente"),
            ("OC-2026-002", "Pneumatics & Automation", "2026-07-28", 45000.0, 2, "Pendiente"),
            ("OC-2026-003", "Herramientas de Corte Monterrey", "2026-09-10", 67000.0, 1, "Pendiente"),
            ("OC-2026-004", "Estructuras Querétaro S.A.", "2026-07-15", 120000.0, 1, "Pagado")
        ]
        cursor.executemany(
            "INSERT INTO backorder_oc (numero_oc, proveedor, fecha_compromiso, monto_oc, proyecto_id, estado) VALUES (?, ?, ?, ?, ?, ?)",
            backorders
        )
        
    conn.commit()

# --- Funciones de Proyectos ---
def get_proyectos(only_active=False):
    conn = get_db_connection()
    query = "SELECT * FROM proyectos"
    if only_active:
        query += " WHERE activo = 1"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_proyecto(nombre, descripcion, monto_ingreso, activo=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO proyectos (nombre, descripcion, monto_ingreso, activo) VALUES (?, ?, ?, ?)",
            (nombre, descripcion, monto_ingreso, activo)
        )
        conn.commit()
        return True, "Proyecto creado con éxito."
    except sqlite3.IntegrityError:
        return False, f"Ya existe un proyecto con el nombre '{nombre}'."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_proyecto(proyecto_id, nombre, descripcion, monto_ingreso, activo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE proyectos SET nombre=?, descripcion=?, monto_ingreso=?, activo=? WHERE id=?",
            (nombre, descripcion, monto_ingreso, activo, proyecto_id)
        )
        conn.commit()
        return True, "Proyecto actualizado con éxito."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- Funciones de Cuentas ---
def get_cuentas():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM cuentas", conn)
    conn.close()
    return df

def add_cuenta(nombre, tipo):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO cuentas (nombre, tipo) VALUES (?, ?)",
            (nombre, tipo)
        )
        conn.commit()
        return True, "Cuenta creada con éxito."
    except sqlite3.IntegrityError:
        return False, f"Ya existe una cuenta con el nombre '{nombre}'."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- Funciones de Gastos ---
def get_gastos_df():
    """Retorna un DataFrame con todos los gastos y nombres de proyectos/cuentas vinculados."""
    conn = get_db_connection()
    query = """
        SELECT g.id, g.fecha, g.concepto, g.monto_neto, g.rubro, g.subrubro, g.concepto_detallado,
               p.nombre as proyecto_nombre, g.proyecto_id,
               g.deducible, g.estado_facturacion, g.metodo_pago,
               c.nombre as cuenta_nombre, g.cuenta_id,
               g.rfc_proveedor, g.uuid_fiscal, g.xml_filename, g.pdf_filename
        FROM gastos g
        LEFT JOIN proyectos p ON g.proyecto_id = p.id
        LEFT JOIN cuentas c ON g.cuenta_id = c.id
        ORDER BY g.fecha DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_gasto(fecha, concepto, monto_neto, rubro, subrubro, concepto_detallado, proyecto_id, deducible, estado_facturacion, metodo_pago, cuenta_id, rfc_proveedor=None, uuid_fiscal=None, xml_filename=None, pdf_filename=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO gastos 
               (fecha, concepto, monto_neto, rubro, subrubro, concepto_detallado, proyecto_id, deducible, estado_facturacion, metodo_pago, cuenta_id, rfc_proveedor, uuid_fiscal, xml_filename, pdf_filename)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fecha, concepto, monto_neto, rubro, subrubro, concepto_detallado, proyecto_id, deducible, estado_facturacion, metodo_pago, cuenta_id, rfc_proveedor, uuid_fiscal, xml_filename, pdf_filename)
        )
        conn.commit()
        return True, cursor.lastrowid
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_gasto(gasto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        conn.commit()
        return True, "Gasto eliminado correctamente."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- Funciones de Backorder OC ---
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
        cursor.execute(
            "INSERT INTO backorder_oc (numero_oc, proveedor, fecha_compromiso, monto_oc, proyecto_id, estado) VALUES (?, ?, ?, ?, ?, ?)",
            (numero_oc, proveedor, fecha_compromiso, monto_oc, proyecto_id, estado)
        )
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
        cursor.execute("UPDATE backorder_oc SET estado = ? WHERE id = ?", (estado, oc_id))
        conn.commit()
        return True, "Estado de OC actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# Ejecutar inicialización al importar para asegurar que la DB esté lista
init_db()
