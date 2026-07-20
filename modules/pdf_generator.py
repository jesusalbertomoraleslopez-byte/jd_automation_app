"""
modules/pdf_generator.py — Generador de PDFs para J&D Automation Industries
Genera recibos de gastos, reportes tabulares y el manual de operación.
"""
import io
import datetime
import os
from fpdf import FPDF

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brand', 'logo_corporativo.png')

# ─── Colores corporativos ───────────────────────────────────
COLOR_CHARCOAL = (67, 78, 98)
COLOR_ORANGE = (254, 140, 41)
COLOR_GRAY = (237, 237, 237)
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_LIGHT = (140, 150, 166)

class JDPdf(FPDF):
    """PDF base con header y footer de J&D Automation Industries."""

    def header(self):
        # Franja superior naranja
        self.set_fill_color(*COLOR_CHARCOAL)
        self.rect(0, 0, 210, 22, 'F')
        # Logo si existe
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=8, y=3, h=16)
        # Título en blanco
        self.set_xy(0, 5)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(*COLOR_WHITE)
        self.cell(0, 10, 'J&D AUTOMATION INDUSTRIES', align='R', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*COLOR_ORANGE)
        self.set_x(0)
        self.cell(0, 5, 'Sistema de Control Financiero Inteligente', align='R', new_x='LMARGIN', new_y='NEXT')
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*COLOR_TEXT_LIGHT)
        self.cell(0, 5, f'Generado: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}   |   Página {self.page_no()}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(*COLOR_ORANGE)
        self.set_text_color(*COLOR_WHITE)
        self.cell(0, 8, f'  {title}', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def kv_row(self, label, value, label_width=60, shade=False):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(*COLOR_GRAY) if shade else self.set_fill_color(*COLOR_WHITE)
        self.set_text_color(*COLOR_CHARCOAL)
        self.cell(label_width, 7, label, fill=True, border=0)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 7, str(value) if value else '—', fill=shade)


def generar_pdf_gasto(gasto: dict) -> bytes:
    """Genera un recibo PDF de un gasto registrado. Retorna bytes."""
    pdf = JDPdf()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Título del recibo ──
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.cell(0, 10, 'RECIBO DE GASTO REGISTRADO', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    # Número de folio
    folio = gasto.get('id', '—')
    fecha_gen = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 6, f'Folio Interno: #{folio}   |   Fecha de Registro: {fecha_gen}', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    # ── Datos del gasto ──
    pdf.section_title('1. DATOS GENERALES DEL EGRESO')
    fields = [
        ('Fecha del Gasto:', gasto.get('fecha', '')),
        ('Concepto General:', gasto.get('concepto', '')),
        ('Monto Neto (IVA Incluido):', f"${float(gasto.get('monto_neto', 0)):,.2f} MXN"),
        ('Proyecto Asociado:', gasto.get('proyecto_nombre', 'N/A')),
        ('Método de Pago:', gasto.get('metodo_pago', '')),
        ('Cuenta / Tarjeta:', gasto.get('cuenta_nombre', 'N/A')),
    ]
    for i, (lbl, val) in enumerate(fields):
        pdf.kv_row(lbl, val, shade=(i % 2 == 0))

    pdf.ln(4)
    pdf.section_title('2. CLASIFICACIÓN CONTABLE')
    clasif_fields = [
        ('Rubro Principal:', gasto.get('rubro', 'N/A') or 'N/A'),
        ('Subrubro:', gasto.get('subrubro', 'N/A') or 'N/A'),
        ('Concepto Detallado:', gasto.get('concepto_detallado', 'N/A') or 'N/A'),
        ('Deducible / Facturable:', gasto.get('deducible', '')),
        ('Estado de Facturación:', gasto.get('estado_facturacion', '')),
    ]
    for i, (lbl, val) in enumerate(clasif_fields):
        pdf.kv_row(lbl, val, shade=(i % 2 == 0))

    if gasto.get('uuid_fiscal') or gasto.get('rfc_proveedor'):
        pdf.ln(4)
        pdf.section_title('3. DATOS FISCALES (CFDI / SAT)')
        fiscal_fields = [
            ('RFC del Proveedor:', gasto.get('rfc_proveedor', 'N/A')),
            ('UUID / Folio Fiscal:', gasto.get('uuid_fiscal', 'N/A')),
        ]
        for i, (lbl, val) in enumerate(fiscal_fields):
            pdf.kv_row(lbl, val, shade=(i % 2 == 0))

    # ── Sello ──
    pdf.ln(12)
    pdf.set_draw_color(*COLOR_CHARCOAL)
    pdf.set_line_width(0.3)
    pdf.line(14, pdf.get_y(), 100, pdf.get_y())
    pdf.line(110, pdf.get_y(), 196, pdf.get_y())
    pdf.ln(2)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(86, 5, 'Firma Capturista', align='C')
    pdf.cell(10, 5, '')
    pdf.cell(86, 5, 'Firma Vo.Bo. Dirección', align='C')
    pdf.ln(6)
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 5, 'Documento generado automaticamente por el Sistema de Control Financiero J&D Automation Industries.', align='C')

    return bytes(pdf.output())


def generar_pdf_tabla(df, titulo: str, columnas_rename: dict = None) -> bytes:
    """Genera un PDF con una tabla de datos de un DataFrame."""
    pdf = JDPdf(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.cell(0, 10, titulo, align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    if df.empty:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(*COLOR_TEXT_LIGHT)
        pdf.cell(0, 10, 'No hay datos disponibles para este reporte.', align='C')
        return bytes(pdf.output())

    display_df = df.copy()
    if columnas_rename:
        display_df = display_df.rename(columns=columnas_rename)

    cols = list(display_df.columns)
    col_width = min(260 / len(cols), 55)

    # Cabecera
    pdf.set_fill_color(*COLOR_CHARCOAL)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font('Helvetica', 'B', 8)
    for col in cols:
        pdf.cell(col_width, 8, str(col)[:18], fill=True, border=1, align='C')
    pdf.ln()

    # Filas
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(30, 30, 30)
    for i, (_, row) in enumerate(display_df.iterrows()):
        if i % 2 == 0:
            pdf.set_fill_color(*COLOR_GRAY)
        else:
            pdf.set_fill_color(*COLOR_WHITE)
        for col in cols:
            val = str(row[col]) if row[col] is not None else ''
            pdf.cell(col_width, 6, val[:22], fill=True, border=1)
        pdf.ln()

    return bytes(pdf.output())


def generar_pdf_manual() -> bytes:
    """Genera el Manual de Operacion completo en PDF."""
    pdf = JDPdf()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Portada
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.ln(20)
    pdf.cell(0, 12, 'MANUAL DE OPERACION DEL SISTEMA', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(*COLOR_ORANGE)
    pdf.cell(0, 8, 'Control Financiero Inteligente - J&D Automation Industries', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 6, f'Version 2.0   |   {datetime.datetime.now().strftime("%B %Y")}', align='C')
    pdf.ln(20)

    # Secciones del manual
    secciones = [
        ("1. Introduccion",
         "El Sistema de Control Financiero de J&D Automation Industries es una aplicacion web desarrollada en Python/Streamlit "
         "disenada para centralizar, clasificar y analizar los egresos operativos y de proyectos de la empresa. "
         "Permite la captura manual de gastos, importacion masiva desde Excel, analisis EBITDA, dashboards interactivos "
         "y generacion de reportes en PDF con respaldo automatico de cada transaccion."),

        ("2. Acceso y Roles de Usuario",
         "La aplicacion requiere autenticacion con usuario y contrasena.\n"
         "  * Administrador: Acceso total. Puede crear, editar y eliminar cualquier registro, gestionar usuarios "
         "y acceder al modulo de Mantenimiento del Sistema.\n"
         "  * Capturista: Puede registrar gastos, proyectos, cuentas y OCs. No puede eliminar registros.\n"
         "  * Consultor: Acceso de solo lectura. Puede visualizar dashboards y descargar reportes.\n\n"
         "Credenciales por defecto: admin / JD2024Admin. Cambie la contrasena en Modulo 8 -> Gestion de Usuarios."),

        ("3. Modulo 1 - Inicio & Registro",
         "Contiene 4 sub-secciones:\n"
         "  1.1 Proyectos: Alta y gestion de proyectos con nombre, descripcion y monto contratado.\n"
         "  1.2 Cuentas & Tarjetas: Registro de metodos de pago (Tarjeta, Transferencia, Efectivo).\n"
         "  1.3 Captura de Gasto: Formulario principal de registro de egresos con clasificacion jerarquica "
         "(Rubro -> Subrubro -> Concepto), validacion de XML/CFDI del SAT, y generacion automatica de recibo PDF.\n"
         "  1.4 Ordenes de Compra (Backorder): Registro y seguimiento de compromisos de pago futuros."),

        ("4. Clasificacion Jerarquica de Gastos",
         "Los gastos se clasifican en 3 niveles opcionales:\n"
         "  Nivel 1 - Rubro Principal (ej. 'Mano de Obra y Personal')\n"
         "  Nivel 2 - Subrubro (ej. 'Nomina Interna Operativa')\n"
         "  Nivel 3 - Concepto Detallado (ej. 'Sueldo Base Tecnicos')\n\n"
         "Estos campos son opcionales: si el gasto no tiene una clasificacion definida, puede dejarse en blanco. "
         "El catalogo de clasificaciones es dinamico y puede administrarse en el Modulo 8 -> Gestion de Clasificaciones."),

        ("5. Modulo 2 - Carga Masiva (Excel)",
         "Permite importar multiples gastos en un solo archivo Excel.\n"
         "  5.1 Descargue la plantilla desde el boton 'Descargar Plantilla'. Esta plantilla incluye las listas "
         "desplegables validadas con los proyectos activos y catalogos vigentes.\n"
         "  5.2 Llene la plantilla con los gastos y cargue el archivo. El sistema validara cada fila antes de importar."),

        ("6. Modulo 8 - Mantenimiento del Sistema (Solo Administrador)",
         "  8.1 Gestion de Clasificaciones: CRUD completo para agregar, ver y eliminar Rubros, Subrubros y Conceptos.\n"
         "  8.2 Gestion de Usuarios: Crear usuarios, asignar roles, activar/desactivar y cambiar contrasenas.\n"
         "  8.3 Correccion de Registros: Edicion directa de campos en gastos ya registrados.\n"
         "  8.4 Limpieza de Base de Datos: Vaciado selectivo de tablas con confirmacion doble.\n"
         "  8.5 Explorador de Almacenamiento: Visualizacion y eliminacion de archivos en el servidor."),

        ("7. Reglas Fiscales Homologadas",
         "  * Todos los montos se ingresan como MONTO NETO CON IVA INCLUIDO.\n"
         "  * Si el estado de facturación es 'Facturado', se recomienda adjuntar el XML (CFDI) y PDF de la factura. "
         "El sistema extraera automaticamente el RFC del proveedor, el UUID fiscal y verificara el total.\n"
         "  * Los gastos bajo el subrubro 'Equipo Mayor y Renta' se excluyen del calculo de EBITDA "
         "(se tratan como depreciacion de activos fijos)."),
    ]

    for titulo_sec, contenido in secciones:
        pdf.section_title(titulo_sec)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 6, contenido)
        pdf.ln(4)

    return bytes(pdf.output())
