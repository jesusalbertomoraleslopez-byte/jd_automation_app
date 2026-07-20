"""
modules/industria40.py — Sección de Manufactura Inteligente e Industria 4.0
"""
import streamlit as st
import plotly.graph_objects as go
from modules.pdf_generator import generar_pdf_tabla
import pandas as pd
import io

def render_industria40():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#434E62 60%,#FE8C29 100%); border-radius:12px; padding:28px 36px; margin-bottom:24px;">
        <div style="color:#FFFFFF; font-size:28px; font-weight:900; font-family:'Montserrat',sans-serif; letter-spacing:-0.5px;">
            🤖 Manufactura Inteligente & Industria 4.0
        </div>
        <div style="color:rgba(255,255,255,0.78); font-size:14px; margin-top:8px;">
            Transformación digital aplicada a la gestión financiera de proyectos de automatización industrial.
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📋 6.1 Justificación Estratégica",
        "🚀 6.2 Beneficios del Proyecto",
        "🛠️ 6.3 Stack Tecnológico"
    ])

    with tab1:
        _render_justificacion()

    with tab2:
        _render_beneficios()

    with tab3:
        _render_stack()

    st.markdown("---")
    _render_export_pdf()


def _render_justificacion():
    st.markdown("### ¿Por qué J&D Automation Industries necesita Control Financiero Inteligente?")

    st.markdown("""
    <div style="background:#FFFFFF; border-radius:10px; padding:20px 28px; border-left:5px solid #FE8C29; margin-bottom:16px;">
        <b style="color:#434E62;">Contexto del Problema</b><br>
        <span style="color:#555; font-size:14px;">
        En empresas de ingeniería y automatización industrial, los proyectos involucran decenas de proveedores,
        cientos de partidas de gasto y múltiples métodos de pago simultáneos. Sin un sistema centralizado,
        el control financiero se vuelve reactivo y opaco — lo que compromete la rentabilidad de los proyectos.
        </span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    problemas = [
        ("⚠️ Falta de Trazabilidad", "Los gastos operativos se registran en hojas de cálculo dispersas sin vinculación al proyecto ni al cliente."),
        ("📊 Sin Visibilidad en Tiempo Real", "La dirección recibe información financiera con semanas de retraso, limitando decisiones estratégicas."),
        ("🧾 Cumplimiento Fiscal Reactivo", "La conciliación de facturas (CFDI/SAT) se hace manualmente, generando riesgos de errores y rechazos."),
    ]
    for col, (titulo, desc) in zip(cols, problemas):
        col.markdown(f"""
        <div style="background:#FFFFFF; border-radius:10px; padding:16px; height:140px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:15px; font-weight:700; color:#434E62;">{titulo}</div>
            <div style="font-size:12px; color:#666; margin-top:8px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 🎯 La Solución: Control Financiero basado en Industria 4.0")
    st.markdown("""
    **J&D Automation Industries** implementa este sistema alineado a los principios de la **4ª Revolución Industrial**:
    - **Digitalización** de todos los registros financieros (eliminación del papel).
    - **Interoperabilidad** con el SAT a través de la lectura de CFDI (XML).
    - **Análisis de Datos** en tiempo real con dashboards interactivos.
    - **Toma de Decisiones Basada en Datos** para la dirección de proyectos.
    """)


def _render_beneficios():
    st.markdown("### 🚀 Beneficios Estratégicos del Proyecto")

    beneficios = [
        {"area": "Rentabilidad", "antes": "Control manual en Excel", "despues": "Dashboard en tiempo real con alerta de proyectos en riesgo", "impacto": "Alto"},
        {"area": "Cumplimiento SAT", "antes": "Conciliación manual mensual", "despues": "Validación automática de CFDI al momento de la captura", "impacto": "Alto"},
        {"area": "Control de Costos", "antes": "Sin clasificación estandarizada", "despues": "Jerarquía de 3 niveles (Rubro→Subrubro→Concepto)", "impacto": "Alto"},
        {"area": "EBITDA", "antes": "Cálculo trimestral aproximado", "despues": "EBITDA dinámico con desglose por proyecto", "impacto": "Medio"},
        {"area": "Auditoría", "antes": "Documentos físicos dispersos", "despues": "Respaldo PDF automático de cada transacción", "impacto": "Alto"},
        {"area": "Eficiencia Operativa", "antes": "4-8 horas semanales en reportes", "despues": "Reportes instantáneos descargables en CSV/PDF", "impacto": "Medio"},
    ]

    df_ben = pd.DataFrame(beneficios)
    df_ben.columns = ['Área', 'Situación Anterior', 'Situación Con el Sistema', 'Impacto']
    st.dataframe(df_ben, use_container_width=True, hide_index=True)

    st.markdown("#### 📈 Indicadores de ROI Estimado")
    cols = st.columns(4)
    kpis = [
        ("⏱️ Tiempo en Reportes", "-80%", "De 8h a 1.5h/semana"),
        ("💰 Visibilidad de Costos", "+100%", "Desde día 1 de implementación"),
        ("📋 Precisión Fiscal", "+95%", "Validación automática CFDI"),
        ("📊 Proyectos Monitoreados", "4+", "En tiempo real simultáneo"),
    ]
    for col, (titulo, valor, desc) in zip(cols, kpis):
        col.metric(titulo, valor, desc)


