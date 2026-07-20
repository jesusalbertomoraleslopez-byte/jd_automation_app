import streamlit as st
import pandas as pd
import datetime
import os
import shutil
import io

# Configuración de página (Debe ser el primer comando de Streamlit)
st.set_page_config(
    page_title="J&D Automation Industries - Control Financiero",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS Personalizado para la Identidad Visual de J&D
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;900&display=swap');
    
    /* Aplicar tipografía Nexa/Montserrat corporativa */
    html, body, [class*="css"], .stWidget, .stMarkdown, p, span, li, label, input, button, select {
        font-family: 'Montserrat', 'Inter', sans-serif !important;
    }

    /* Fondo gris claro (#EDEDED) */
    .stApp {
        background-color: #EDEDED;
    }
    
    /* Títulos y encabezados en Charcoal (#434E62) */
    h1, h2, h3, h4, h5, h6 {
        color: #434E62 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar en Charcoal (#434E62) */
    section[data-testid="stSidebar"] {
        background-color: #434E62 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* Selección del menú en el Sidebar */
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    
    /* Pestañas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #434E62 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FE8C29 !important;
        border-bottom-color: #FE8C29 !important;
    }

    /* Tarjetas de Métricas (Monto Neto) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #EDEDED !important;
        border-left: 5px solid #FE8C29 !important; /* Acento UT Orange */
        padding: 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #434E62 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #8C96A6 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Formularios */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #EDEDED !important;
        border-radius: 12px !important;
        padding: 25px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
    }
    
    /* Bordes al enfocar inputs */
    input[type="text"]:focus, input[type="number"]:focus, textarea:focus, select:focus {
        border-color: #FE8C29 !important;
        box-shadow: 0 0 0 1px #FE8C29 !important;
    }
    
    /* Botones en UT Orange (#FE8C29) con texto Blanco (#FFFFFF) */
    div.stButton > button:first-child, div.stFormSubmitButton > button:first-child {
        background-color: #FE8C29 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        box-shadow: 0 2px 5px rgba(254, 140, 41, 0.3) !important;
        transition: transform 0.1s, background-color 0.2s !important;
    }
    div.stButton > button:first-child:hover, div.stFormSubmitButton > button:first-child:hover {
        background-color: #e0771b !important;
        color: #FFFFFF !important;
    }
    div.stButton > button:first-child:active, div.stFormSubmitButton > button:first-child:active {
        transform: scale(0.98) !important;
    }

    /* Alertas */
    div[data-testid="stAlert"] {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

def render_header(title, subtitle):
    # Contenedor estilizado para el encabezado con la imagen corporativa en PNG transparente
    with st.container():
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
            st.image("brand/logo_corporativo.png", width=160)
        with col_title:
            st.markdown(f"""
            <div style="border-left: 3px solid #FE8C29; padding-left: 20px; margin-top: 5px;">
              <h2 style="margin: 0; color: #434E62; font-family: 'Montserrat', sans-serif; font-size: 24px; font-weight: 700;">{title}</h2>
              <p style="margin: 3px 0 0 0; color: #8C96A6; font-family: 'Montserrat', sans-serif; font-size: 13px;">{subtitle}</p>
            </div>
            """, unsafe_allow_html=True)


# Importación de módulos internos del proyecto
import database as db
from modules.xml_parser import parse_cfdi_xml
from modules.excel_handler import generate_excel_template, import_excel_expenses
import modules.dashboards as dash

# Crear directorio para almacenar comprobantes físicos
COMPROBANTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'comprobantes')
os.makedirs(COMPROBANTES_DIR, exist_ok=True)

# Inicializar sesión de Streamlit para controlar recargas
if 'expense_submitted' not in st.session_state:
    st.session_state['expense_submitted'] = False

# --- BARRA LATERAL / NAVEGACIÓN ---
st.sidebar.image("brand/logo_blanco.png", use_container_width=True)
st.sidebar.markdown("<h3 style='color: #FFFFFF; text-align: center; margin-top:0; font-family:\"Montserrat\"; font-size: 18px;'>Control Financiero</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación del Sistema",
    [
        "🏠 Inicio & Registro",
        "📂 Carga Masiva (Excel)",
        "📊 Dashboards Interactivos",
        "💰 EBITDA & Reportes de Cuenta"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Regla Fiscal Homologada:** Todos los montos se ingresan como **MONTO NETO CON IVA INCLUIDO**."
)

# --- MÓDULO 1: INICIO Y REGISTRO ---
if menu == "🏠 Inicio & Registro":
    render_header("Control de Registro", "Gestione proyectos, cuentas y capture los gastos de la operación diaria.")

    
    tab_proyectos, tab_cuentas, tab_gastos, tab_backorder = st.tabs([
        "📁 Proyectos", 
        "💳 Cuentas & Tarjetas", 
        "💵 Captura de Gasto", 
        "📝 Órdenes de Compra (Backorder)"
    ])
    
    # --- SUBTAB: PROYECTOS ---
    with tab_proyectos:
        st.subheader("Administración de Proyectos")
        col_list, col_form = st.columns([2, 1])
        
        with col_form:
            st.markdown("#### **Crear Nuevo Proyecto**")
            p_nombre = st.text_input("Nombre del Proyecto", placeholder="Ej. Línea C3 - Planta GM")
            p_desc = st.text_area("Descripción", placeholder="Detalles de la cotización...")
            p_monto = st.number_input("Ingreso Contratado (Monto Neto)", min_value=0.0, step=1000.0, format="%.2f")
            p_activo = st.selectbox("Estado del Proyecto", ["Activo", "Inactivo"])
            
            if st.button("Guardar Proyecto"):
                if p_nombre:
                    status = 1 if p_activo == "Activo" else 0
                    success, msg = db.add_proyecto(p_nombre, p_desc, p_monto, status)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("El nombre del proyecto es obligatorio.")
                    
        with col_list:
            st.markdown("#### **Proyectos Registrados**")
            df_p = db.get_proyectos()
            if not df_p.empty:
                df_p_disp = df_p.copy()
                df_p_disp['activo'] = df_p_disp['activo'].map({1: 'Activo', 0: 'Inactivo'})
                df_p_disp['monto_ingreso'] = df_p_disp['monto_ingreso'].map('${:,.2f}'.format)
                df_p_disp.columns = ['ID', 'Nombre', 'Descripción', 'Ingreso Contratado (Neto)', 'Estado']
                st.dataframe(df_p_disp, use_container_width=True, hide_index=True)
            else:
                st.info("No hay proyectos registrados.")

    # --- SUBTAB: CUENTAS ---
    with tab_cuentas:
        st.subheader("Cuentas y Tarjetas de Pago")
        col_c_list, col_c_form = st.columns([2, 1])
        
        with col_c_form:
            st.markdown("#### **Añadir Cuenta**")
            c_nombre = st.text_input("Nombre de la Cuenta / Tarjeta", placeholder="Ej. Banorte Corporativa *5678")
            c_tipo = st.selectbox("Tipo de Cuenta", ["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"])
            
            if st.button("Guardar Cuenta"):
                if c_nombre:
                    success, msg = db.add_cuenta(c_nombre, c_tipo)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("El nombre de la cuenta es obligatorio.")
                    
        with col_c_list:
            st.markdown("#### **Cuentas Configuradas**")
            df_c = db.get_cuentas()
            if not df_c.empty:
                df_c.columns = ['ID', 'Nombre de la Cuenta', 'Tipo de Cuenta']
                st.dataframe(df_c, use_container_width=True, hide_index=True)
            else:
                st.info("No hay cuentas configuradas.")

    # --- SUBTAB: CAPTURA DE GASTO ---
    with tab_gastos:
        st.subheader("Captura Manual de Gasto")
        st.markdown("Registre un egreso manualmente e integre comprobantes fiscales.")
        
        # Obtener catálogos para los selects
        df_p_activos = db.get_proyectos(only_active=True)
        df_c_all = db.get_cuentas()
        
        if df_p_activos.empty:
            st.warning("Debe registrar al menos un proyecto activo para poder capturar gastos.")
        elif df_c_all.empty:
            st.warning("Debe registrar al menos una cuenta para poder capturar gastos.")
        else:
            with st.form("form_gasto", clear_on_submit=True):
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    g_fecha = st.date_input("Fecha de Gasto", datetime.date.today())
                    g_concepto = st.text_input("Concepto del Gasto", placeholder="Ej. Compra de relevadores y cableado")
                    g_monto = st.number_input("Monto Neto (IVA Incluido)", min_value=0.01, step=50.0, format="%.2f")
                    g_rubro = st.selectbox(
                        "Rubro de Gasto", 
                        ['Materiales', 'Mano de obra', 'Supervisión', 'Gastos generales', 'Herramienta', 'Maquinaria']
                    )
                    proyecto_options = dict(zip(df_p_activos['nombre'], df_p_activos['id']))
                    g_proy_name = st.selectbox("Proyecto Asociado", list(proyecto_options.keys()))
                    g_proy_id = proyecto_options[g_proy_name]
                    
                with col_g2:
                    g_deducible = st.selectbox("¿Deducible / Facturable?", ["Sí", "No"])
                    g_estado_fact = st.selectbox("Estatus de Facturación", ["Pendiente", "Facturado"])
                    g_metodo = st.selectbox("Método de Pago", ["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"])
                    
                    # Filtrar cuentas correspondientes al método de pago
                    df_c_filtradas = df_c_all[df_c_all['tipo'] == g_metodo]
                    if df_c_filtradas.empty:
                        st.error(f"No hay cuentas registradas para el método: {g_metodo}. Configure una primero.")
                        g_cuenta_id = None
                    else:
                        cuenta_options = dict(zip(df_c_filtradas['nombre'], df_c_filtradas['id']))
                        g_cuenta_name = st.selectbox("Cuenta / Tarjeta Origen", list(cuenta_options.keys()))
                        g_cuenta_id = cuenta_options[g_cuenta_name]

                st.markdown("---")
                st.markdown("#### **Comprobantes SAT (Obligatorio para Facturado)**")
                
                col_file1, col_file2 = st.columns(2)
                with col_file1:
                    uploaded_xml = st.file_uploader("Cargar XML de la Factura (CFDI)", type=["xml"], key="manual_xml")
                with col_file2:
                    uploaded_pdf = st.file_uploader("Cargar PDF de la Factura", type=["pdf"], key="manual_pdf")

                # Lógica de Validación de XML/PDF al presionar procesar en el formulario
                xml_rfc = None
                xml_uuid = None
                xml_total = None
                xml_file_saved = None
                pdf_file_saved = None
                
                # Procesar XML si se cargó
                if uploaded_xml:
                    xml_data = uploaded_xml.read()
                    parsed_res = parse_cfdi_xml(xml_data)
                    if parsed_res['success']:
                        xml_rfc = parsed_res['rfc_proveedor']
                        xml_uuid = parsed_res['uuid']
                        xml_total = parsed_res['total']
                        
                        # Guardar archivo físico simulado
                        xml_file_saved = f"xml_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_xml.name}"
                        with open(os.path.join(COMPROBANTES_DIR, xml_file_saved), "wb") as f:
                            f.write(xml_data)
                    else:
                        st.error(parsed_res['error'])
                
                if uploaded_pdf:
                    pdf_data = uploaded_pdf.read()
                    pdf_file_saved = f"pdf_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_pdf.name}"
                    with open(os.path.join(COMPROBANTES_DIR, pdf_file_saved), "wb") as f:
                        f.write(pdf_data)

                # Campos ocultos o informativos para mostrar validación de XML
                if xml_uuid:
                    st.info(f"📁 **Información Extraída del XML:**\n- RFC Proveedor: `{xml_rfc}`\n- Folio Fiscal (UUID): `{xml_uuid}`\n- Total XML: `${xml_total:,.2f}`")
                    
                    # Validar Monto
                    if abs(xml_total - g_monto) > 0.05:
                        st.warning(f"⚠️ El monto ingresado (${g_monto:,.2f}) no coincide con el total del XML (${xml_total:,.2f}).")
                    else:
                        st.success("✅ Validación Exitosa: El monto coincide con el archivo XML.")

                btn_submit = st.form_submit_button("Guardar Gasto")
                
                if btn_submit:
                    # Validaciones de negocio
                    if g_estado_fact == "Facturado" and (not xml_uuid or not uploaded_pdf):
                        st.error("❌ Regla Fiscal: Si el estado es 'Facturado', debe adjuntar XML (válido) y PDF.")
                    elif not g_cuenta_id:
                        st.error("❌ Debe seleccionar una cuenta válida.")
                    else:
                        fecha_str = g_fecha.strftime('%Y-%m-%d')
                        success, insert_id = db.add_gasto(
                            fecha=fecha_str,
                            concepto=g_concepto,
                            monto_neto=g_monto,
                            rubro=g_rubro,
                            proyecto_id=g_proy_id,
                            deducible=g_deducible,
                            estado_facturacion=g_estado_fact,
                            metodo_pago=g_metodo,
                            cuenta_id=g_cuenta_id,
                            rfc_proveedor=xml_rfc,
                            uuid_fiscal=xml_uuid,
                            xml_filename=xml_file_saved,
                            pdf_filename=pdf_file_saved
                        )
                        if success:
                            st.success(f"🎉 Gasto registrado exitosamente con Folio Interno: {insert_id}")
                            st.session_state['expense_submitted'] = True
                            st.rerun()
                        else:
                            st.error(f"Error al guardar: {insert_id}")

            # Mostrar tabla de gastos recientes y opción para eliminar
            st.markdown("---")
            st.markdown("#### **Gastos Recientes**")
            df_g = db.get_gastos_df()
            if not df_g.empty:
                df_g_disp = df_g.copy()
                df_g_disp['monto_neto'] = df_g_disp['monto_neto'].map('${:,.2f}'.format)
                
                # Columnas resumidas
                cols_to_show = [
                    'id', 'fecha', 'concepto', 'monto_neto', 'rubro', 
                    'proyecto_nombre', 'deducible', 'estado_facturacion', 
                    'metodo_pago', 'cuenta_nombre', 'rfc_proveedor', 'uuid_fiscal'
                ]
                st.dataframe(df_g_disp[cols_to_show].rename(columns={
                    'id': 'Folio', 'fecha': 'Fecha', 'concepto': 'Concepto', 
                    'monto_neto': 'Monto Neto', 'rubro': 'Rubro', 
                    'proyecto_nombre': 'Proyecto', 'deducible': 'Deducible', 
                    'estado_facturacion': 'Estatus Fact.', 'metodo_pago': 'Método Pago', 
                    'cuenta_nombre': 'Cuenta', 'rfc_proveedor': 'RFC Proveedor', 
                    'uuid_fiscal': 'UUID'
                }), use_container_width=True, hide_index=True)
                
                # Opción para borrar
                with st.expander("🗑️ Eliminar un registro de gasto"):
                    delete_id = st.number_input("Ingrese el Folio del gasto a eliminar:", min_value=1, step=1)
                    if st.button("Confirmar Eliminación"):
                        del_ok, del_msg = db.delete_gasto(delete_id)
                        if del_ok:
                            st.success(del_msg)
                            st.rerun()
                        else:
                            st.error(del_msg)
            else:
                st.info("No hay gastos registrados.")

    # --- SUBTAB: BACKORDER ---
    with tab_backorder:
        st.subheader("Backorder de Órdenes de Compra (OC)")
        st.markdown("Monitoree los compromisos futuros de pago a proveedores contratados.")
        
        col_b_list, col_b_form = st.columns([2, 1])
        
        with col_b_form:
            st.markdown("#### **Registrar OC en Backorder**")
            b_oc = st.text_input("Número de OC", placeholder="Ej. OC-2026-045")
            b_prov = st.text_input("Proveedor", placeholder="Ej. FESTO Pneumatic S.A.")
            b_fecha = st.date_input("Fecha Compromiso de Pago", datetime.date.today() + datetime.timedelta(days=15))
            b_monto = st.number_input("Monto OC (IVA Incluido)", min_value=0.0, step=100.0, format="%.2f")
            
            df_p_activos = db.get_proyectos(only_active=True)
            if not df_p_activos.empty:
                b_proy_opts = dict(zip(df_p_activos['nombre'], df_p_activos['id']))
                b_proy_name = st.selectbox("Proyecto Destino", list(b_proy_opts.keys()), key="backorder_proy")
                b_proy_id = b_proy_opts[b_proy_name]
            else:
                st.error("Registre un proyecto activo antes de ingresar órdenes de compra.")
                b_proy_id = None
                
            b_estado = st.selectbox("Estado inicial", ["Pendiente", "Pagado"])
            
            if st.button("Guardar OC"):
                if b_oc and b_prov and b_proy_id:
                    success, msg = db.add_backorder(
                        numero_oc=b_oc,
                        proveedor=b_prov,
                        fecha_compromiso=b_fecha.strftime('%Y-%m-%d'),
                        monto_oc=b_monto,
                        proyecto_id=b_proy_id,
                        estado=b_estado
                    )
                    if success:
                        st.success("Orden de compra registrada exitosamente.")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Complete todos los campos obligatorios.")
                    
        with col_b_list:
            st.markdown("#### **Órdenes de Compra en el Sistema**")
            df_b = db.get_backorders_df()
            if not df_b.empty:
                df_b_disp = df_b.copy()
                df_b_disp['monto_oc'] = df_b_disp['monto_oc'].map('${:,.2f}'.format)
                df_b_disp.columns = ['ID', 'Folio OC', 'Proveedor', 'Fecha Compromiso', 'Monto Neto', 'Proyecto', 'Proyecto ID', 'Estado de Pago']
                
                # Mostrar tabla
                st.dataframe(
                    df_b_disp[['Folio OC', 'Proveedor', 'Fecha Compromiso', 'Monto Neto', 'Proyecto', 'Estado de Pago']], 
                    use_container_width=True, 
                    hide_index=True
                )
                
                # Cambiar estado
                with st.expander("🔄 Cambiar Estado de Pago de OC"):
                    oc_select_opts = dict(zip(df_b['numero_oc'], df_b['id']))
                    selected_oc = st.selectbox("Seleccione Folio OC", list(oc_select_opts.keys()))
                    new_state = st.selectbox("Nuevo Estado", ["Pendiente", "Pagado"])
                    if st.button("Actualizar Estado"):
                        selected_id = oc_select_opts[selected_oc]
                        up_ok, up_msg = db.update_backorder_status(selected_id, new_state)
                        if up_ok:
                            st.success(up_msg)
                            st.rerun()
                        else:
                            st.error(up_msg)
            else:
                st.info("No hay órdenes de compra registradas.")

# --- MÓDULO 2: CARGA MASIVA (EXCEL) ---
elif menu == "📂 Carga Masiva (Excel)":
    render_header("Carga Masiva (Excel)", "Descargue la plantilla de validación y cargue los gastos diarios de forma transaccional.")
    
    col_d1, col_d2 = st.columns([1, 2])
    
    with col_d1:
        st.markdown("### **1. Descargar Plantilla**")
        st.markdown(
            "Esta plantilla autogenerada incluye listas desplegables validadas en base a sus Proyectos Activos y Rubros configurados."
        )
        
        try:
            excel_bytes = generate_excel_template()
            st.download_button(
                label="📥 Descargar Plantilla de Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"plantilla_gastos_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error al generar la plantilla: {str(e)}")
            
    with col_d2:
        st.markdown("### **2. Cargar Excel Completado**")
        st.markdown(
            "Suba el Excel del día. El sistema validará los campos y registrará todo de manera transaccional."
        )
        
        uploaded_excel = st.file_uploader("Arrastre o seleccione el archivo Excel (.xlsx)", type=["xlsx"])
        
        if uploaded_excel:
            st.info("Archivo cargado. Presione el botón a continuación para procesar la importación.")
            if st.button("🚀 Validar e Importar a Base de Datos"):
                result = import_excel_expenses(uploaded_excel.read())
                if result['success']:
                    st.success(f"🎉 ¡Importación exitosa! Se cargaron **{result['imported_count']}** registros de gastos a la base de datos.")
                else:
                    st.error("❌ Se encontraron errores de validación. No se importó ningún registro:")
                    for err in result['errors']:
                        st.markdown(f"- {err}")

# --- MÓDULO 3: DASHBOARDS INTERACTIVOS ---
elif menu == "📊 Dashboards Interactivos":
    render_header("Dashboards de Análisis Financiero", "Visualice reportes operativos y estratégicos de J&D Automation Industries.")
    
    # Cargar datos base
    df_gastos_base = db.get_gastos_df()
    df_backorder_base = db.get_backorders_df()
    df_proy_base = db.get_proyectos()
    
    # Barra de Filtros
    st.markdown("### **Filtros del Panel**")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    # Filtro de fecha
    if not df_gastos_base.empty:
        df_gastos_base['fecha_dt'] = pd.to_datetime(df_gastos_base['fecha'])
        min_date = df_gastos_base['fecha_dt'].min().date()
        max_date = df_gastos_base['fecha_dt'].max().date()
    else:
        min_date = datetime.date.today() - datetime.timedelta(days=30)
        max_date = datetime.date.today()
        
    with col_f1:
        date_range = st.date_input("Rango de Fechas", [min_date, max_date])
        
    with col_f2:
        proj_list = ["Todos"] + df_proy_base['nombre'].tolist()
        selected_proj = st.selectbox("Filtrar por Proyecto", proj_list)
        
    with col_f3:
        rubros_list = ['Materiales', 'Mano de obra', 'Supervisión', 'Gastos generales', 'Herramienta', 'Maquinaria']
        selected_rubros = st.multiselect("Filtrar por Rubro(s)", rubros_list, default=rubros_list)

    # Aplicar filtros a gastos
    df_g_filtered = df_gastos_base.copy()
    
    if len(date_range) == 2 and not df_g_filtered.empty:
        start_date, end_date = date_range
        df_g_filtered = df_g_filtered[
            (df_g_filtered['fecha_dt'].dt.date >= start_date) & 
            (df_g_filtered['fecha_dt'].dt.date <= end_date)
        ]
        
    if selected_proj != "Todos" and not df_g_filtered.empty:
        df_g_filtered = df_g_filtered[df_g_filtered['proyecto_nombre'] == selected_proj]
        
    if selected_rubros and not df_g_filtered.empty:
        df_g_filtered = df_g_filtered[df_g_filtered['rubro'].isin(selected_rubros)]
        
    # Aplicar filtros a backorder
    df_b_filtered = df_backorder_base.copy()
    if selected_proj != "Todos" and not df_b_filtered.empty:
        df_b_filtered = df_b_filtered[df_b_filtered['proyecto_nombre'] == selected_proj]

    # Tabs de Dashboards
    tab1, tab2, tab3 = st.tabs([
        "💸 Distribución de Gastos", 
        "⏳ Proyección Backorder OC", 
        "📈 Rentabilidad por Proyecto"
    ])
    
    with tab1:
        dash.render_gastos_dashboard(df_g_filtered)
        
    with tab2:
        dash.render_backorder_dashboard(df_b_filtered)
        
    with tab3:
        dash.render_proyectos_dashboard(df_proy_base, df_g_filtered)

# --- MÓDULO 4: EBITDA & REPORTES ---
elif menu == "💰 EBITDA & Reportes de Cuenta":
    render_header("EBITDA & Reportes de Cuenta", "Calcule el rendimiento operativo de la empresa y exporte reportes por método de pago.")
    
    df_gastos = db.get_gastos_df()
    df_proy = db.get_proyectos()
    
    tab_ebitda, tab_export = st.tabs(["📊 Cálculo de EBITDA", "📥 Exportar Reportes"])
    
    with tab_ebitda:
        st.subheader("Cálculo del EBITDA")
        st.markdown(
            "**Fórmula:** `[Ingresos de Proyectos] - [Gastos Operativos (excluyendo depreciación de maquinaria)]`"
        )
        
        # Ingresos totales contratados
        total_ingresos = df_proy['monto_ingreso'].sum()
        
        # Gastos operativos
        # Excluimos "Maquinaria" del cálculo de gastos operativos basándonos en la depreciación de maquinaria descrita
        df_gastos_op = df_gastos[df_gastos['rubro'] != 'Maquinaria']
        total_gastos_op = df_gastos_op['monto_neto'].sum()
        
        # Gastos excluidos
        df_gastos_excl = df_gastos[df_gastos['rubro'] == 'Maquinaria']
        total_gastos_excl = df_gastos_excl['monto_neto'].sum()
        
        ebitda = total_ingresos - total_gastos_op
        
        col_e1, col_e2, col_e3 = st.columns(3)
        col_e1.metric("Ingresos de Proyectos", f"${total_ingresos:,.2f} MXN")
        col_e2.metric("Gastos Operativos (excl. Maquinaria)", f"${total_gastos_op:,.2f} MXN")
        
        # Indicador de color para EBITDA positivo/negativo
        if ebitda >= 0:
            col_e3.metric("EBITDA Estimado", f"${ebitda:,.2f} MXN", "Operación Rentable", delta_color="normal")
        else:
            col_e3.metric("EBITDA Estimado", f"${ebitda:,.2f} MXN", "Operación con Pérdida", delta_color="inverse")
            
        st.markdown("---")
        
        # Desglose de Gastos Operativos vs Excluidos
        st.markdown("### **Desglose para EBITDA**")
        
        col_des1, col_des2 = st.columns(2)
        
        with col_des1:
            st.markdown("**Gastos Considerados (Operativos):**")
            if not df_gastos_op.empty:
                df_op_grouped = df_gastos_op.groupby('rubro')['monto_neto'].sum().reset_index()
                df_op_grouped['monto_neto'] = df_op_grouped['monto_neto'].map('${:,.2f}'.format)
                df_op_grouped.columns = ['Rubro Operativo', 'Monto Acumulado']
                st.dataframe(df_op_grouped, use_container_width=True, hide_index=True)
            else:
                st.info("No hay gastos operativos registrados.")
                
        with col_des2:
            st.markdown("**Gastos Excluidos (Maquinaria/Activos Fijos):**")
            if not df_gastos_excl.empty:
                df_ex_grouped = df_gastos_excl.groupby('rubro')['monto_neto'].sum().reset_index()
                df_ex_grouped['monto_neto'] = df_ex_grouped['monto_neto'].map('${:,.2f}'.format)
                df_ex_grouped.columns = ['Rubro Excluido', 'Monto Acumulado']
                st.dataframe(df_ex_grouped, use_container_width=True, hide_index=True)
            else:
                st.info("No hay gastos de Maquinaria registrados (exclusión de 0.00 MXN).")

    with tab_export:
        st.subheader("Reportes Específicos por Tipo de Movimiento")
        st.markdown("Consulte los listados segmentados de egresos y descárguelos en formato CSV.")
        
        tab_cc, tab_trans, tab_cash = st.tabs([
            "💳 Movimientos Tarjeta de Crédito", 
            "🏦 Transferencias Bancarias", 
            "💵 Movimientos en Efectivo"
        ])
        
        # Función auxiliar para renderizar y habilitar descarga
        def render_export_section(df_subset, filename_prefix):
            if df_subset.empty:
                st.info("No hay movimientos registrados para esta categoría.")
                return
                
            # Columnas limpias para mostrar y exportar
            cols_clean = [
                'fecha', 'concepto', 'monto_neto', 'rubro', 
                'proyecto_nombre', 'deducible', 'estado_facturacion', 
                'cuenta_nombre', 'rfc_proveedor', 'uuid_fiscal'
            ]
            df_disp = df_subset[cols_clean].rename(columns={
                'fecha': 'Fecha', 'concepto': 'Concepto', 
                'monto_neto': 'Monto Neto', 'rubro': 'Rubro', 
                'proyecto_nombre': 'Proyecto', 'deducible': 'Deducible', 
                'estado_facturacion': 'Estatus Fact.', 'cuenta_nombre': 'Cuenta/Tarjeta', 
                'rfc_proveedor': 'RFC Proveedor', 'uuid_fiscal': 'UUID'
            })
            
            # Mostrar datos formateados
            df_formatted = df_disp.copy()
            df_formatted['Monto Neto'] = df_formatted['Monto Neto'].map('${:,.2f}'.format)
            st.dataframe(df_formatted, use_container_width=True, hide_index=True)
            
            # Convertir a CSV para botón de descarga
            csv_buffer = io.StringIO()
            df_disp.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            
            st.download_button(
                label=f"📥 Descargar Reporte CSV ({filename_prefix})",
                data=csv_buffer.getvalue(),
                file_name=f"{filename_prefix}_{datetime.date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        with tab_cc:
            df_cc = df_gastos[df_gastos['metodo_pago'] == 'Tarjeta de Crédito']
            render_export_section(df_cc, "tarjeta_credito")
            
        with tab_trans:
            df_trans = df_gastos[df_gastos['metodo_pago'] == 'Transferencia Bancaria']
            render_export_section(df_trans, "transferencias_bancarias")
            
        with tab_cash:
            df_cash = df_gastos[df_gastos['metodo_pago'] == 'Efectivo']
            render_export_section(df_cash, "movimientos_efectivo")
