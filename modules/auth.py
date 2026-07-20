"""
modules/auth.py — Sistema de Autenticación para J&D Automation Industries
Gestiona el login, sesión de usuario, y control de acceso por rol.
"""
import streamlit as st
import os
import database as db

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brand', 'logo_corporativo.png')
LOGO_BLANCO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brand', 'logo_blanco.png')

def render_login():
    """Renderiza la pantalla de login corporativa. Retorna True si se autentica."""
    st.markdown("""
    <style>
    .login-card {
        max-width: 440px;
        margin: 60px auto;
        background: #FFFFFF;
        border-radius: 16px;
        padding: 40px 48px;
        box-shadow: 0 8px 32px rgba(67,78,98,0.15);
        border-top: 6px solid #FE8C29;
    }
    .login-title {
        color: #434E62;
        font-family: 'Montserrat', sans-serif;
        font-size: 22px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 4px;
    }
    .login-subtitle {
        color: #8C96A6;
        font-size: 13px;
        text-align: center;
        margin-bottom: 28px;
    }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_center, col_r = st.columns([1, 2, 1])
    with col_center:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=200)
        st.markdown('<div class="login-title">Control Financiero</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">J&D Automation Industries — Acceso Restringido</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            usuario = st.text_input("👤 Usuario", placeholder="admin")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)

        if submitted:
            result = db.verificar_login(usuario.strip(), password)
            if result:
                st.session_state['usuario'] = result
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos. Intente nuevamente.")

        st.markdown("""
        <div style='text-align:center; margin-top:24px; color:#8C96A6; font-size:11px;'>
        Credenciales por defecto: <b>admin</b> / <b>JD2024Admin</b><br>
        Por favor cambie su contraseña en el módulo de Mantenimiento.
        </div>
        """, unsafe_allow_html=True)

    return st.session_state.get('autenticado', False)

def get_usuario():
    """Retorna el dict del usuario activo o None."""
    return st.session_state.get('usuario', None)

def get_rol():
    """Retorna el rol del usuario activo o None."""
    u = get_usuario()
    return u['rol'] if u else None

def es_admin():
    return get_rol() == 'Administrador'

def render_sidebar_usuario():
    """Renderiza el badge de sesión activa en el sidebar."""
    u = get_usuario()
    if u:
        rol_color = {'Administrador': '#FE8C29', 'Capturista': '#5C9BFE', 'Consultor': '#62C462'}.get(u['rol'], '#FFFFFF')
        st.sidebar.markdown(f"""
        <div style='background: rgba(255,255,255,0.08); border-radius:8px; padding:10px 14px; margin-bottom:8px;'>
            <div style='color:#FFFFFF; font-size:13px; font-weight:700;'>👤 {u.get('nombre_completo','')}</div>
            <div style='color:{rol_color}; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px;'>
                ● {u['rol']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

def requiere_auth():
    """Verifica si el usuario está autenticado; si no, muestra login."""
    if not st.session_state.get('autenticado', False):
        render_login()
        st.stop()

def requiere_admin():
    """Verifica que el usuario sea Administrador; si no, muestra acceso denegado."""
    if not es_admin():
        st.error("🔒 **Acceso Denegado**: Este módulo está restringido a usuarios con rol **Administrador**.")
        st.stop()
