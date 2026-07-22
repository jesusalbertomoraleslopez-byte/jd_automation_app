"""
modules/mantenimiento.py — Sección de Mantenimiento del Sistema (Solo Administrador)
"""
import streamlit as st
import pandas as pd
import os
import datetime
import database as db
import modules.excel_handler as excel_handler

# Directorio de comprobantes físicos
COMPROBANTES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'comprobantes')

def render_mantenimiento():
    st.markdown("""
    <div style="border-left: 3px solid #FE8C29; padding-left: 20px; margin-bottom: 20px;">
      <h2 style="margin: 0; color: #434E62; font-family: 'Montserrat', sans-serif; font-size: 24px; font-weight: 700;">Mantenimiento del Sistema</h2>
      <p style="margin: 3px 0 0 0; color: #8C96A6; font-family: 'Montserrat', sans-serif; font-size: 13px;">Panel de administración técnica, usuarios, clasificaciones y limpieza de registros.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_cuentas, tab_clasifs, tab_users, tab_records, tab_cleanup = st.tabs([
        "💳 8.1 Cuentas & Tarjetas",
        "⚙️ 8.2 Gestión de Clasificaciones",
        "👥 8.3 Gestión de Usuarios",
        "📝 8.4 Corrección de Registros",
        "🗑️ 8.5 Limpieza de BD y Archivos"
    ])

    with tab_cuentas:
        _render_gestion_cuentas()

    with tab_clasifs:
        _render_gestion_clasificaciones()

    with tab_users:
        _render_gestion_usuarios()

    with tab_records:
        _render_correccion_registros()

    with tab_cleanup:
        _render_limpieza_sistema()


def _render_gestion_cuentas():
    st.subheader("Administración de Cuentas y Tarjetas Bancarias")
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

    # ─── HERRAMIENTAS DE EXCEL PARA CATÁLOGO ───
    st.markdown("---")
    st.markdown("### **📊 Herramientas de Excel para Catálogo de Clasificaciones**")
    
    col_ex1, col_ex2 = st.columns(2)
    
    with col_ex1:
        st.markdown("##### **1. Descargar Catálogo Actual**")
        st.caption("Exporta la lista completa de clasificaciones activas en un archivo Excel con formato corporativo.")
        excel_bytes = excel_handler.export_clasificaciones_excel()
        st.download_button(
            label="📥 Descargar Catálogo Actual (.xlsx)",
            data=excel_bytes,
            file_name=f"Catalogo_Clasificaciones_JD_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_ex2:
        st.markdown("##### **2. Carga Masiva desde Plantilla Excel**")
        st.caption("Descargue la plantilla, complete sus nuevos Rubros/Subrubros/Conceptos e impórtelos masivamente.")
        
        c_tmpl, c_blank = st.columns([1, 1])
        with c_tmpl:
            tmpl_bytes = excel_handler.generate_clasificaciones_template()
            st.download_button(
                label="📄 Plantilla Excel de Ejemplo",
                data=tmpl_bytes,
                file_name="Plantilla_Importar_Clasificaciones_JD.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        uploaded_clas_file = st.file_uploader("Subir Archivo Excel con Clasificaciones", type=["xlsx", "xls"], key="up_clas_excel")
        if uploaded_clas_file is not None:
            if st.button("🚀 Importar Clasificaciones a Base de Datos", type="primary", use_container_width=True):
                added, dups, errs = excel_handler.import_clasificaciones_excel(uploaded_clas_file.getvalue())
                if errs:
                    for err in errs:
                        st.error(err)
                if added > 0:
                    st.success(f"✅ ¡Éxito! Se importaron **{added}** nuevas clasificaciones correctamente.")
                    if dups > 0:
                        st.info(f"ℹ️ Se omitieron **{dups}** clasificaciones duplicadas que ya existían en la BD.")
                    st.rerun()
                elif dups > 0 and not errs:
                    st.warning(f"⚠️ Todas las clasificaciones del archivo (**{dups}**) ya existían en la BD.")


def _render_gestion_usuarios():
    st.subheader("Gestión de Usuarios del Sistema")
    
    col_list, col_actions = st.columns([2, 1])
    
    with col_list:
        st.markdown("#### **Usuarios Registrados (Editor Directo)**")
        st.markdown("Modifique cualquier celda (Nombre, Correo, Rol, Contraseña o Activo) y presione el botón de abajo para guardar.")
        df_u = db.get_usuarios_df()
        if not df_u.empty:
            df_disp = df_u.copy()
            df_disp['activo'] = df_disp['activo'].map({1: True, 0: False})
            df_disp.columns = ['ID', 'Usuario', 'Contraseña', 'Nombre Completo', 'Correo Electrónico', 'Rol', 'Activo']
            
            edited_df = st.data_editor(
                df_disp,
                column_config={
                    "ID": st.column_config.NumberColumn(disabled=True),
                    "Usuario": st.column_config.TextColumn(disabled=True),
                    "Contraseña": st.column_config.TextColumn(help="Contraseña en texto plano visible y editable"),
                    "Nombre Completo": st.column_config.TextColumn(),
                    "Correo Electrónico": st.column_config.TextColumn(),
                    "Rol": st.column_config.SelectboxColumn(options=["Administrador", "Capturista", "Consultor"]),
                    "Activo": st.column_config.CheckboxColumn()
                },
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("💾 Guardar Cambios en Usuarios", use_container_width=True):
                any_error = False
                for _, row in edited_df.iterrows():
                    user_id = row['ID']
                    username = row['Usuario']
                    password_plain = row['Contraseña']
                    nombre_completo = row['Nombre Completo']
                    email = row['Correo Electrónico']
                    rol = row['Rol']
                    activo = 1 if row['Activo'] else 0
                    
                    # Guardar cambios
                    succ1, msg1 = db.update_usuario_detalles(username, nombre_completo, email, rol)
                    succ2, msg2 = db.toggle_usuario_activo(user_id, activo)
                    
                    # Comparar con original para hashes de contraseña
                    original_row = df_u[df_u['id'] == user_id].iloc[0]
                    if original_row['password_plain'] != password_plain:
                        succ3, msg3 = db.cambiar_password(username, password_plain)
                        if not succ3:
                            st.error(f"Error al cambiar contraseña de {username}: {msg3}")
                            any_error = True
                            
                    if not succ1 or not succ2:
                        st.error(f"Error al actualizar {username}: {msg1 or msg2}")
                        any_error = True
                        
                if not any_error:
                    st.success("¡Usuarios actualizados con éxito!")
                    st.rerun()
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
                st.warning("Complete todos los campos del nuevo usuario.")


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
