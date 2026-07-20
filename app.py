import streamlit as st
import pandas as pd
import datetime
import os
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

    /* Botones primarios en UT Orange (#FE8C29) */
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

# Importación de módulos internos y de autenticación
import database as db
from modules.xml_parser import parse_cfdi_xml
from modules.excel_handler import CLASIFICACIONES, generate_excel_template, import_excel_expenses
import modules.dashboards as dash
import modules.auth as auth
import modules.pdf_generator as pdf_gen
import modules.proyectos_dash as proy_dash
import modules.industria40 as i40
import modules.manual as man
import modules.mantenimiento as maint

# Control de Autenticación
auth.requiere_auth()

# Crear directorio para almacenar comprobantes físicos
COMPROBANTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'comprobantes')
os.makedirs(COMPROBANTES_DIR, exist_ok=True)

# Inicializar sesión de Streamlit para controlar recargas y PDFs
if 'expense_submitted' not in st.session_state:
    st.session_state['expense_submitted'] = False

# --- BARRA LATERAL / NAVEGACIÓN ---
st.sidebar.image("brand/logo_blanco.png", use_container_width=True)
st.sidebar.markdown("<h3 style='color: #FFFFFF; text-align: center; margin-top:0; font-family:\"Montserrat\"; font-size: 16px;'>Control Financiero</h3>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Renderizar información de usuario
auth.render_sidebar_usuario()
st.sidebar.markdown("---")

# Menú principal numerado con sub-secciones explicativas
menu_options = [
    "1. 🏠 Inicio & Registro",
    "2. 📂 Carga Masiva (Excel)",
    "3. 📊 Dashboards Interactivos",
    "4. 💰 EBITDA & Reportes de Cuenta",
    "5. 📁 Proyectos — Estado & Pareto",
    "6. 🤖 Industria 4.0",
    "7. 📖 Manual de Operación del Sistema"
]

if auth.es_admin():
    menu_options.append("8. ⚙️ Mantenimiento del Sistema")

menu = st.sidebar.radio("Navegación del Sistema", menu_options)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Regla Fiscal Homologada:** Todos los montos se ingresan como **MONTO NETO CON IVA INCLUIDO**."
)