def _render_stack():
    st.markdown("### 🛠️ Stack Tecnológico del Sistema")

    stack = [
        {"Capa": "Frontend / UI", "Tecnología": "Streamlit 1.30+", "Rol": "Interfaz web reactiva en Python", "Justificación": "Despliegue rápido sin necesidad de JavaScript"},
        {"Capa": "Análisis de Datos", "Tecnología": "Pandas 2.0+", "Rol": "Manipulación y transformación de datos", "Justificación": "Estándar de la industria para data engineering"},
        {"Capa": "Visualización", "Tecnología": "Plotly 5.x", "Rol": "Dashboards y gráficas interactivas", "Justificación": "Gráficas de alta calidad con interactividad nativa"},
        {"Capa": "Base de Datos", "Tecnología": "SQLite 3", "Rol": "Persistencia de datos transaccional", "Justificación": "Sin servidor requerido, ideal para PYME"},
        {"Capa": "Excel / Plantillas", "Tecnología": "OpenPyXL 3.1+", "Rol": "Generación de plantillas con validaciones", "Justificación": "Compatible 100% con Microsoft Excel"},
        {"Capa": "Generación PDF", "Tecnología": "FPDF2 2.7+", "Rol": "Recibos, reportes y manuales en PDF", "Justificación": "Ligero, sin dependencias externas"},
        {"Capa": "Seguridad", "Tecnología": "bcrypt 4.0+", "Rol": "Hash seguro de contraseñas", "Justificación": "Estándar criptográfico para autenticación"},
        {"Capa": "Fiscal / SAT", "Tecnología": "xml.etree.ElementTree", "Rol": "Lectura y validación de CFDI (XML)", "Justificación": "Nativo de Python, sin dependencias externas"},
        {"Capa": "Control de Versiones", "Tecnología": "GitHub", "Rol": "Repositorio del código fuente", "Justificación": "Colaboración y despliegue continuo (CI/CD)"},
        {"Capa": "Deployment", "Tecnología": "Streamlit Community Cloud", "Rol": "Servidor de despliegue gratuito", "Justificación": "Despliegue automático desde GitHub"},
    ]

    df_stack = pd.DataFrame(stack)
    st.dataframe(df_stack, use_container_width=True, hide_index=True)

    # Diagrama visual de arquitectura
    st.markdown("#### 🏗️ Diagrama de Arquitectura")
    fig = go.Figure()
    layers = [
        ("Usuario Final", 5, "#FE8C29"),
        ("Streamlit Web App", 4, "#434E62"),
        ("Módulos Python\n(auth, pdf, dashboards, etc.)", 3, "#5C7A9B"),
        ("SQLite + Sistema de Archivos", 2, "#8C96A6"),
        ("GitHub + Streamlit Cloud", 1, "#B4BCC6"),
    ]
    for name, y, color in layers:
        fig.add_trace(go.Scatter(
            x=[1, 9], y=[y, y],
            mode='lines',
            line=dict(color=color, width=30),
            name=name
        ))
        fig.add_annotation(x=5, y=y, text=f"<b>{name}</b>", showarrow=False,
                           font=dict(color='white', size=12))

    fig.update_layout(
        height=350, showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_export_pdf():
    st.markdown("### 📄 Exportar Sección")
    stack_data = [
        {"Capa": "Frontend", "Tecnología": "Streamlit 1.30+"},
        {"Capa": "Datos", "Tecnología": "Pandas + SQLite"},
        {"Capa": "Visualización", "Tecnología": "Plotly 5.x"},
        {"Capa": "PDF", "Tecnología": "FPDF2"},
        {"Capa": "Seguridad", "Tecnología": "bcrypt"},
        {"Capa": "Deploy", "Tecnología": "GitHub + Streamlit Cloud"},
    ]
    df_export = pd.DataFrame(stack_data)
    pdf_bytes = generar_pdf_tabla(df_export, "Stack Tecnológico — J&D Automation Industries")
    st.download_button(
        "📥 Descargar Resumen I4.0 en PDF",
        data=pdf_bytes,
        file_name="JD_Industria40_Stack.pdf",
        mime="application/pdf"
    )
