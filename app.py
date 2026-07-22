import streamlit as st
import pandas as pd
import datetime
import os
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage

from PIL import Image
from streamlit_paste_button import paste_image_button

# Cargar ícono oficial de J&D
FAVICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brand', 'favicon_512.png')
favicon_img = Image.open(FAVICON_PATH) if os.path.exists(FAVICON_PATH) else "📊"

# Configuración de página (Debe ser el primer comando de Streamlit)
st.set_page_config(
    page_title="J&D Automation Industries - Control Financiero",
    page_icon=favicon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyectar meta tags HTML para ícono de accesos directos, marcadores y favoritos
if os.path.exists(FAVICON_PATH):
    import base64
    with open(FAVICON_PATH, "rb") as f:
        fav_b64 = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(f"""
    <head>
        <link rel="icon" type="image/png" href="data:image/png;base64,{fav_b64}">
        <link rel="shortcut icon" type="image/png" href="data:image/png;base64,{fav_b64}">
        <link rel="apple-touch-icon" href="data:image/png;base64,{fav_b64}">
    </head>
    """, unsafe_allow_html=True)

# Estilo CSS Personalizado para la Identidad Visual de J&D
st.markdown("""
<meta name="google" content="notranslate">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;900&display=swap');
    
    /* Ocultar el input auxiliar de pegado de portapapeles */
    div.element-container:has(input[placeholder="PASTE_IMAGE_PLACEHOLDER"]) {
        display: none !important;
    }
    
    /* ─── ESTILIZADO CORPORATIVO J&D PARA CARGA DE ARCHIVOS (FILE UPLOADER) ─── */
    section[data-testid="stFileUploaderDropzone"],
    div[data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #FE8C29 !important;
        border-radius: 10px !important;
        padding: 14px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
        transition: all 0.3s ease !important;
    }
    
    section[data-testid="stFileUploaderDropzone"]:hover,
    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #e0771b !important;
        background-color: #FFFDFB !important;
    }

    /* Botón corporativo J&D (#FE8C29) dentro del File Uploader */
    section[data-testid="stFileUploaderDropzone"] button, 
    div[data-testid="stFileUploaderDropzone"] button,
    [data-testid="stFileUploader"] button {
        background-color: #FE8C29 !important;
        font-size: 0 !important; /* Ocultar texto nativo duplicado */
        color: transparent !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 24px !important;
        box-shadow: 0 2px 5px rgba(254, 140, 41, 0.35) !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Ocultar absolutamente todos los elementos internos para evitar duplicaciones o encimado */
    section[data-testid="stFileUploaderDropzone"] button *, 
    div[data-testid="stFileUploaderDropzone"] button *,
    [data-testid="stFileUploader"] button * {
        display: none !important;
        visibility: hidden !important;
        font-size: 0 !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* Renderizar ÚNICAMENTE la etiqueta limpia "Cargar" */
    section[data-testid="stFileUploaderDropzone"] button::after, 
    div[data-testid="stFileUploaderDropzone"] button::after,
    [data-testid="stFileUploader"] button::after {
        content: "Cargar" !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        color: #FFFFFF !important;
        display: inline-block !important;
        visibility: visible !important;
        line-height: 1.4 !important;
    }
    
    section[data-testid="stFileUploaderDropzone"] button:hover, 
    div[data-testid="stFileUploaderDropzone"] button:hover,
    [data-testid="stFileUploader"] button:hover {
        background-color: #e0771b !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(254, 140, 41, 0.45) !important;
    }
    
    /* Instructivo de arrastrar y soltar traducido al español */
    [data-testid="stFileUploaderDropzoneInstructions"] {
        color: #434E62 !important;
        font-weight: 600 !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Aplicar tipografía Montserrat corporativa */
    html, body, .stWidget, .stMarkdown, p, li, label, input, button {
        font-family: 'Montserrat', 'Inter', sans-serif !important;
    }

    /* ─── ESTILOS CORPORATIVOS PARA SELECTBOX Y DESPLEGABLES (DROPDOWNS) ─── */
    [data-testid="stSelectbox"], 
    [data-testid="stMultiSelect"] {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Contenedor desplegable BaseWeb */
    [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        color: #434E62 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    [data-baseweb="select"] > div:hover {
        border-color: #FE8C29 !important;
    }

    /* Proteger íconos y SVGs en desplegables y expanders de corrupción tipográfica */
    [data-testid="stSelectbox"] svg,
    [data-testid="stMultiSelect"] svg,
    [data-baseweb="select"] svg,
    [data-baseweb="icon"],
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] svg {
        font-family: sans-serif !important;
        display: inline-block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    /* ─── ESTILOS CORPORATIVOS PARA ACCORDEONES Y EXPANDERS ─── */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        margin-bottom: 12px !important;
        overflow: hidden !important;
    }

    [data-testid="stExpander"] summary {
        background-color: #FAFAFA !important;
        color: #434E62 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        transition: background-color 0.2s ease, color 0.2s ease !important;
    }

    [data-testid="stExpander"] summary:hover {
        background-color: #FFF8F3 !important;
        color: #FE8C29 !important;
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
import modules.flujo_caja as flujo

def generar_eml_bytes(to_email, subject, body_text, attachment_bytes=None, attachment_name=None, body_html=None):
    """
    Genera un archivo .EML corporativo con diseño HTML institucional, logotipo de J&D Automation Industries y adjuntos.
    """
    msg = MIMEMultipart('related')
    msg['From'] = 'control.financiero@jd-automation.com'
    msg['To'] = to_email
    msg['Cc'] = 'david.alanis@jydautomation.com.mx, jesus.morales@jydautomation.com.mx, administracion@jydautomation.com.mx'
    msg['Subject'] = subject

    # Formatear HTML institucional si no se especificó un HTML completo
    if not body_html:
        lines = body_text.split('\n')
        formatted_content = ""
        in_list = False
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                if in_list:
                    formatted_content += '</ul>'
                    in_list = False
                continue
                
            if line_str.startswith("----------------") or line_str.startswith("================"):
                if in_list:
                    formatted_content += '</ul>'
                    in_list = False
                formatted_content += '<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 16px 0;"/>'
            elif line_str.isupper() and len(line_str) > 3:
                if in_list:
                    formatted_content += '</ul>'
                    in_list = False
                formatted_content += f'<h4 style="color: #434E62; margin: 20px 0 8px 0; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #FE8C29; padding-bottom: 4px;">{line_str}</h4>'
            elif line_str.startswith("* ") or line_str.startswith("• "):
                if not in_list:
                    formatted_content += '<ul style="margin: 8px 0 14px 0; padding-left: 20px;">'
                    in_list = True
                formatted_content += f'<li style="margin-bottom: 6px; color: #334155; font-size: 13.5px;">{line_str[2:].strip()}</li>'
            elif len(line_str) > 2 and line_str[0].isdigit() and (line_str[1:3] == ". " or line_str[2:4] == ". "):
                if in_list:
                    formatted_content += '</ul>'
                    in_list = False
                formatted_content += f'<p style="margin: 0 0 8px 0; color: #334155; font-size: 13.5px; font-weight: 500;">{line_str}</p>'
            else:
                if in_list:
                    formatted_content += '</ul>'
                    in_list = False
                formatted_content += f'<p style="margin: 0 0 10px 0; color: #334155; font-size: 13.5px; line-height: 1.5;">{line_str}</p>'
                
        if in_list:
            formatted_content += '</ul>'

        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, Helvetica, sans-serif; background-color: #F4F6F9; margin: 0; padding: 20px; color: #333333;">
            <div style="max-width: 650px; margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #DDE2E6;">
                <!-- Header con Logotipo Corporativo -->
                <div style="background-color: #434E62; padding: 22px 28px; border-bottom: 4px solid #FE8C29;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="vertical-align: middle;">
                                <img src="cid:logo_jd" alt="J&D Automation" style="max-height: 25px; width: auto; display: block;" />
                            </td>
                            <td style="text-align: right; vertical-align: middle;">
                                <span style="color: #FFFFFF; font-size: 15px; font-weight: 700; display: block;">J&D AUTOMATION INDUSTRIES</span>
                                <span style="color: #FE8C29; font-size: 12px; font-weight: 600; display: block; margin-top: 2px;">Control Financiero Inteligente</span>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <!-- Cuerpo Principal -->
                <div style="padding: 28px 30px;">
                    {formatted_content}
                </div>
                
                <!-- Pie de Página Corporativo -->
                <div style="background-color: #F8FAFC; padding: 18px 25px; text-align: center; font-size: 12px; color: #64748B; border-top: 1px solid #E2E8F0;">
                    <p style="margin: 0 0 4px 0; font-weight: 700; color: #434E62;">J&D AUTOMATION INDUSTRIES S.A. DE C.V.</p>
                    <p style="margin: 0 0 6px 0;">Calle P #352, Col. Eduardo Guerra, Torreón, Coah. México</p>
                    <p style="margin: 0;">
                        <a href="https://www.jydautomation.mx" style="color: #FE8C29; text-decoration: none; font-weight: 700;">www.jydautomation.mx</a> | 
                        <a href="mailto:contacto@jydautomation.mx" style="color: #FE8C29; text-decoration: none; font-weight: 700;">contacto@jydautomation.mx</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)

    msg_alt.attach(MIMEText(body_text, 'plain', 'utf-8'))
    msg_alt.attach(MIMEText(body_html, 'html', 'utf-8'))

    # Incrustar el Logotipo oficial (blanco) como CID inline — visible sobre fondo Charcoal
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brand', 'logo_blanco.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brand', 'logo_naranja.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_img = MIMEImage(f.read())
            logo_img.add_header('Content-ID', '<logo_jd>')
            logo_img.add_header('Content-Disposition', 'inline', filename='logo_jd.png')
            msg.attach(logo_img)

    # Adjuntar documento de soporte (PDF o Excel)
    if attachment_bytes and attachment_name:
        part = MIMEApplication(attachment_bytes, Name=attachment_name)
        part.add_header('Content-Disposition', 'attachment', filename=attachment_name)
        msg.attach(part)

    return msg.as_bytes()

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
st.sidebar.markdown("<h3 style='color: #FFFFFF; text-align: center; margin-top:0; font-family:\"Montserrat\"; font-size: 16px; margin-bottom: 5px;'>Control Financiero</h3>", unsafe_allow_html=True)
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 15px;">
    <a href="https://jydautomation.mx/" target="_blank" style="color: #FE8C29; text-decoration: none; font-family: 'Montserrat', sans-serif; font-size: 13px; font-weight: bold; border: 1px solid #FE8C29; padding: 4px 10px; border-radius: 4px; display: inline-block; transition: all 0.3s ease;">
        🌐 jydautomation.mx
    </a>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Renderizar información de usuario
auth.render_sidebar_usuario()
st.sidebar.markdown("---")

# Menú principal numerado con sub-secciones explicativas
menu_options = [
    "1. 💵 Gastos — Captura & Carga Masiva",
    "2. 📁 Proyectos — Gestión & Pareto",
    "3. 🗓️ Flujo de Caja Proyectado",
    "4. 📊 Dashboards Interactivos",
    "5. 💰 EBITDA & Reportes de Cuenta",
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

# ─── FUNCIONES AUXILIARES DE RENDERIZADO ──────────────────────────────────
def _render_gestion_proyectos():
    st.subheader("Alta & Gestión de Proyectos")
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
            df_p_disp.columns = ['ID', 'Código', 'Nombre', 'Descripción', 'Ingreso Contratado (Neto)', 'Estado']
            st.dataframe(df_p_disp, use_container_width=True, hide_index=True)
        else:
            st.info("No hay proyectos registrados.")

def _render_carga_masiva_excel():
    st.subheader("Carga Masiva de Gastos (Excel)")
    col_d1, col_d2 = st.columns([1, 2])
    
    with col_d1:
        st.markdown("### **Descargar Plantilla**")
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
        st.markdown("### **Importar Gastos**")
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

def _render_control_backorder():
    st.subheader("Control de Órdenes de Compra (OC)")
    df_p_activos = db.get_proyectos(only_active=True)
    if df_p_activos.empty:
        st.warning("⚠️ Debe tener al menos un proyecto activo para registrar órdenes de compra.")
        return
        
    col_list_b, col_form_b = st.columns([2, 1])
    
    with col_form_b:
        st.markdown("#### **Registrar Nueva Órden de Compra**")
        oc_num = st.text_input("Número / Folio de OC", placeholder="Ej. OC-2026-042")
        oc_prov = st.text_input("Proveedor", placeholder="Ej. Festo Pneumatic")
        oc_fecha = st.date_input("Fecha Compromiso de Pago", datetime.date.today())
        oc_monto = st.number_input("Monto de la OC (IVA Incluido)", min_value=0.0, step=100.0, format="%.2f")
        
        proyecto_options_b = dict(zip('[' + df_p_activos['codigo'] + '] ' + df_p_activos['nombre'], df_p_activos['id']))
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
            
            col_oc_act1, col_oc_act2 = st.columns(2)
            with col_oc_act1:
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
            with col_oc_act2:
                with st.expander("Descargar PDF y Correo .EML de Orden de Compra"):
                    oc_list = df_b.to_dict('records')
                    oc_dict_opts = {r['numero_oc']: r for r in oc_list}
                    sel_oc_num = st.selectbox("Seleccione Orden de Compra:", list(oc_dict_opts.keys()))
                    if sel_oc_num:
                        oc_data = oc_dict_opts[sel_oc_num]
                        pdf_oc_bytes = pdf_gen.generar_pdf_orden_compra(oc_data)
                        
                        st.download_button(
                            label=f"📥 Descargar PDF ({sel_oc_num})",
                            data=pdf_oc_bytes,
                            file_name=f"Orden_Compra_{sel_oc_num}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        st.markdown("---")
                        st.markdown("##### **📩 Generar Correo (.eml) con PDF Adjunto**")
                        df_users = db.get_usuarios_df()
                        emails_registrados = []
                        if not df_users.empty and 'email' in df_users.columns:
                            emails_registrados = df_users['email'].dropna().tolist()
                        
                        email_oc_destino = st.selectbox(
                            "Correo Destino:",
                            options=["david.alanis@jydautomation.com.mx", "jesus.morales@jydautomation.com.mx", "administracion@jydautomation.com.mx"] + emails_registrados,
                            key="oc_eml_dest_sel"
                        )
                        
                        asunto_oc_eml = f"Orden de Compra Folio #{sel_oc_num} — J&D Automation Industries"
                        
                        monto_oc_fmt = f"${float(oc_data.get('monto_oc', 0)):,.2f} MXN"
                        cuerpo_oc_eml = f"""Estimado(a),\n\nAdjunto a este correo encontrará el documento oficial de la ORDEN DE COMPRA enviada por J&D Automation Industries.\n\nDETALLES DE LA ORDEN DE COMPRA:\n------------------------------------------------------------\n* Folio de OC: {oc_data.get('numero_oc', 'N/A')}\n* Proveedor: {oc_data.get('proveedor', 'N/A')}\n* Proyecto Destino: {oc_data.get('proyecto_nombre', 'N/A')}\n* Fecha Compromiso de Pago: {oc_data.get('fecha_compromiso', 'N/A')}\n* Monto Total Neto (IVA Incluido): {monto_oc_fmt}\n* Estado de Pago: {oc_data.get('estado', 'Pendiente')}\n\nTÉRMINOS DE ENTREGA Y FACTURACIÓN:\n------------------------------------------------------------\n1. Entregar los bienes/servicios conforme a la fecha compromiso estipulada.\n2. Toda factura deberá emitirse a nombre de J&D Automation Industries con IVA desglosado.\n3. Indicar el folio {sel_oc_num} en la factura fiscal y remisiones correspondientes.\n\nPor favor revise el documento PDF adjunto como respaldo oficial.\n\nSaludos cordiales,\nDepartamento de Compras & Finanzas | J&D Automation Industries"""
                        
                        eml_oc_bytes = generar_eml_bytes(
                            to_email=email_oc_destino,
                            subject=asunto_oc_eml,
                            body_text=cuerpo_oc_eml,
                            attachment_bytes=pdf_oc_bytes,
                            attachment_name=f"Orden_Compra_{sel_oc_num}.pdf"
                        )
                        
                        st.download_button(
                            label="✉️ Descargar Archivo .EML (Para Outlook)",
                            data=eml_oc_bytes,
                            file_name=f"Correo_Orden_Compra_{sel_oc_num}.eml",
                            mime="message/rfc822",
                            use_container_width=True
                        )
        else:
            st.info("No hay órdenes de compra registradas.")

def _render_captura_individual_gasto():
    st.subheader("Captura Individual de Gastos Diarios")
    
    df_p_activos = db.get_proyectos(only_active=True)
    df_c_all = db.get_cuentas()
    
    if df_p_activos.empty:
        st.warning("⚠️ Para capturar gastos, primero debe registrar al menos un **Proyecto Activo**.")
    elif df_c_all.empty:
        st.warning("⚠️ Para capturar gastos, primero debe registrar al menos una **Cuenta/Tarjeta**.")
    else:
        if st.session_state.get('gasto_guardado_exito', False):
            st.success("🎉 **¡Registro Exitoso!** El gasto se ha guardado en la base de datos.")
            
            col_ok_1, col_ok_2 = st.columns(2)
            with col_ok_1:
                st.markdown("##### **📄 Descargar Respaldo Físico**")
                st.download_button(
                    label="📥 Descargar Respaldo PDF (Obligatorio)",
                    data=st.session_state['last_pdf_bytes'],
                    file_name=st.session_state['last_pdf_name'],
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
                if st.button("Capturar Otro Gasto", use_container_width=True):
                    st.session_state['gasto_guardado_exito'] = False
                    st.session_state['last_pdf_bytes'] = None
                    st.session_state['last_pdf_name'] = None
                    st.rerun()
            
            with col_ok_2:
                st.markdown("##### **📩 Enviar Notificación por Correo (.eml)**")
                df_users = db.get_usuarios_df()
                emails_registrados = []
                if not df_users.empty and 'email' in df_users.columns:
                    emails_registrados = df_users['email'].dropna().tolist()
                
                email_destino = st.selectbox(
                    "Seleccione Correo Destino:",
                    options=["david.alanis@jydautomation.com.mx", "jesus.morales@jydautomation.com.mx", "administracion@jydautomation.com.mx"] + emails_registrados
                )
                
                asunto_eml = f"Notificación de Gasto Registrado — Folio Interno J&D"
                cuerpo_eml = f"""Estimado(a),

Se ha registrado un nuevo gasto operativo en el Sistema de Control Financiero J&D Automation Industries.

Detalles del Registro:
----------------------------------------
* Respaldo PDF: Adjunto a este correo

Por favor revise el documento PDF adjunto como comprobante oficial del movimiento.

Saludos cordiales,
Sistema de Control Financiero | J&D Automation Industries"""
                
                eml_data = generar_eml_bytes(
                    to_email=email_destino,
                    subject=asunto_eml,
                    body_text=cuerpo_eml,
                    attachment_bytes=st.session_state['last_pdf_bytes'],
                    attachment_name=st.session_state['last_pdf_name']
                )
                
                st.download_button(
                    label="✉️ Descargar Archivo .EML (Para Outlook)",
                    data=eml_data,
                    file_name=f"notificacion_gasto_{st.session_state.get('last_pdf_name', 'recibo').replace('.pdf', '')}.eml",
                    mime="message/rfc822",
                    use_container_width=True
                )
        
        else:
            with st.form("form_captura_gasto", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### **1. Información Transaccional**")
                    fecha_g = st.date_input("Fecha de Gasto", datetime.date.today())
                    concepto_g = st.text_input("Concepto del Gasto", placeholder="Ej. Compra de relevadores y cableado")
                    monto_g = st.number_input("Monto Neto (IVA Incluido)", min_value=0.01, step=10.0, format="%.2f")
                    
                    st.markdown("##### **2. Jerarquía de Clasificación (Opcional)**")
                    clasifs_dict = db.get_clasificaciones_dict()
                    rubro_options = ["— Dejar en blanco —"] + list(clasifs_dict.keys())
                    rubro_sel = st.selectbox("Rubro Principal (Opcional)", rubro_options)
                    
                    if rubro_sel != "— Dejar en blanco —":
                        subrubros_dict = clasifs_dict.get(rubro_sel, {})
                        subrubro_options = ["— Dejar en blanco —"] + list(subrubros_dict.keys())
                        subrubro_sel = st.selectbox("Subrubro (Opcional)", subrubro_options)
                        
                        if subrubro_sel != "— Dejar en blanco —":
                            conceptos_list = subrubros_dict.get(subrubro_sel, [])
                            concepto_det_options = ["— Dejar en blanco —"] + conceptos_list
                            concepto_det_sel = st.selectbox("Concepto Detallado (Opcional)", concepto_det_options)
                        else:
                            concepto_det_sel = None
                    else:
                        subrubro_sel = None
                        concepto_det_sel = None
                        
                    proyecto_options = dict(zip('[' + df_p_activos['codigo'] + '] ' + df_p_activos['nombre'], df_p_activos['id']))
                    proy_name = st.selectbox("Proyecto Asociado", list(proyecto_options.keys()))
                    proy_id = proyecto_options[proy_name]
                    
                with col2:
                    st.markdown("##### **3. Datos Fiscales y Método de Pago**")
                    deducible = st.selectbox("¿Deducible / Facturable?", ["Sí", "No"])
                    estado_fact = st.selectbox("Estatus de Facturación", ["Pendiente", "Facturado"])
                    metodo_pago = st.selectbox("Método de Pago", ["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"])
                    
                    df_c_filtered = df_c_all[df_c_all['tipo'] == metodo_pago]
                    if not df_c_filtered.empty:
                        cuenta_options = dict(zip(df_c_filtered['nombre'], df_c_filtered['id']))
                        cuenta_name = st.selectbox("Cuenta / Tarjeta Origen", list(cuenta_options.keys()))
                        cuenta_id = cuenta_options[cuenta_name]
                    else:
                        cuenta_id = None
                        st.warning(f"No hay cuentas configuradas para {metodo_pago}.")
                        
                    st.markdown("##### **4. Soporte Digital (CFDI / XML & Fotos)**")
                    xml_file = st.file_uploader("Adjuntar XML de Factura (CFDI)", type=["xml"])
                    
                    st.markdown("**Adjuntar Foto / Comprobante:**")
                    col_up, col_paste = st.columns([3, 2])
                    with col_up:
                        img_file = st.file_uploader("Subir Imagen (JPG, PNG)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
                    with col_paste:
                        paste_res = paste_image_button(
                            label="📋 Pegar Imagen (Ctrl+V)",
                            background_color="#434E62",
                            hover_background_color="#2C3E50",
                            text_color="#FFFFFF",
                            key="paste_comprobante_gasto"
                        )
                    
                    pasted_img = paste_res.image_data if (paste_res and paste_res.image_data is not None) else None
                    if pasted_img is not None:
                        st.image(pasted_img, caption="📷 Comprobante pegado desde el portapapeles", width=220)
                    
                    rfc_prov = None
                    uuid_fisc = None
                    
                    if xml_file is not None:
                        xml_bytes = xml_file.read()
                        xml_info = parse_cfdi_xml(xml_bytes)
                        if xml_info['valid']:
                            st.success(f"✓ CFDI Válido | RFC: {xml_info['rfc_emisor']} | UUID: {xml_info['uuid'][:8]}...")
                            rfc_prov = xml_info['rfc_emisor']
                            uuid_fisc = xml_info['uuid']
                            if abs(xml_info['total'] - monto_g) > 0.05:
                                st.warning(f"⚠️ El total del XML (${xml_info['total']:,.2f}) no coincide exactamente con el monto ingresado (${monto_g:,.2f}).")
                        else:
                            st.error(f"❌ Error en XML: {xml_info['error']}")
                            
                submit_gasto = st.form_submit_button("🚀 Registrar Gasto Oficialmente", use_container_width=True)
                
                if submit_gasto:
                    if not concepto_g:
                        st.error("El concepto del gasto es obligatorio.")
                    elif cuenta_id is None:
                        st.error("Debe seleccionar una cuenta de cargo válida.")
                    else:
                        rubro_val = rubro_sel if rubro_sel != "— Dejar en blanco —" else None
                        subrubro_val = subrubro_sel if subrubro_sel != "— Dejar en blanco —" else None
                        detallado_val = concepto_det_sel if concepto_det_sel != "— Dejar en blanco —" else None
                        
                        img_filename = None
                        if img_file is not None:
                            img_ext = os.path.splitext(img_file.name)[1]
                            img_filename = f"comprobante_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{img_ext}"
                            img_path = os.path.join(COMPROBANTES_DIR, img_filename)
                            with open(img_path, "wb") as f:
                                f.write(img_file.read())
                        elif pasted_img is not None:
                            img_filename = f"comprobante_pasted_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                            img_path = os.path.join(COMPROBANTES_DIR, img_filename)
                            pasted_img.save(img_path, format="PNG")
                                
                        xml_filename = None
                        if xml_file is not None and xml_info.get('valid', False):
                            xml_filename = f"cfdi_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xml"
                            xml_path = os.path.join(COMPROBANTES_DIR, xml_filename)
                            with open(xml_path, "wb") as f:
                                f.write(xml_bytes)
                                
                        success, insert_id = db.add_gasto(
                            fecha=fecha_g.strftime('%Y-%m-%d'),
                            concepto=concepto_g,
                            monto_neto=monto_g,
                            rubro=rubro_val,
                            subrubro=subrubro_val,
                            concepto_detallado=detallado_val,
                            proyecto_id=proy_id,
                            deducible=deducible,
                            estado_facturacion=estado_fact,
                            metodo_pago=metodo_pago,
                            cuenta_id=cuenta_id,
                            rfc_proveedor=rfc_prov,
                            uuid_fiscal=uuid_fisc,
                            xml_filename=xml_filename,
                            comprobante_img_filename=img_filename
                        )
                        
                        if success:
                            gasto_pdf_info = {
                                'id': insert_id,
                                'fecha': fecha_g.strftime('%Y-%m-%d'),
                                'concepto': concepto_g,
                                'monto_neto': monto_g,
                                'proyecto_nombre': proy_name,
                                'metodo_pago': metodo_pago,
                                'cuenta_nombre': cuenta_name,
                                'rubro': rubro_val,
                                'subrubro': subrubro_val,
                                'concepto_detallado': detallado_val,
                                'deducible': deducible,
                                'estado_facturacion': estado_fact,
                                'rfc_proveedor': rfc_prov,
                                'uuid_fiscal': uuid_fisc
                            }
                            
                            pdf_bytes = pdf_gen.generar_pdf_gasto(gasto_pdf_info)
                            local_pdf_name = f"recibo_gasto_{insert_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                            with open(os.path.join(COMPROBANTES_DIR, local_pdf_name), "wb") as f:
                                f.write(pdf_bytes)
                                
                            db.update_gasto(insert_id, pdf_filename=local_pdf_name)
                            
                            st.session_state['last_pdf_bytes'] = pdf_bytes
                            st.session_state['last_pdf_name'] = local_pdf_name
                            st.session_state['gasto_guardado_exito'] = True
                            st.rerun()
                        else:
                            st.error(f"Error al guardar gasto: {insert_id}")
            
            st.markdown("---")
            st.markdown("#### **Histórico Reciente de Gastos Capturados**")
            df_g = db.get_gastos_df()
            if not df_g.empty:
                df_renamed = df_g.copy()
                df_renamed['monto_neto_fmt'] = df_renamed['monto_neto'].map('${:,.2f}'.format)
                
                cols_order = ['id', 'fecha', 'concepto', 'monto_neto_fmt', 'proyecto_nombre', 'rubro', 'subrubro', 'deducible', 'estado_facturacion', 'metodo_pago', 'cuenta_nombre']
                df_renamed = df_renamed[cols_order]
                df_renamed.columns = ['ID', 'Fecha', 'Concepto', 'Monto Neto', 'Proyecto', 'Rubro', 'Subrubro', 'Deducible', 'Factura', 'Método Pago', 'Cuenta']
                
                def style_row(row):
                    if row['Factura'] == 'Facturado':
                        return ['background-color: #EBF5FB; color: #1B4F72'] * len(row)
                    elif row['Factura'] == 'Pendiente':
                        return ['background-color: #FEF9E7; color: #7D6608'] * len(row)
                    return [''] * len(row)
                
                styler = df_renamed.style.apply(style_row, axis=1)
                st.dataframe(styler, use_container_width=True, hide_index=True)
                
                df_with_img = df_g[df_g['comprobante_img_filename'].notna() & (df_g['comprobante_img_filename'] != '')]
                if not df_with_img.empty:
                    with st.expander("📷 Visualizar Comprobante de Transferencia / Fotos"):
                        img_select_opts = dict(zip(df_with_img['id'].astype(str) + " - " + df_with_img['concepto'], df_with_img['comprobante_img_filename']))
                        selected_img_key = st.selectbox("Seleccione Gasto para ver la foto:", list(img_select_opts.keys()))
                        selected_img_file = img_select_opts[selected_img_key]
                        img_path = os.path.join(COMPROBANTES_DIR, selected_img_file)
                        if os.path.exists(img_path):
                            st.image(img_path, caption=f"Comprobante del Gasto: {selected_img_key}", use_container_width=True)
            else:
                st.info("No hay gastos registrados.")


# ─── MÓDULO 1: GASTOS — CAPTURA & CARGA MASIVA ──────────────────────────────
if menu.startswith("1."):
    render_header("Gastos Operativos", "Capture gastos individuales o realice cargas masivas en Excel.")
    
    tab_captura, tab_masiva = st.tabs([
        "💵 1.1 Captura Individual de Gasto", 
        "📂 1.2 Carga Masiva (Excel)"
    ])
    
    with tab_captura:
        _render_captura_individual_gasto()
        
    with tab_masiva:
        _render_carga_masiva_excel()

# ─── MÓDULO 2: PROYECTOS — GESTIÓN & PARETO ─────────────────────────────────
elif menu.startswith("2."):
    render_header("Proyectos", "Administre proyectos, órdenes de compra y evalúe la salud financiera y pareto de costos.")
    
    tab_proy_alta, tab_backorder, tab_estado, tab_pareto, tab_progreso = st.tabs([
        "📁 2.1 Alta & Gestión de Proyectos",
        "📝 2.2 Órdenes de Compra",
        "📊 2.3 Estado General por Proyecto",
        "📉 2.4 Pareto de Costos",
        "📈 2.5 Progreso vs Presupuesto"
    ])
    
    df_gastos = db.get_gastos_df()
    df_proy = db.get_proyectos()
    
    with tab_proy_alta:
        _render_gestion_proyectos()
        
    with tab_backorder:
        _render_control_backorder()
        
    with tab_estado:
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
            
    with tab_progreso:
        proy_dash.render_progreso_presupuesto(df_proy, df_gastos)


# ─── MÓDULO 3: FLUJO DE CAJA PROYECTADO ──────────────────────────────────────
elif menu.startswith("3."):
    render_header("Flujo de Caja Proyectado", "Proyecte, programe y controle el flujo de caja e ingresos/egresos del negocio.")
    flujo.render_flujo_caja_modulo()

# ─── MÓDULO 4: DASHBOARDS INTERACTIVOS ───────────────────────────────────────
elif menu.startswith("4."):
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
            df_g_filtered = df_g_filtered[(df_g_filtered['fecha_dt'].dt.date >= start_date) & (df_g_filtered['fecha_dt'].dt.date <= end_date)]
        if not df_b_filtered.empty:
            df_b_filtered['fecha_dt'] = pd.to_datetime(df_b_filtered['fecha_compromiso'])
            df_b_filtered = df_b_filtered[(df_b_filtered['fecha_dt'].dt.date >= start_date) & (df_b_filtered['fecha_dt'].dt.date <= end_date)]
            
    if proj_sel != "Todos":
        df_g_filtered = df_g_filtered[df_g_filtered['proyecto_nombre'] == proj_sel]
        df_b_filtered = df_b_filtered[df_b_filtered['proyecto_nombre'] == proj_sel]
        
    if deduc_sel != "Todos":
        df_g_filtered = df_g_filtered[df_g_filtered['deducible'] == deduc_sel]

    tab1, tab2, tab3 = st.tabs(["📊 4.1 Gastos Operativos", "📝 4.2 Órdenes de Compra", "📁 4.3 Rentabilidad de Proyectos"])
    
    with tab1:
        dash.render_gastos_dashboard(df_g_filtered)
        
    with tab2:
        dash.render_backorder_dashboard(df_b_filtered)
        
    with tab3:
        dash.render_proyectos_dashboard(df_proy_base, df_g_filtered)

# ─── MÓDULO 5: EBITDA & REPORTES ─────────────────────────────────────────────
elif menu.startswith("5."):
    render_header("EBITDA & Reportes de Cuenta", "Calcule el rendimiento operativo de la empresa y exporte reportes por método de pago.")
    
    df_gastos = db.get_gastos_df()
    df_proy = db.get_proyectos()
    
    tab_ebitda, tab_export = st.tabs(["📊 5.1 Cálculo de EBITDA", "📥 5.2 Exportar Reportes"])
    
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
                    pdf_bytes = None

            # Generación de archivo EML de copia
            st.markdown("---")
            st.markdown("##### **📩 Generar Plantilla de Correo (.eml) para Enviar Copia**")
            
            df_users = db.get_usuarios_df()
            emails_registrados = []
            if not df_users.empty and 'email' in df_users.columns:
                emails_registrados = df_users['email'].dropna().tolist()
            
            opciones_email = emails_registrados + ["Otro correo..."]
            dest_email_sel = st.selectbox(f"Seleccione Destinatario ({filename_prefix})", opciones_email, key=f"eml_dest_{filename_prefix}")
            
            if dest_email_sel == "Otro correo...":
                dest_email = st.text_input(f"Escriba el correo destino ({filename_prefix})", placeholder="ejemplo@jd-automation.com", key=f"eml_dest_txt_{filename_prefix}").strip()
            else:
                dest_email = dest_email_sel
                
            if st.button(f"Generar Archivo EML ({filename_prefix})", use_container_width=True):
                if dest_email:
                    try:
                        if not pdf_bytes:
                            pdf_bytes = pdf_gen.generar_pdf_tabla(df_disp, f"Reporte de Movimientos - {filename_prefix.upper()}")
                        
                        pdf_att_name = f"reporte_{filename_prefix}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
                        subject = f"Reporte de Movimientos - {filename_prefix.upper()} - J&D Automation"
                        body = f"Hola,\n\nSe adjunta el reporte de movimientos de {filename_prefix.upper()} de J&D Automation Industries correspondiente al día de hoy ({datetime.date.today().strftime('%d/%m/%Y')}).\n\nSaludos,\nSistema de Control Financiero J&D."
                        
                        eml_data = generar_eml_bytes(dest_email, subject, body, pdf_bytes, pdf_att_name)
                        
                        st.download_button(
                            label=f"📥 Descargar Archivo EML ({filename_prefix}.eml)",
                            data=eml_data,
                            file_name=f"reporte_{filename_prefix}_{datetime.date.today().strftime('%Y%m%d')}.eml",
                            mime="message/rfc822",
                            use_container_width=True
                        )
                        st.success("✉️ Archivo EML generado con éxito. Descárguelo y ábralo en su gestor de correo para enviar.")
                    except Exception as e:
                        st.error(f"Error al generar correo: {str(e)}")
                else:
                    st.warning("Ingrese o seleccione un correo electrónico válido.")
            
        with tab_cc:
            df_cc = df_gastos[df_gastos['metodo_pago'] == 'Tarjeta de Crédito']
            render_export_section(df_cc, "tarjeta_credito")
            
        with tab_trans:
            df_trans = df_gastos[df_gastos['metodo_pago'] == 'Transferencia Bancaria']
            render_export_section(df_trans, "transferencias_bancarias")
            
        with tab_cash:
            df_cash = df_gastos[df_gastos['metodo_pago'] == 'Efectivo']
            render_export_section(df_cash, "movimientos_efectivo")

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