# ─── MÓDULO 1: INICIO Y REGISTRO ─────────────────────────────────────────────
if menu.startswith("1."):
    render_header("Control de Registro", "Gestione proyectos, cuentas y capture los gastos de la operación diaria.")
    
    tab_proyectos, tab_cuentas, tab_gastos, tab_backorder = st.tabs([
        "📁 1.1 Proyectos", 
        "💳 1.2 Cuentas & Tarjetas", 
        "💵 1.3 Captura de Gasto", 
        "📝 1.4 Órdenes de Compra (Backorder)"
    ])
    
    # --- SUBTAB 1.1: PROYECTOS ---
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
                
    # --- SUBTAB 1.2: CUENTAS ---
    with tab_cuentas:
        st.subheader("Administración de Cuentas y Tarjetas")
        col_list_c, col_form_c = st.columns([2, 1])
        
        with col_form_c:
            st.markdown("#### **Registrar Cuenta / Tarjeta**")
            c_nombre = st.text_input("Nombre / Identificador de Cuenta", placeholder="Ej. Banorte Operativa *4492")
            c_tipo = st.selectbox("Método de Pago Asociado", ["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"])
            
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
                    
        with col_list_c:
            st.markdown("#### **Cuentas y Tarjetas Registradas**")
            df_c = db.get_cuentas()
            if not df_c.empty:
                df_c_disp = df_c.copy()
                df_c_disp.columns = ['ID', 'Identificador de Cuenta', 'Método de Pago Asociado']
                st.dataframe(df_c_disp, use_container_width=True, hide_index=True)
            else:
                st.info("No hay cuentas registradas.")
                
    # --- SUBTAB 1.3: CAPTURA DE GASTO (CON RESPALDO PDF AUTOMÁTICO) ---
    with tab_gastos:
        st.subheader("Captura Individual de Gastos Diarios")
        
        df_p_activos = db.get_proyectos(only_active=True)
        df_c_all = db.get_cuentas()
        
        if df_p_activos.empty:
            st.warning("⚠️ Para capturar gastos, primero debe registrar al menos un **Proyecto Activo**.")
        elif df_c_all.empty:
            st.warning("⚠️ Para capturar gastos, primero debe registrar al menos una **Cuenta/Tarjeta**.")
        else:
            # Si hay un PDF generado en la transacción anterior, mostrar botón de descarga prominente
            if st.session_state.get('gasto_guardado_exito', False):
                st.success("🎉 **¡Registro Exitoso!** El gasto se ha guardado en la base de datos.")
                
                # Botón para descargar el PDF generado como respaldo obligatorio
                st.download_button(
                    label="📥 Descargar Respaldo PDF del Registro (Obligatorio)",
                    data=st.session_state['last_pdf_bytes'],
                    file_name=st.session_state['last_pdf_name'],
                    mime="application/pdf",
                    use_container_width=True
                )
                
                if st.button("Capturar Otro Gasto"):
                    st.session_state['gasto_guardado_exito'] = False
                    st.session_state['last_pdf_bytes'] = None
                    st.session_state['last_pdf_name'] = None
                    st.rerun()
            else:
                with st.form("manual_expense_form"):
                    col_g1, col_g2 = st.columns(2)
                    
                    with col_g1:
                        g_fecha = st.date_input("Fecha de Gasto", datetime.date.today())
                        g_concepto = st.text_input("Concepto del Gasto", placeholder="Ej. Compra de relevadores y cableado")
                        g_monto = st.number_input("Monto Neto (IVA Incluido)", min_value=0.01, step=50.0, format="%.2f")
                        
                        # --- CLASIFICACIONES DE 3 NIVELES OPCIONALES (allow_blank) ---
                        rubros_lista = ["— Dejar en blanco —"] + list(CLASIFICACIONES.keys())
                        g_rubro_raw = st.selectbox("Rubro Principal (Opcional)", rubros_lista)
                        
                        if g_rubro_raw != "— Dejar en blanco —":
                            g_rubro = g_rubro_raw
                            subrubros_lista = ["— Dejar en blanco —"] + list(CLASIFICACIONES[g_rubro].keys())
                            g_subrubro_raw = st.selectbox("Subrubro (Opcional)", subrubros_lista)
                            
                            if g_subrubro_raw != "— Dejar en blanco —":
                                g_subrubro = g_subrubro_raw
                                conceptos_lista = ["— Dejar en blanco —"] + CLASIFICACIONES[g_rubro][g_subrubro]
                                g_concepto_det_raw = st.selectbox("Concepto Detallado (Opcional)", conceptos_lista)
                                g_concepto_detallado = g_concepto_det_raw if g_concepto_det_raw != "— Dejar en blanco —" else None
                            else:
                                g_subrubro = None
                                g_concepto_detallado = None
                        else:
                            g_rubro = None
                            g_subrubro = None
                            g_concepto_detallado = None
                            
                        proyecto_options = dict(zip(df_p_activos['nombre'], df_p_activos['id']))
                        g_proy_name = st.selectbox("Proyecto Asociado", list(proyecto_options.keys()))
                        g_proy_id = proyecto_options[g_proy_name]
                        
                    with col_g2:
                        g_deducible = st.selectbox("¿Deducible / Facturable?", ["Sí", "No"])
                        g_estado_fact = st.selectbox("Estatus de Facturación", ["Pendiente", "Facturado"])
                        g_metodo = st.selectbox("Método de Pago", ["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"])
                        
                        df_c_filtradas = df_c_all[df_c_all['tipo'] == g_metodo]
                        if df_c_filtradas.empty:
                            st.error(f"No hay cuentas de tipo: {g_metodo}. Regístrelas en Cuentas & Tarjetas.")
                            g_cuenta_id = None
                            g_cuenta_name = "—"
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

                    xml_rfc = None
                    xml_uuid = None
                    xml_total = None
                    xml_file_saved = None
                    pdf_file_saved = None
                    
                    if uploaded_xml:
                        xml_data = uploaded_xml.read()
                        parsed_res = parse_cfdi_xml(xml_data)
                        if parsed_res['success']:
                            xml_rfc = parsed_res['rfc_proveedor']
                            xml_uuid = parsed_res['uuid']
                            xml_total = parsed_res['total']
                            
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

                    if xml_uuid:
                        st.info(f"📁 **Información Extraída del XML:**\n- RFC: `{xml_rfc}`\n- UUID: `{xml_uuid}`\n- Total XML: `${xml_total:,.2f}`")
                        if abs(xml_total - g_monto) > 0.05:
                            st.warning(f"⚠️ El monto ingresado (${g_monto:,.2f}) difiere del total del XML (${xml_total:,.2f}).")
                        else:
                            st.success("✅ Validación Exitosa: El monto coincide con el archivo XML.")

                    btn_submit = st.form_submit_button("Guardar Gasto")
                    
                    if btn_submit:
                        if g_estado_fact == "Facturado" and (not xml_uuid or not uploaded_pdf):
                            st.error("❌ Regla Fiscal: Si el estado es 'Facturado', debe adjuntar XML (válido) y PDF.")
                        elif not g_cuenta_id:
                            st.error("❌ Debe seleccionar una cuenta origen válida.")
                        else:
                            fecha_str = g_fecha.strftime('%Y-%m-%d')
                            success, insert_id = db.add_gasto(
                                fecha=fecha_str,
                                concepto=g_concepto,
                                monto_neto=g_monto,
                                rubro=g_rubro,
                                subrubro=g_subrubro,
                                concepto_detallado=g_concepto_detallado,
                                proyecto_id=g_proy_id,
                                deducible=g_deducible,
                                estado_facturacion=g_estado_fact,
                                metodo_pago=g_metodo,
                                cuenta_id=g_cuenta_id,
                                rfc_proveedor=xml_rfc,
                                uuid_fiscal=xml_uuid,
                                xml_filename=xml_file_saved,
                                pdf_filename=None # Se actualizará con el PDF de respaldo generado a continuación
                            )
                            
                            if success:
                                # --- GENERACIÓN DEL PDF DE RESPALDO (OBLIGATORIO) ---
                                gasto_pdf_info = {
                                    'id': insert_id,
                                    'fecha': fecha_str,
                                    'concepto': g_concepto,
                                    'monto_neto': g_monto,
                                    'proyecto_nombre': g_proy_name,
                                    'metodo_pago': g_metodo,
                                    'cuenta_nombre': g_cuenta_name,
                                    'rubro': g_rubro,
                                    'subrubro': g_subrubro,
                                    'concepto_detallado': g_concepto_detallado,
                                    'deducible': g_deducible,
                                    'estado_facturacion': g_estado_fact,
                                    'rfc_proveedor': xml_rfc,
                                    'uuid_fiscal': xml_uuid
                                }
                                
                                # Generar recibo PDF
                                pdf_bytes = pdf_gen.generar_pdf_gasto(gasto_pdf_info)
                                local_pdf_name = f"recibo_gasto_{insert_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                                
                                # Guardar PDF de respaldo físico en el servidor
                                with open(os.path.join(COMPROBANTES_DIR, local_pdf_name), "wb") as f:
                                    f.write(pdf_bytes)
                                    
                                # Asociar el archivo PDF de respaldo en la base de datos
                                db.update_gasto(insert_id, pdf_filename=local_pdf_name)
                                
                                # Almacenar en sesión para descarga instantánea
                                st.session_state['last_pdf_bytes'] = pdf_bytes
                                st.session_state['last_pdf_name'] = local_pdf_name
                                st.session_state['gasto_guardado_exito'] = True
                                st.rerun()
                            else:
                                st.error(f"Error al guardar gasto: {insert_id}")
                                
            # Tabla de gastos recientes (solo lectura rápida, eliminación bloqueada para no administradores)
            st.markdown("---")
            st.markdown("#### **Gastos Recientes**")
            df_g = db.get_gastos_df()
            if not df_g.empty:
                df_g_disp = df_g.copy()
                df_g_disp['monto_neto'] = df_g_disp['monto_neto'].map('${:,.2f}'.format)
                
                cols_to_show = [
                    'id', 'fecha', 'concepto', 'monto_neto', 'rubro', 'subrubro', 'concepto_detallado',
                    'proyecto_nombre', 'deducible', 'estado_facturacion', 
                    'metodo_pago', 'cuenta_nombre', 'rfc_proveedor', 'uuid_fiscal'
                ]
                st.dataframe(df_g_disp[cols_to_show].rename(columns={
                    'id': 'Folio', 'fecha': 'Fecha', 'concepto': 'Concepto Gral', 
                    'monto_neto': 'Monto Neto', 'rubro': 'Rubro Principal', 
                    'subrubro': 'Subrubro', 'concepto_detallado': 'Concepto Detallado',
                    'proyecto_nombre': 'Proyecto', 'deducible': 'Deducible', 
                    'estado_facturacion': 'Estatus Fact.', 'metodo_pago': 'Método Pago', 
                    'cuenta_nombre': 'Cuenta/Tarjeta', 'rfc_proveedor': 'RFC Proveedor', 
                    'uuid_fiscal': 'UUID'
                }), use_container_width=True, hide_index=True)
            else:
                st.info("No hay gastos registrados.")

    # --- SUBTAB 1.4: ORDENES DE COMPRA ---
    with tab_backorder:
        st.subheader("Control del Backorder de Órdenes de Compra (OC)")
        col_list_b, col_form_b = st.columns([2, 1])
        
        with col_form_b:
            st.markdown("#### **Registrar OC en Backorder**")
            oc_num = st.text_input("Número / Folio de OC", placeholder="Ej. OC-2026-042")
            oc_prov = st.text_input("Proveedor", placeholder="Ej. Festo Pneumatic")
            oc_fecha = st.date_input("Fecha Compromiso de Pago", datetime.date.today())
            oc_monto = st.number_input("Monto de la OC (IVA Incluido)", min_value=0.0, step=100.0, format="%.2f")
            
            # Asociar a proyecto
            proyecto_options_b = dict(zip(df_p_activos['nombre'], df_p_activos['id']))
            oc_proy_name = st.selectbox("Proyecto Destino", list(proyecto_options_b.keys()), key="oc_proy_sel")
            oc_proy_id = proyecto_options_b[oc_proy_name]
            
            if st.button("Guardar OC"):
                if oc_num and oc_prov:
                    success, msg = db.add_backorder(
                        numero_oc=oc_num,
                        proveedor=oc_prov,
                        fecha_compromiso=oc_fecha.strftime('%Y-%m-%d'),
                        monto_oc=oc_monto,
                        proyecto_id=oc_proy_id
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("El número de OC y el proveedor son requeridos.")
                    
        with col_list_b:
            st.markdown("#### **Órdenes de Compra Registradas**")
            df_b = db.get_backorders_df()
            if not df_b.empty:
                df_b_disp = df_b.copy()
                df_b_disp['monto_oc'] = df_b_disp['monto_oc'].map('${:,.2f}'.format)
                df_b_disp.columns = ['ID', 'Folio OC', 'Proveedor', 'Fecha Compromiso', 'Monto OC', 'Proyecto Destino', 'ID Proyecto', 'Estado de Pago']
                st.dataframe(df_b_disp.drop(columns=['ID Proyecto']), use_container_width=True, hide_index=True)
                
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

# ─── MÓDULO 2: CARGA MASIVA ──────────────────────────────────────────────────
elif menu.startswith("2."):
    render_header("Carga Masiva (Excel)", "Descargue la plantilla de validación y cargue los gastos diarios de forma transaccional.")
    
    col_d1, col_d2 = st.columns([1, 2])
    
    with col_d1:
        st.markdown("### **2.1 Descargar Plantilla**")
        st.markdown(
            "Esta plantilla incluye listas de validación dinámicas vinculadas a sus Proyectos Activos y Clasificaciones configuradas."
        )
        
        try:
            excel_bytes = generate_excel_template()
            st.download_button(
                label="📥 Descargar Plantilla Excel (.xlsx)",
                data=excel_bytes,
                file_name="Plantilla_Gastos_JD_Automation.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success("¡Plantilla autogenerada con éxito!")
        except Exception as e:
            st.error(f"Error al generar la plantilla: {str(e)}")
            
    with col_d2:
        st.markdown("### **2.2 Importar Gastos**")
        st.markdown("Suba el archivo Excel lleno para validar e importar múltiples registros.")
        
        uploaded_excel = st.file_uploader("Subir Archivo Excel", type=["xlsx", "xls"])
        
        if uploaded_excel:
            file_bytes = uploaded_excel.read()
            if st.button("Procesar e Importar Archivo"):
                with st.spinner("Validando transacciones e importando a la base de datos..."):
                    result = import_excel_expenses(file_bytes)
                
                if result['success']:
                    st.success(f"🎉 ¡Importación exitosa! Se cargaron **{result['imported_count']}** registros de gastos a la base de datos.")
                else:
                    st.error("❌ Se encontraron errores de validación. No se importó ningún registro:")
                    for err in result['errors']:
                        st.markdown(f"- {err}")

# ─── MÓDULO 3: DASHBOARDS INTERACTIVOS ───────────────────────────────────────
elif menu.startswith("3."):
    render_header("Dashboards de Análisis Financiero", "Visualice reportes operativos y estratégicos de J&D Automation Industries.")
    
    df_gastos_base = db.get_gastos_df()
    df_backorder_base = db.get_backorders_df()
    df_proy_base = db.get_proyectos()
    
    st.markdown("### **Filtros del Panel**")
    col_f1, col_f2, col_f3 = st.columns(3)
    
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
        proj_sel = st.selectbox("Proyecto", proj_list)
        
    with col_f3:
        deduc_sel = st.selectbox("Deducibilidad Fiscal", ["Todos", "Sí", "No"])

    # Aplicar filtros
    df_g_filtered = df_gastos_base.copy()
    df_b_filtered = df_backorder_base.copy()
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        if not df_g_filtered.empty:
            df_g_filtered = df_g_filtered[(df_g_filtered['fecha_dt'].date >= start_date) & (df_g_filtered['fecha_dt'].date <= end_date)]
        if not df_b_filtered.empty:
            df_b_filtered['fecha_dt'] = pd.to_datetime(df_b_filtered['fecha_compromiso'])
            df_b_filtered = df_b_filtered[(df_b_filtered['fecha_dt'].date >= start_date) & (df_b_filtered['fecha_dt'].date <= end_date)]
            
    if proj_sel != "Todos":
        df_g_filtered = df_g_filtered[df_g_filtered['proyecto_nombre'] == proj_sel]
        df_b_filtered = df_b_filtered[df_b_filtered['proyecto_nombre'] == proj_sel]
        
    if deduc_sel != "Todos":
        df_g_filtered = df_g_filtered[df_g_filtered['deducible'] == deduc_sel]

    tab1, tab2, tab3 = st.tabs(["📊 3.1 Gastos Operativos", "📝 3.2 Backorder de OC", "📁 3.3 Rentabilidad de Proyectos"])
    
    with tab1:
        dash.render_gastos_dashboard(df_g_filtered)
        
    with tab2:
        dash.render_backorder_dashboard(df_b_filtered)
        
    with tab3:
        dash.render_proyectos_dashboard(df_proy_base, df_g_filtered)

# ─── MÓDULO 4: EBITDA & REPORTES ─────────────────────────────────────────────
elif menu.startswith("4."):
    render_header("EBITDA & Reportes de Cuenta", "Calcule el rendimiento operativo de la empresa y exporte reportes por método de pago.")
    
    df_gastos = db.get_gastos_df()
    df_proy = db.get_proyectos()
    
    tab_ebitda, tab_export = st.tabs(["📊 4.1 Cálculo de EBITDA", "📥 4.2 Exportar Reportes"])
    
    with tab_ebitda:
        st.subheader("Cálculo del EBITDA")
        st.markdown(
            "**Fórmula:** `[Ingresos de Proyectos] - [Gastos Operativos (excluyendo depreciación de maquinaria)]`"
        )
        
        total_ingresos = df_proy['monto_ingreso'].sum()
        
        # Excluimos "Equipo Mayor y Renta" (maquinaria) del cálculo de gastos operativos
        df_gastos_op = df_gastos[df_gastos['subrubro'] != 'Equipo Mayor y Renta']
        total_gastos_op = df_gastos_op['monto_neto'].sum()
        
        df_gastos_excl = df_gastos[df_gastos['subrubro'] == 'Equipo Mayor y Renta']
        total_gastos_excl = df_gastos_excl['monto_neto'].sum()
        
        ebitda = total_ingresos - total_gastos_op
        
        col_e1, col_e2, col_e3 = st.columns(3)
        col_e1.metric("Ingresos de Proyectos", f"${total_ingresos:,.2f} MXN")
        col_e2.metric("Gastos Operativos (excl. Renta Equipo)", f"${total_gastos_op:,.2f} MXN")
        
        if ebitda >= 0:
            col_e3.metric("EBITDA Estimado", f"${ebitda:,.2f} MXN", "Operación Rentable", delta_color="normal")
        else:
            col_e3.metric("EBITDA Estimado", f"${ebitda:,.2f} MXN", "Operación con Pérdida", delta_color="inverse")
            
        st.markdown("---")
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
            st.markdown("**Gastos Excluidos (Renta de Maquinaria/Equipo Mayor):**")
            if not df_gastos_excl.empty:
                df_ex_grouped = df_gastos_excl.groupby('subrubro')['monto_neto'].sum().reset_index()
                df_ex_grouped['monto_neto'] = df_ex_grouped['monto_neto'].map('${:,.2f}'.format)
                df_ex_grouped.columns = ['Subrubro Excluido', 'Monto Acumulado']
                st.dataframe(df_ex_grouped, use_container_width=True, hide_index=True)
            else:
                st.info("No hay gastos de Renta de Maquinaria registrados (exclusión de 0.00 MXN).")

    with tab_export:
        st.subheader("Reportes Específicos por Tipo de Movimiento")
        st.markdown("Consulte los listados segmentados de egresos y descárguelos en formato CSV y PDF.")
        
        tab_cc, tab_trans, tab_cash = st.tabs([
            "💳 Movimientos Tarjeta de Crédito", 
            "🏦 Transferencias Bancarias", 
            "💵 Movimientos en Efectivo"
        ])
        
        def render_export_section(df_subset, filename_prefix):
            if df_subset.empty:
                st.info("No hay movimientos registrados para esta categoría.")
                return
                
            cols_clean = [
                'fecha', 'concepto', 'monto_neto', 'rubro', 'subrubro', 'concepto_detallado',
                'proyecto_nombre', 'deducible', 'estado_facturacion', 
                'cuenta_nombre', 'rfc_proveedor', 'uuid_fiscal'
            ]
            df_disp = df_subset[cols_clean].rename(columns={
                'fecha': 'Fecha', 'concepto': 'Concepto Gral', 
                'monto_neto': 'Monto Neto', 'rubro': 'Rubro Principal', 
                'subrubro': 'Subrubro', 'concepto_detallado': 'Concepto Detallado',
                'proyecto_nombre': 'Proyecto', 'deducible': 'Deducible', 
                'estado_facturacion': 'Estatus Fact.', 'cuenta_nombre': 'Cuenta/Tarjeta', 
                'rfc_proveedor': 'RFC Proveedor', 'uuid_fiscal': 'UUID'
            })
            
            df_formatted = df_disp.copy()
            df_formatted['Monto Neto'] = df_formatted['Monto Neto'].map('${:,.2f}'.format)
            st.dataframe(df_formatted, use_container_width=True, hide_index=True)
            
            # Descargas en CSV y PDF
            col_down1, col_down2 = st.columns(2)
            with col_down1:
                csv_buffer = io.StringIO()
                df_disp.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label=f"📥 Descargar CSV ({filename_prefix})",
                    data=csv_buffer.getvalue(),
                    file_name=f"{filename_prefix}_{datetime.date.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_down2:
                try:
                    pdf_bytes = pdf_gen.generar_pdf_tabla(df_disp, f"Reporte de Movimientos - {filename_prefix.upper()}")
                    st.download_button(
                        label=f"📥 Descargar PDF ({filename_prefix})",
                        data=pdf_bytes,
                        file_name=f"reporte_{filename_prefix}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error al generar PDF: {str(e)}")
            
        with tab_cc:
            df_cc = df_gastos[df_gastos['metodo_pago'] == 'Tarjeta de Crédito']
            render_export_section(df_cc, "tarjeta_credito")
            
        with tab_trans:
            df_trans = df_gastos[df_gastos['metodo_pago'] == 'Transferencia Bancaria']
            render_export_section(df_trans, "transferencias_bancarias")
            
        with tab_cash:
            df_cash = df_gastos[df_gastos['metodo_pago'] == 'Efectivo']
            render_export_section(df_cash, "movimientos_efectivo")

# ─── MÓDULO 5: PROYECTOS — ESTADO & PARETO ───────────────────────────────────
elif menu.startswith("5."):
    render_header("Proyectos: Estado & Pareto de Costos", "Evalúe la salud financiera de sus proyectos y controle los conceptos de mayor costo.")
    
    df_gastos = db.get_gastos_df()
    df_proy = db.get_proyectos()
    
    tab_est, tab_pareto, tab_prog = st.tabs([
        "📊 5.1 Estado General por Proyecto",
        "📉 5.2 Pareto de Costos",
        "📈 5.3 Progreso vs Presupuesto"
    ])
    
    with tab_est:
        proy_dash.render_estado_proyectos(df_proy, df_gastos)
        
    with tab_pareto:
        if df_proy.empty:
            st.info("No hay proyectos registrados para analizar.")
        else:
            proy_options = {"Todos": "Todos"}
            proy_options.update(dict(zip(df_proy['nombre'], df_proy['id'])))
            
            selected_proj_name = st.selectbox("Seleccione Proyecto para el Pareto", list(proy_options.keys()))
            selected_proj_id = proy_options[selected_proj_name]
            
            proy_dash.render_pareto_proyecto(df_gastos, selected_proj_id, selected_proj_name)
            
    with tab_prog:
        proy_dash.render_progreso_presupuesto(df_proy, df_gastos)

# ─── MÓDULO 6: INDUSTRIA 4.0 ─────────────────────────────────────────────────
elif menu.startswith("6."):
    i40.render_industria40()

# ─── MÓDULO 7: MANUAL DE OPERACIÓN ───────────────────────────────────────────
elif menu.startswith("7."):
    man.render_manual()

# ─── MÓDULO 8: MANTENIMIENTO DEL SISTEMA ─────────────────────────────────────
elif menu.startswith("8."):
    auth.requiere_admin()
    maint.render_mantenimiento()
