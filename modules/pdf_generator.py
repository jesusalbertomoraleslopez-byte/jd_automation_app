"""
modules/pdf_generator.py — Generador de PDFs para J&D Automation Industries
Utiliza la hoja membretada oficial corporativa con márgenes calibrados para recibos de gastos,
órdenes de compra (backorder), reportes tabulares y el manual de operación.
"""
import io
import datetime
import os
from fpdf import FPDF

BRAND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brand')
LOGO_PATH = os.path.join(BRAND_DIR, 'logo_corporativo.png')
LETTERHEAD_PATH = os.path.join(BRAND_DIR, 'hoja_membretada.png')

# ─── Colores corporativos J&D ───────────────────────────────
COLOR_CHARCOAL = (67, 78, 98)
COLOR_ORANGE = (254, 140, 41)
COLOR_GRAY = (245, 247, 250)
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_LIGHT = (120, 130, 145)

class JDPdf(FPDF):
    """PDF base con hoja membretada oficial de J&D Automation Industries."""

    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        # Márgenes calibrados exactamente para no empalmar con cabecera (44mm) ni pie de página (42mm)
        if orientation == 'P':
            self.set_margins(15, 46, 15)
            self.set_auto_page_break(auto=True, margin=46)
        else:
            self.set_margins(15, 38, 15)
            self.set_auto_page_break(auto=True, margin=36)

    def header(self):
        # Dibujar la hoja membretada oficial de fondo
        if os.path.exists(LETTERHEAD_PATH):
            self.image(LETTERHEAD_PATH, x=0, y=0, w=self.w, h=self.h)
        else:
            # Fallback en caso de que no exista la imagen
            self.set_fill_color(*COLOR_CHARCOAL)
            self.rect(0, 0, self.w, 20, 'F')
            if os.path.exists(LOGO_PATH):
                self.image(LOGO_PATH, x=8, y=2, h=16)
            self.set_xy(0, 4)
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(*COLOR_WHITE)
            self.cell(0, 8, 'J&D AUTOMATION INDUSTRIES', align='R', new_x='LMARGIN', new_y='NEXT')

    def footer(self):
        # Colocar número de página y fecha arriba de la barra inferior de la hoja membretada
        self.set_y(-42 if self.cur_orientation == 'P' else -32)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*COLOR_CHARCOAL)
        self.cell(0, 4, f'Generado: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}   |   Página {self.page_no()}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(*COLOR_ORANGE)
        self.set_text_color(*COLOR_WHITE)
        self.cell(0, 7, f'  {title}', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def kv_row(self, label, value, label_width=60, shade=False):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(*COLOR_GRAY) if shade else self.set_fill_color(*COLOR_WHITE)
        self.set_text_color(*COLOR_CHARCOAL)
        self.cell(label_width, 7, label, fill=True, border=0)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(30, 30, 30)
        remaining_width = self.w - self.r_margin - self.x
        val_str = str(value) if (value and str(value).strip() != '') else 'N/A'
        val_str = val_str.replace('—', '-').replace('–', '-')
        self.multi_cell(remaining_width, 7, val_str, fill=shade, new_x='LMARGIN', new_y='NEXT')


def generar_pdf_gasto(gasto: dict) -> bytes:
    """Genera un recibo PDF de un gasto registrado sobre la hoja membretada."""
    pdf = JDPdf()
    pdf.add_page()

    # ── Título del recibo ──
    pdf.set_font('Helvetica', 'B', 15)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.cell(0, 8, 'RECIBO DE GASTO REGISTRADO', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    # Número de folio
    folio = gasto.get('id', 'N/A')
    fecha_gen = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 5, f'Folio Interno: #{folio}   |   Fecha de Registro: {fecha_gen}', align='C', new_x='LMARGIN', new_y='NEXT')
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

    pdf.ln(3)
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
        pdf.ln(3)
        pdf.section_title('3. DATOS FISCALES (CFDI / SAT)')
        fiscal_fields = [
            ('RFC del Proveedor:', gasto.get('rfc_proveedor', 'N/A')),
            ('UUID / Folio Fiscal:', gasto.get('uuid_fiscal', 'N/A')),
        ]
        for i, (lbl, val) in enumerate(fiscal_fields):
            pdf.kv_row(lbl, val, shade=(i % 2 == 0))

    # ── Sello de Firmas ──
    pdf.ln(10)
    pdf.set_draw_color(*COLOR_CHARCOAL)
    pdf.set_line_width(0.3)
    pdf.line(20, pdf.get_y(), 95, pdf.get_y())
    pdf.line(115, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(75, 4, 'Firma Capturista', align='C')
    pdf.cell(20, 4, '')
    pdf.cell(75, 4, 'Firma Vo.Bo. Dirección', align='C')
    pdf.ln(5)
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 4, 'Documento generado automáticamente por el Sistema de Control Financiero J&D Automation Industries.', align='C')

    return bytes(pdf.output())


def generar_pdf_orden_compra(orden: dict) -> bytes:
    """Genera un PDF oficial de Orden de Compra (OC) sobre la hoja membretada corporativa."""
    pdf = JDPdf()
    pdf.add_page()

    # ── Título del Documento ──
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.cell(0, 8, 'ORDEN DE COMPRA (BACKORDER)', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    folio = orden.get('numero_oc', 'N/A')
    fecha_gen = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 5, f'Folio de OC: #{folio}   |   Fecha de Emisión: {fecha_gen}', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    # ── Datos de la Orden de Compra ──
    pdf.section_title('1. INFORMACIÓN DE LA ORDEN DE COMPRA')
    fields = [
        ('Folio de la OC:', orden.get('numero_oc', 'N/A')),
        ('Proveedor:', orden.get('proveedor', 'N/A')),
        ('Fecha Compromiso de Pago:', orden.get('fecha_compromiso', 'N/A')),
        ('Monto de la OC (IVA Incluido):', f"${float(orden.get('monto_oc', 0)):,.2f} MXN"),
        ('Proyecto Destino:', orden.get('proyecto_nombre', 'N/A')),
        ('Estado de Pago:', orden.get('estado_pago', 'Pendiente')),
    ]
    for i, (lbl, val) in enumerate(fields):
        pdf.kv_row(lbl, val, shade=(i % 2 == 0))

    # ── Términos y Condiciones ──
    pdf.ln(4)
    pdf.section_title('2. TÉRMINOS Y CONDICIONES DE ENTREGA Y PAGO')
    terminos = (
        "1. La entrega de materiales o servicios se realizará según la fecha compromiso estipulada.\n"
        "2. Todas las facturas deberán emitirse a nombre de J&D Automation Industries con IVA desglose.\n"
        "3. El pago se efectuará conforme a los plazos pactados tras recepción a satisfacción de los insumos.\n"
        "4. Indicar el número de Folio de OC en toda la correspondencia y facturas fiscales relativas a esta orden."
    )
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 4.5, terminos)

    # ── Sello de Firmas de Autorización ──
    pdf.ln(12)
    pdf.set_draw_color(*COLOR_CHARCOAL)
    pdf.set_line_width(0.3)
    
    y_line = pdf.get_y()
    pdf.line(15, y_line, 70, y_line)
    pdf.line(80, y_line, 135, y_line)
    pdf.line(145, y_line, 195, y_line)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(55, 4, 'Elaboró (Compras)', align='C')
    pdf.cell(10, 4, '')
    pdf.cell(55, 4, 'Autorizó (Gerencia)', align='C')
    pdf.cell(10, 4, '')
    pdf.cell(50, 4, 'Vo.Bo. Dirección', align='C')
    pdf.ln(6)
    
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 4, 'Documento oficial de compromiso comercial generado por el Sistema de Control Financiero J&D Automation Industries.', align='C')

    return bytes(pdf.output())


def generar_pdf_tabla(df, titulo: str, columnas_rename: dict = None) -> bytes:
    """Genera un PDF horizontal (Landscape) sobre la hoja membretada con una tabla de datos."""
    pdf = JDPdf(orientation='L')
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.cell(0, 8, titulo, align='C', new_x='LMARGIN', new_y='NEXT')
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
    col_width = min(265 / len(cols), 55)

    # Cabecera
    pdf.set_fill_color(*COLOR_CHARCOAL)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.set_font('Helvetica', 'B', 8)
    for col in cols:
        pdf.cell(col_width, 7, str(col)[:18], fill=True, border=1, align='C')
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
            val = val.replace('—', '-').replace('–', '-')
            pdf.cell(col_width, 6, val[:22], fill=True, border=1)
        pdf.ln()

    return bytes(pdf.output())


def generar_pdf_manual() -> bytes:
    """Genera el Manual de Operación completo en PDF sobre la hoja membretada."""
    pdf = JDPdf()
    pdf.add_page()

    # Portada
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.ln(4)
    pdf.cell(0, 10, 'MANUAL DE OPERACIÓN DEL SISTEMA', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(*COLOR_ORANGE)
    pdf.cell(0, 6, 'Control Financiero Inteligente - J&D Automation Industries', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)
    now = datetime.datetime.now()
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    pdf.cell(0, 5, f'Versión 2.0   |   {meses_es[now.month]} {now.year}', align='C')
    pdf.ln(10)

    # Secciones del manual
    secciones = [
        ("1. Introducción",
         "El Sistema de Control Financiero de J&D Automation Industries es una aplicación web desarrollada en Python/Streamlit "
         "diseñada para centralizar, clasificar y analizar los egresos operativos y de proyectos de la empresa. "
         "Permite la captura manual de gastos, importación masiva desde Excel, análisis EBITDA, dashboards interactivos "
         "y generación de reportes en PDF respaldados en la hoja membretada oficial."),

        ("2. Acceso y Roles de Usuario",
         "La aplicación requiere autenticación con usuario y contraseña.\n"
         "  * Administrador: Acceso total. Puede crear, editar y eliminar cualquier registro, gestionar usuarios "
         "y acceder al módulo de Mantenimiento del Sistema.\n"
         "  * Capturista: Puede registrar gastos, proyectos, cuentas y OCs. No puede eliminar registros.\n"
         "  * Consultor: Acceso de solo lectura. Puede visualizar dashboards y descargar reportes.\n\n"
         "Credenciales por defecto: admin / JD2024Admin. Cambie la contraseña en Módulo 8 -> Gestión de Usuarios."),

        ("3. Módulo 1 - Gastos (Captura & Carga Masiva)",
         "Contiene 2 sub-secciones:\n"
         "  1.1 Captura Individual de Gasto: Formulario principal de egresos con soporte para CFDI/XML, comprobante en foto o "
         "pegar directamente desde el portapapeles (Ctrl+V), y recibo PDF generado sobre la hoja membretada corporativa.\n"
         "  1.2 Carga Masiva (Excel): Importación transaccional con plantilla validada vinculada a la base de datos."),

        ("4. Módulo 2 - Proyectos (Gestión & Pareto)",
         "Contiene 5 sub-secciones:\n"
         "  2.1 Alta & Gestión de Proyectos: Registro con código de 5 dígitos, nombre, descripción e ingreso contratado.\n"
         "  2.2 Órdenes de Compra (Backorder): Registro de compromisos de compra futuros y generación de PDF de OC.\n"
         "  2.3 Estado General por Proyecto: Semáforo de salud financiera, presupuesto contratado vs gasto real y utilidad.\n"
         "  2.4 Pareto de Costos: Gráfica 80/20 de los conceptos de mayor costo por proyecto.\n"
         "  2.5 Progreso vs Presupuesto: Avance porcentual de la ejecución presupuestaria."),

        ("5. Módulo 3 - Flujo de Caja Proyectado y Flujo de Información de Pagos (Opción A)",
         "Permite proyectar la salud financiera de la empresa semana a semana (3 meses) y ejecutar pagos:\n"
         "  3.1 Matriz de Flujo Semanal: Vista interactiva con código de colores (Verde para ejecutados, Rosa para pendientes).\n"
         "  3.2 Flujo de Información de Pagos (Opción A):\n"
         "      * PASO 1 (Programación): Se registra el gasto futuro en 3.4 (Estado: Pendiente / Celda Rosa en Matriz).\n"
         "      * PASO 2 (Ejecución): En 3.2 se selecciona el gasto pendiente, se confirma el monto/fecha real y se asigna Cuenta Bancaria y Método de Pago.\n"
         "      * PASO 3 (Impacto Contable): El sistema genera el egreso real en la BD, cambia el estatus a PAGADO, vuelve verde la celda en la Matriz y recalcula el Saldo Acumulado de Caja en tiempo real.\n"
         "  3.3 Exportar Excel y Correo .EML: Descarga la matriz quincenal en Excel y genera el correo ejecutivo .eml con gráficos e imagen de cabecera."),

        ("6. Módulo 8 - Mantenimiento del Sistema (Solo Administrador)",
         "  8.1 Cuentas & Tarjetas: Registro de bancos, tarjetas y métodos de pago.\n"
         "  8.2 Gestión de Clasificaciones: Catálogo dinámico para agregar/eliminar Rubros, Subrubros y Conceptos.\n"
         "  8.3 Gestión de Usuarios: Crear usuarios, asignar roles, activar/desactivar y cambiar contraseñas.\n"
         "  8.4 Corrección de Registros: Edición directa de campos en gastos ya registrados.\n"
         "  8.5 Limpieza de Base de Datos: Vaciado selectivo de tablas con confirmación doble."),

        ("7. Reglas Fiscales Homologadas",
         "  * Todos los montos se ingresan como MONTO NETO CON IVA INCLUIDO.\n"
         "  * Si el estado de facturación es 'Facturado', se recomienda adjuntar el XML (CFDI) y PDF de la factura. "
         "El sistema extraerá automáticamente el RFC del proveedor, el UUID fiscal y verificará el total.\n"
         "  * Los gastos bajo el subrubro 'Equipo Mayor y Renta' se excluyen del cálculo de EBITDA "
         "(se tratan como depreciación de activos fijos)."),
    ]

    for titulo_sec, contenido in secciones:
        pdf.section_title(titulo_sec)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5, contenido)
        pdf.ln(3)

    return bytes(pdf.output())


def generar_pdf_catalogo_clasificaciones(df_clasificaciones=None):
    """
    Genera un reporte oficial en PDF con el Catálogo de Clasificaciones Activas
    de J&D Automation Industries utilizando la hoja membretada institucional.
    """
    from database import get_clasificaciones_df
    
    if df_clasificaciones is None or df_clasificaciones.empty:
        df_clasificaciones = get_clasificaciones_df()

    pdf = JDPdf(orientation='P', unit='mm', format='A4')
    pdf.add_page()

    # Título principal del reporte
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.cell(0, 8, 'CATÁLOGO DE CLASIFICACIONES DE GASTOS Y PROYECTOS', align='L', new_x='LMARGIN', new_y='NEXT')
    
    # Subtítulo y fecha
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*COLOR_TEXT_LIGHT)
    pdf.cell(0, 5, f'J&D AUTOMATION INDUSTRIES S.A. DE C.V.  |  Fecha de emisión: {datetime.date.today().strftime("%d/%m/%Y")}', align='L', new_x='LMARGIN', new_y='NEXT')
    
    # Resumen cuantitativo
    total_items = len(df_clasificaciones)
    total_rubros = df_clasificaciones['rubro'].nunique() if 'rubro' in df_clasificaciones.columns else 0
    
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*COLOR_CHARCOAL)
    pdf.cell(0, 5, f'Total de Rubros Principales: {total_rubros}   |   Total de Clasificaciones Registradas: {total_items}', align='L', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    # Encabezado de la Tabla
    # Ancho total en A4 retrato: 180mm disponible
    col_w = [15, 50, 50, 65]
    headers = ['ID', 'Rubro Principal', 'Subrubro', 'Concepto Detallado']

    def render_table_header():
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(*COLOR_CHARCOAL)
        pdf.set_text_color(*COLOR_WHITE)
        for idx, h in enumerate(headers):
            pdf.cell(col_w[idx], 7, h, border=1, fill=True, align='C' if idx == 0 else 'L')
        pdf.ln()

    render_table_header()

    # Rellenar filas
    pdf.set_font('Helvetica', '', 8.5)
    row_alt = False

    for row in df_clasificaciones.itertuples():
        if pdf.get_y() > 240:
            pdf.add_page()
            render_table_header()

        c_id = str(getattr(row, 'id', ''))
        rubro = str(getattr(row, 'rubro', ''))
        subrubro = str(getattr(row, 'subrubro', ''))
        concepto = str(getattr(row, 'concepto', ''))

        if row_alt:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
        row_alt = not row_alt

        pdf.set_text_color(*COLOR_CHARCOAL)
        
        pdf.cell(col_w[0], 6.5, c_id, border=1, fill=True, align='C')
        pdf.cell(col_w[1], 6.5, rubro[:28], border=1, fill=True, align='L')
        pdf.cell(col_w[2], 6.5, subrubro[:28], border=1, fill=True, align='L')
        pdf.cell(col_w[3], 6.5, concepto[:38], border=1, fill=True, align='L')
        pdf.ln()

    return bytes(pdf.output())

