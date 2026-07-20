"""
modules/mantenimiento.py — Sección de Mantenimiento del Sistema (Solo Administrador)
"""
import streamlit as st
import pandas as pd
import os
import database as db

# Directorio de comprobantes físicos
COMPROBANTES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'comprobantes')

def render_mantenimiento():
    st.markdown("""
    <div style="border-left: 3px solid #FE8C29; padding-left: 20px; margin-bottom: 20px;">
      <h2 style="margin: 0; color: #434E62; font-family: 'Montserrat', sans-serif; font-size: 24px; font-weight: 700;">Mantenimiento del Sistema</h2>
      <p style="margin: 3px 0 0 0; color: #8C96A6; font-family: 'Montserrat', sans-serif; font-size: 13px;">Panel de administración técnica, usuarios, clasificaciones y limpieza de registros.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_clasifs, tab_users, tab_records, tab_cleanup = st.tabs([
        "⚙️ 8.1 Gestión de Clasificaciones",
        "👥 8.2 Gestión de Usuarios",
        "📝 8.3 Corrección de Registros",
        "🗑️ 8.4 Limpieza de BD y Archivos"
    ])

    with tab_clasifs:
        _render_gestion_clasificaciones()

    with tab_users:
        _render_gestion_usuarios()

    with tab_records:
        _render_correccion_registros()

    with tab_cleanup:
        _render_limpieza_sistema()


def _render_gestion_clasificaciones():
    st.subheader("Administración de Clasificaciones Jerárquicas")
    
    col_form, col_table = st.columns([1, 2])
    
    with col_form:
        st.markdown("#### **Agregar Nueva Clasificación**")
        
        # Obtener los rubros y subrubros existentes para autocompletar o escribir nuevos
        clasifs_dict = db.get_clasificaciones_dict()
        rubros_existentes = list(clasifs_dict.keys())
        
        # Selección o creación de Rubro
        opcion_rubro = st.radio("Método para Rubro Principal", ["Seleccionar Existente", "Crear Nuevo"])
        if opcion_rubro == "Seleccionar Existente" and rubros_existentes:
            nuevo_rubro = st.selectbox("Rubro Principal Existente", rubros_existentes)
        else:
            nuevo_rubro = st.text_input("Nuevo Rubro Principal", placeholder="Ej. Gastos Especiales").strip()
            
        # Selección o creación de Subrubro
        subrubros_existentes = []
        if opcion_rubro == "Seleccionar Existente" and nuevo_rubro in clasifs_dict:
            subrubros_existentes = list(clasifs_dict[nuevo_rubro].keys())
            
        opcion_sub = st.radio("Método para Subrubro", ["Seleccionar Existente", "Crear Nuevo"])
        if opcion_sub == "Seleccionar Existente" and subrubros_existentes:
            nuevo_subrubro = st.selectbox("Subrubro Existente", subrubros_existentes)
        else:
            nuevo_subrubro = st.text_input("Nuevo Subrubro", placeholder="Ej. Licencias y Software").strip()
            
        # Ingreso de Concepto Detallado
        nuevo_concepto = st.text_input("Concepto Detallado", placeholder="Ej. Licencia AutoCAD Anual").strip()
        
        if st.button("Guardar Clasificación", use_container_width=True):
            if nuevo_rubro and nuevo_subrubro and nuevo_concepto:
                success, msg = db.add_clasificacion(nuevo_rubro, nuevo_subrubro, nuevo_concepto)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Todos los campos (Rubro, Subrubro y Concepto) son obligatorios.")

    with col_table:
        st.markdown("#### **Catálogo de Clasificaciones Activas**")
        df_c = db.get_clasificaciones_df()
        if not df_c.empty:
            df_disp = df_c.copy()
            df_disp.columns = ['ID', 'Rubro Principal', 'Subrubro', 'Concepto Detallado']
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
            
            # Opción para borrar
            st.markdown("---")
            st.markdown("#### **🗑️ Eliminar una Clasificación**")
            col_del_id, col_del_btn = st.columns([2, 1])
            with col_del_id:
                id_eliminar = st.number_input("Ingrese el ID de la clasificación a eliminar:", min_value=1, step=1, key="del_clas_id")
            with col_del_btn:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("Eliminar Clasificación", key="del_clas_btn", use_container_width=True):
                    success, msg = db.delete_clasificacion(id_eliminar)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("No hay clasificaciones registradas.")


def _render_gestion_usuarios():
    st.subheader("Gestión de Usuarios del Sistema")
    
    col_list, col_actions = st.columns([2, 1])
    
    with col_list:
        st.markdown("#### **Usuarios Registrados**")
        df_u = db.get_usuarios_df()
        if not df_u.empty:
            df_disp = df_u.copy()
            df_disp['activo'] = df_disp['activo'].map({1: 'Activo', 0: 'Inactivo'})
            df_disp.columns = ['ID', 'Usuario', 'Nombre Completo', 'Correo Electrónico', 'Rol', 'Estado']
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
        else:
            st.info("No hay usuarios registrados.")
            
    with col_actions:
        st.markdown("#### **Crear Nuevo Usuario**")
        new_username = st.text_input("Nombre de Usuario (Login)", key="new_u_username").strip()
        new_password = st.text_input("Contraseña", type="password", key="new_u_pass")
        new_fullname = st.text_input("Nombre Completo", key="new_u_fullname").strip()
        new_email = st.text_input("Correo Electrónico", key="new_u_email").strip()
        new_rol = st.selectbox("Rol del Usuario", ["Administrador", "Capturista", "Consultor"], key="new_u_rol")
        
        if st.button("Crear Usuario", use_container_width=True):
            if new_username and new_password and new_fullname and new_email:
                success, msg = db.add_usuario(new_username, new_password, new_fullname, new_email, new_rol)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Complete todos los campos del nuevo usuario (incluyendo el correo).")

        st.markdown("---")
        st.markdown("#### **Modificar Usuario**")
        if not df_u.empty:
            user_select = st.selectbox("Seleccione Usuario", df_u['username'].tolist())
            user_row = df_u[df_u['username'] == user_select].iloc[0]
            action = st.selectbox("Acción", ["Editar Datos (Nombre/Correo/Rol)", "Cambiar Contraseña", "Cambiar Estado (Activo/Inactivo)"])
            
            if action == "Editar Datos (Nombre/Correo/Rol)":
                mod_fullname = st.text_input("Nombre Completo", value=str(user_row['nombre_completo'] or ''))
                mod_email = st.text_input("Correo Electrónico", value=str(user_row['email'] or ''))
                roles = ["Administrador", "Capturista", "Consultor"]
                try:
                    rol_index = roles.index(user_row['rol'])
                except ValueError:
                    rol_index = 0
                mod_rol = st.selectbox("Rol del Usuario", roles, index=rol_index)
                
                if st.button("Guardar Cambios", use_container_width=True):
                    if mod_fullname and mod_email:
                        success, msg = db.update_usuario_detalles(user_select, mod_fullname, mod_email, mod_rol)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("El nombre y el correo no pueden quedar vacíos.")
            elif action == "Cambiar Contraseña":
                new_pwd = st.text_input("Nueva Contraseña", type="password", key="change_pwd_input")
                if st.button("Actualizar Contraseña", use_container_width=True):
                    if new_pwd:
                        success, msg = db.cambiar_password(user_select, new_pwd)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Ingrese una contraseña válida.")
            else:
                current_status = "Activo" if user_row['activo'] == 1 else "Inactivo"
                new_status_val = 0 if user_row['activo'] == 1 else 1
                new_status_txt = "Desactivar" if user_row['activo'] == 1 else "Activar"
                
                st.write(f"Estado actual: **{current_status}**")
                if st.button(f"{new_status_txt} Usuario", use_container_width=True):
                    success, msg = db.toggle_usuario_activo(user_row['id'], new_status_val)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def _render_correccion_registros():
    st.subheader("Corrección y Modificación Directa de Egresos")
    st.markdown("Edite los datos de la tabla directamente y presione el botón de abajo para guardar los cambios en la base de datos.")
    
    df_gastos = db.get_gastos_df()
    if not df_gastos.empty:
        # Preparar columnas editables
        cols_edit = [
            'id', 'fecha', 'concepto', 'monto_neto', 'rubro', 'subrubro', 'concepto_detallado',
            'proyecto_id', 'deducible', 'estado_facturacion', 'metodo_pago', 'cuenta_id',
            'rfc_proveedor', 'uuid_fiscal'
        ]
        
        df_editable = df_gastos[cols_edit].copy()
        
        # Usar st.data_editor
        df_edited = st.data_editor(
            df_editable,
            disabled=['id'], # Evitar que editen el folio interno
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "Folio",
                "fecha": st.column_config.TextColumn("Fecha (AAAA-MM-DD)"),
                "concepto": st.column_config.TextColumn("Concepto Gral"),
                "monto_neto": st.column_config.NumberColumn("Monto Neto (IVA Incl)"),
                "deducible": st.column_config.SelectboxColumn("Deducible", options=["Sí", "No"]),
                "estado_facturacion": st.column_config.SelectboxColumn("Facturación", options=["Pendiente", "Facturado"]),
                "metodo_pago": st.column_config.SelectboxColumn("Método", options=["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"])
            }
        )
        
        if st.button("💾 Guardar Cambios en la Base de Datos", use_container_width=True):
            success_count = 0
            err_list = []
            
            # Comparar y aplicar cambios
            for idx, row in df_edited.iterrows():
                original_row = df_editable.iloc[idx]
                # Buscar diferencias
                changes = {}
                for col in cols_edit:
                    if col == 'id':
                        continue
                    if row[col] != original_row[col]:
                        changes[col] = row[col]
                
                if changes:
                    # Aplicar actualización en BD
                    ok, err = db.update_gasto(row['id'], **changes)
                    if ok:
                        success_count += 1
                    else:
                        err_list.append(f"Folio #{row['id']}: {err}")
            
            if success_count > 0:
                st.success(f"🎉 Se actualizaron correctamente {success_count} registros de gastos.")
            if err_list:
                for err in err_list:
                    st.error(err)
            if success_count > 0 and not err_list:
                st.rerun()
                
        st.markdown("---")
        st.markdown("#### 🗑️ Borrar un Registro Específico")
        del_gasto_id = st.number_input("Ingrese el Folio del gasto a eliminar permanentemente:", min_value=1, step=1, key="del_gasto_id_man")
        
        st.warning("⚠️ **Atención**: Esta acción es irreversible y eliminará el registro de la base de datos.")
        confirm_del = st.checkbox("Confirmar eliminación permanente del folio ingresado", key="confirm_del_gasto_chk")
        
        if st.button("🗑️ Eliminar Registro Permanentemente", key="del_gasto_btn_man"):
            if confirm_del:
                success, msg = db.delete_gasto(del_gasto_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.info("Debe marcar la casilla de confirmación para proceder.")
    else:
        st.info("No hay registros de gastos para modificar.")


def _render_limpieza_sistema():
    st.subheader("Acciones Destructivas y Limpieza de Almacenamiento")
    
    col_db, col_files = st.columns(2)
    
    with col_db:
        st.markdown("#### **1. Limpieza de Tablas de Base de Datos**")
        st.write("Seleccione la tabla que desea vaciar por completo. **Esta acción borrará todos los registros asociados**.")
        
        tabla_limpiar = st.selectbox("Seleccione Tabla", ["gastos", "backorder_oc", "proyectos", "cuentas"])
        
        st.error("🚨 **Advertencia de Seguridad**: El vaciado de tablas borrará permanentemente toda la información de la base de datos. Haga un respaldo previo.")
        confirm_clean_db = st.checkbox("Confirmo que deseo vaciar la tabla seleccionada", key="confirm_clean_db")
        
        if st.button("🔥 Vaciar Tabla por Completo", use_container_width=True):
            if confirm_clean_db:
                success, msg = db.limpiar_tabla(tabla_limpiar)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.info("Debe marcar la casilla de confirmación para proceder.")
                
    with col_files:
        st.markdown("#### **2. Explorador de Almacenamiento (Comprobantes)**")
        st.write("Consulte y limpie los archivos XML y PDF guardados físicamente en el servidor de almacenamiento local.")
        
        if os.path.exists(COMPROBANTES_DIR):
            archivos = os.listdir(COMPROBANTES_DIR)
            if archivos:
                st.info(f"📂 Actualmente hay **{len(archivos)}** comprobantes guardados físicamente.")
                archivo_sel = st.selectbox("Seleccione archivo para previsualizar o eliminar:", archivos)
                
                st.write(f"Archivo: `{archivo_sel}`")
                
                confirm_del_file = st.checkbox("Confirmo que deseo borrar este archivo del almacenamiento", key="confirm_del_file")
                if st.button("🗑️ Eliminar Archivo del Servidor", use_container_width=True):
                    if confirm_del_file:
                        try:
                            file_path = os.path.join(COMPROBANTES_DIR, archivo_sel)
                            os.remove(file_path)
                            st.success(f"Archivo '{archivo_sel}' eliminado correctamente del servidor.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al eliminar archivo: {str(e)}")
                    else:
                        st.info("Debe marcar la casilla de confirmación.")
            else:
                st.info("No hay archivos en la carpeta de comprobantes.")
        else:
            st.warning("El directorio de comprobantes no ha sido inicializado aún.")

        st.markdown("---")
        st.markdown("#### **3. Limpieza de Almacenamiento en GitHub**")
        st.write("Para eliminar o depurar archivos directamente desde el repositorio Git, utilice comandos remotos o el explorador web de GitHub.")
        st.markdown("💡 *Recomendación: Mantenga el almacenamiento local sincronizado periódicamente subiendo sus commits mediante git push.*")
