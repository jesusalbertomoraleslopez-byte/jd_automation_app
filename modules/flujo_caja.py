import streamlit as st
import pandas as pd
import datetime
import os
import database as db
import modules.excel_handler as excel_h
import modules.pdf_generator as pdf_gen

def get_quincenas():
    """Genera 12 períodos quincenales (4 en el pasado, 1 actual, 7 en el futuro)."""
    today = datetime.date.today()
    quincenas = []
    
    current_half = 1 if today.day <= 15 else 2
    
    y = today.year
    m = today.month
    h = current_half
    
    # Retroceder 4 quincenas
    for _ in range(4):
        h -= 1
        if h == 0:
            h = 2
            m -= 1
            if m == 0:
                m = 12
                y -= 1
                
    # Generar 12 períodos consecutivos
    for _ in range(12):
        meses_es = {
            1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
            7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
        }
        label = f"{'01' if h == 1 else '16'}-{meses_es[m]}"
        
        if h == 1:
            start_date = datetime.date(y, m, 1)
            end_date = datetime.date(y, m, 15)
        else:
            start_date = datetime.date(y, m, 16)
            if m == 12:
                end_date = datetime.date(y+1, 1, 1) - datetime.timedelta(days=1)
            else:
                end_date = datetime.date(y, m+1, 1) - datetime.timedelta(days=1)
                
        quincenas.append({
            'label': label,
            'start': start_date,
            'end': end_date,
            'year': y,
            'month': m,
            'half': h
        })
        
        h += 1
        if h == 3:
            h = 1
            m += 1
            if m == 13:
                m = 1
                y += 1
                
    return quincenas

def calculate_cashflow_matrix(quincenas, saldo_inicial_caja):
    """Calcula los flujos de caja e históricos por períodos quincenales."""
    df_g_prog = db.get_gastos_programados_df()
    df_i_prog = db.get_ingresos_programados_df()
    df_backorder = db.get_backorders_df()
    df_gastos_reales = db.get_gastos_df()
    df_proy = db.get_proyectos()

    # Formatear fechas
    if not df_gastos_reales.empty:
        df_gastos_reales['fecha_dt'] = pd.to_datetime(df_gastos_reales['fecha'])
    if not df_backorder.empty:
        df_backorder['fecha_dt'] = pd.to_datetime(df_backorder['fecha_compromiso'])
    if not df_i_prog.empty:
        df_i_prog['fecha_dt'] = pd.to_datetime(df_i_prog['fecha_esperada'])
    if not df_g_prog.empty:
        df_g_prog['fecha_dt'] = pd.to_datetime(df_g_prog['fecha_compromiso'])

    # Definir filas de la matriz
    inflow_rows = []
    if not df_proy.empty:
        for _, row in df_proy.iterrows():
            inflow_rows.append(f"💼 [{row['codigo']}] {row['nombre']}")
    inflow_rows.append("📥 Otros Ingresos / Ventas")

    outflow_rows = [
        "👥 Nómina Operativa J&D",
        "🏛️ SAT - Impuestos",
        "🏥 IMSS / Infonavit",
        "🔧 Proveedores (Backorder OCs)",
        "⚡ Servicios & Operación",
        "⛽ Combustibles (Gasolina)",
        "📦 Otros Egresos"
    ]

    all_rows = inflow_rows + outflow_rows
    col_labels = [q['label'] for q in quincenas]

    # Matrices de valores y estados
    df_values = pd.DataFrame(0.0, index=all_rows, columns=col_labels)
    df_status = pd.DataFrame('Ninguno', index=all_rows, columns=col_labels)

    for q in quincenas:
        lbl = q['label']
        start = pd.to_datetime(q['start'])
        end = pd.to_datetime(q['end'])

        # ─── 1. Procesar Ingresos Programados ───
        if not df_i_prog.empty:
            mask = (df_i_prog['fecha_dt'] >= start) & (df_i_prog['fecha_dt'] <= end)
            q_inflows = df_i_prog[mask]
            
            for _, row in q_inflows.iterrows():
                p_id = row['proyecto_id']
                monto = row['monto']
                status = row['estado']
                
                # Encontrar fila del proyecto
                proj_row = "📥 Otros Ingresos / Ventas"
                if pd.notna(p_id) and not df_proy.empty:
                    p_match = df_proy[df_proy['id'] == p_id]
                    if not p_match.empty:
                        proj_row = f"💼 [{p_match.iloc[0]['codigo']}] {p_match.iloc[0]['nombre']}"
                
                if proj_row in df_values.index:
                    df_values.loc[proj_row, lbl] += monto
                    # Estado: si hay múltiples se conserva 'Cobrado' si todo está cobrado, o 'Pendiente' si hay pendientes
                    current_status = df_status.loc[proj_row, lbl]
                    if current_status == 'Ninguno':
                        df_status.loc[proj_row, lbl] = status
                    elif current_status == 'Cobrado' and status == 'Pendiente':
                        df_status.loc[proj_row, lbl] = 'Pendiente'

        # ─── 2. Procesar Egresos ───
        # Mapeo de categorías
        cat_map = {
            'Nómina': "👥 Nómina Operativa J&D",
            'SAT': "🏛️ SAT - Impuestos",
            'IMSS': "🏥 IMSS / Infonavit",
            'Infonavit': "🏥 IMSS / Infonavit",
            'Servicios': "⚡ Servicios & Operación",
            'Gasolina': "⛽ Combustibles (Gasolina)",
            'Otros': "📦 Otros Egresos"
        }

        # 2a. Gastos Reales (Históricos) - Siempre 'Pagado'
        if not df_gastos_reales.empty:
            mask = (df_gastos_reales['fecha_dt'] >= start) & (df_gastos_reales['fecha_dt'] <= end)
            q_real = df_gastos_reales[mask]
            for _, row in q_real.iterrows():
                monto = row['monto_neto']
                rubro = row['rubro']
                
                # Mapear rubro a fila
                row_name = "📦 Otros Egresos"
                for cat_key, target_row in cat_map.items():
                    if rubro and cat_key.lower() in rubro.lower():
                        row_name = target_row
                        break
                        
                df_values.loc[row_name, lbl] += monto
                df_status.loc[row_name, lbl] = 'Pagado'

        # 2b. Gastos Fijos Programados
        if not df_g_prog.empty:
            mask = (df_g_prog['fecha_dt'] >= start) & (df_g_prog['fecha_dt'] <= end)
            q_fixed = df_g_prog[mask]
            for _, row in q_fixed.iterrows():
                monto = row['monto']
                cat = row['categoria']
                status = row['estado']
                
                # Si el estado es 'Pagado', ya se sumó en Gastos Reales
                if status == 'Pagado':
                    continue
                    
                row_name = "📦 Otros Egresos"
                if cat in cat_map:
                    row_name = cat_map[cat]
                    
                df_values.loc[row_name, lbl] += monto
                
                current_status = df_status.loc[row_name, lbl]
                if current_status in ('Ninguno', 'Pagado') and status == 'Pendiente':
                    df_status.loc[row_name, lbl] = 'Pendiente'

        # 2c. Backorder OCs
        if not df_backorder.empty:
            mask = (df_backorder['fecha_dt'] >= start) & (df_backorder['fecha_dt'] <= end)
            q_bo = df_backorder[mask]
            row_name = "🔧 Proveedores (Backorder OCs)"
            for _, row in q_bo.iterrows():
                monto = row['monto_oc']
                status = row['estado']  # 'Pendiente' o 'Pagado'
                
                df_values.loc[row_name, lbl] += monto
                current_status = df_status.loc[row_name, lbl]
                
                if status == 'Pendiente':
                    df_status.loc[row_name, lbl] = 'Pendiente'
                elif current_status == 'Ninguno' and status == 'Pagado':
                    df_status.loc[row_name, lbl] = 'Pagado'

    return df_values, df_status, inflow_rows, outflow_rows

def render_flujo_caja_modulo():
    tab_matrix, tab_exec, tab_export, tab_setup = st.tabs([
        "📊 3.1 Matriz de Flujo Quincenal",
        "⚡ 3.2 Ejecutar Gastos Planeados",
        "📥 3.3 Exportar Excel de Flujo",
        "⚙️ 3.4 Programación General"
    ])

    quincenas = get_quincenas()

    # Saldo Inicial configurable
    df_accounts = db.get_cuentas()
    saldo_inicial_real = 500000.0  # Default premium

    # ─── TAB 3.1: MATRIZ DE FLUJO ───
    with tab_matrix:
        st.markdown("### **Matriz de Movimientos Financieros (Vista Quincenal)**")
        st.markdown("Las celdas <span style='color:#155724;background-color:#D4EDDA;padding:2px 5px;border-radius:3px;font-weight:bold;'>Verdes</span> indican transacciones reales/ejecutadas, mientras que las <span style='color:#721C24;background-color:#F8D7DA;padding:2px 5px;border-radius:3px;'>Rosas</span> corresponden a compromisos pendientes.", unsafe_allow_html=True)
        
        col_init, col_empty = st.columns([1, 2])
        with col_init:
            saldo_inicial = st.number_input(
                "💰 Saldo Inicial de Caja (Bancos)",
                min_value=0.0,
                value=float(saldo_inicial_real),
                step=10000.0,
                key="matrix_init_bal"
            )

        df_values, df_status, inflow_rows, outflow_rows = calculate_cashflow_matrix(quincenas, saldo_inicial)

        # Agregar filas calculadas
        total_entradas = df_values.loc[inflow_rows].sum()
        total_salidas = df_values.loc[outflow_rows].sum()
        balance = total_entradas - total_salidas

        # Calcular saldos acumulados
        saldo_acumulado = []
        caja_corr = saldo_inicial
        for b_val in balance:
            caja_corr += b_val
            saldo_acumulado.append(caja_corr)

        # Construir DataFrames finales para visualización
        df_vals_disp = df_values.copy()
        df_vals_disp.loc['TOTAL ENTRADAS'] = total_entradas
        df_vals_disp.loc['TOTAL SALIDAS'] = total_salidas
        df_vals_disp.loc['BALANCE (NETO)'] = balance
        df_vals_disp.loc['SALDO ACUMULADO'] = saldo_acumulado

        # Asignar estados de filas de totales
        df_status_disp = df_status.copy()
        df_status_disp.loc['TOTAL ENTRADAS'] = 'Ninguno'
        df_status_disp.loc['TOTAL SALIDAS'] = 'Ninguno'
        df_status_disp.loc['BALANCE (NETO)'] = 'Ninguno'
        df_status_disp.loc['SALDO ACUMULADO'] = 'Ninguno'

        # Dar formato de moneda
        df_format = df_vals_disp.copy()
        
        # Pandas Styler para colorear celdas según estado
        def style_cells(data):
            styles = pd.DataFrame('', index=data.index, columns=data.columns)
            for col in data.columns:
                for idx in data.index:
                    status = df_status_disp.loc[idx, col]
                    val = df_vals_disp.loc[idx, col]
                    
                    if idx in ('TOTAL ENTRADAS', 'TOTAL SALIDAS', 'BALANCE (NETO)'):
                        styles.loc[idx, col] = 'background-color: #F2F2F2; font-weight: bold; border-top: 1px solid #CCCCCC;'
                    elif idx == 'SALDO ACUMULADO':
                        if val >= 0:
                            styles.loc[idx, col] = 'background-color: #E2F0D9; font-weight: bold; border-top: 1px solid #000000; border-bottom: 2px double #000000;'
                        else:
                            styles.loc[idx, col] = 'background-color: #FCE4D6; font-weight: bold; border-top: 1px solid #000000; border-bottom: 2px double #000000; color: #C00000;'
                    else:
                        if val > 0:
                            if status in ('Cobrado', 'Pagado'):
                                styles.loc[idx, col] = 'background-color: #D4EDDA; color: #155724; font-weight: bold;'
                            elif status == 'Pendiente':
                                styles.loc[idx, col] = 'background-color: #F8D7DA; color: #721C24;'
            return styles

        st.dataframe(
            df_format.style.apply(style_cells, axis=None).format('${:,.2f}'),
            use_container_width=True,
            height=500
        )

        # Alertas de flujo
        for q_idx, q in enumerate(quincenas):
            if saldo_acumulado[q_idx] < 0:
                st.error(f"⚠️ **Alerta de Flujo:** Se estima un saldo de caja deficitario de **${saldo_acumulado[q_idx]:,.2f} MXN** para la quincena **{q['label']}**. Planifique cobranzas o postergue egresos.")

    # ─── TAB 3.2: EJECUTAR GASTOS PLANEADOS ───
    with tab_exec:
        st.markdown("### **Ejecutar Gastos Planeados (Pasar a Real)**")
        st.markdown("Seleccione un gasto programado de la lista de pendientes, asocie la cuenta bancaria de retiro, el método de pago y ejecútelo oficialmente en la base de datos de egresos.")

        df_pending = db.get_gastos_programados_df()
        if not df_pending.empty:
            df_pending = df_pending[df_pending['estado'] == 'Pendiente']

        if not df_pending.empty:
            df_pending['monto_disp'] = df_pending.apply(lambda r: f"{r['concepto']} — ${r['monto']:,.2f} (Fecha: {r['fecha_compromiso']})", axis=1)
            
            selected_option = st.selectbox("Seleccione el Gasto Programado a Ejecutar", df_pending['monto_disp'].tolist())
            selected_row = df_pending[df_pending['monto_disp'] == selected_option].iloc[0]
            
            st.markdown("---")
            st.markdown("#### **Detalles de la Transacción Real**")
            
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                ex_fecha = st.date_input("Fecha de Pago Real", datetime.date.today())
                ex_concepto = st.text_input("Concepto Real", value=str(selected_row['concepto']))
                ex_monto = st.number_input("Monto Neto Cobrado (IVA Incluido)", value=float(selected_row['monto']), min_value=0.01, step=100.0, format="%.2f")
            
            with col_ex2:
                ex_metodo = st.selectbox("Método de Pago Efectuado", ["Tarjeta de Crédito", "Transferencia Bancaria", "Efectivo"])
                
                # Filtrar cuentas asociadas al método
                df_accounts_ex = db.get_cuentas()
                df_accounts_ex_filtered = df_accounts_ex[df_accounts_ex['tipo'] == ex_metodo]
                
                if not df_accounts_ex_filtered.empty:
                    ex_cuenta_name = st.selectbox("Cuenta / Tarjeta de Cargo", df_accounts_ex_filtered['nombre'].tolist())
                    ex_cuenta_row = df_accounts_ex_filtered[df_accounts_ex_filtered['nombre'] == ex_cuenta_name].iloc[0]
                    ex_cuenta_id = ex_cuenta_row['id']
                else:
                    ex_cuenta_id = None
                    st.warning(f"No hay cuentas configuradas para el método: {ex_metodo}. Regístrelas en Inicio → Cuentas.")
            
            col_ex3, col_ex4 = st.columns(2)
            with col_ex3:
                ex_deducible = st.selectbox("¿Deducible / Facturable?", ["Sí", "No"])
                ex_estado_fact = st.selectbox("Estatus de Facturación", ["Facturado", "Pendiente"])
                
            if st.button("🚀 Ejecutar y Registrar Gasto Oficialmente", use_container_width=True):
                if ex_cuenta_id:
                    # 1. Crear gasto real
                    success, insert_id = db.add_gasto(
                        fecha=ex_fecha.strftime('%Y-%m-%d'),
                        concepto=ex_concepto,
                        monto_neto=ex_monto,
                        rubro=selected_row['categoria'],
                        subrubro='Gastos Fijos Programados',
                        concepto_detallado=selected_row['concepto'],
                        proyecto_id=None,
                        deducible=ex_deducible,
                        estado_facturacion=ex_estado_fact,
                        metodo_pago=ex_metodo,
                        cuenta_id=ex_cuenta_id,
                        rfc_proveedor=None,
                        uuid_fiscal=None
                    )
                    
                    if success:
                        # 2. Generar PDF de respaldo obligatorio
                        gasto_pdf_info = {
                            'id': insert_id,
                            'fecha': ex_fecha.strftime('%Y-%m-%d'),
                            'concepto': ex_concepto,
                            'monto_neto': ex_monto,
                            'proyecto_nombre': 'Gastos Generales / Fijos',
                            'metodo_pago': ex_metodo,
                            'cuenta_nombre': ex_cuenta_name,
                            'rubro': selected_row['categoria'],
                            'subrubro': 'Gastos Fijos Programados',
                            'concepto_detallado': selected_row['concepto'],
                            'deducible': ex_deducible,
                            'estado_facturacion': ex_estado_fact,
                            'rfc_proveedor': None,
                            'uuid_fiscal': None
                        }
                        
                        pdf_bytes = pdf_gen.generar_pdf_gasto(gasto_pdf_info)
                        local_pdf_name = f"recibo_gasto_{insert_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                        
                        COMPROBANTES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'comprobantes')
                        os.makedirs(COMPROBANTES_DIR, exist_ok=True)
                        
                        with open(os.path.join(COMPROBANTES_DIR, local_pdf_name), "wb") as f:
                            f.write(pdf_bytes)
                            
                        db.update_gasto(insert_id, pdf_filename=local_pdf_name)
                        
                        # 3. Marcar programado como 'Pagado'
                        db.update_gasto_programado_row(
                            gasto_id=selected_row['id'],
                            concepto=selected_row['concepto'],
                            monto=selected_row['monto'],
                            fecha_compromiso=selected_row['fecha_compromiso'],
                            categoria=selected_row['categoria'],
                            recurrente=selected_row['recurrente'],
                            frecuencia=selected_row['frecuencia'],
                            estado='Pagado'
                        )
                        
                        st.success(f"🎉 Gasto ejecutado y guardado con éxito. ID Real: {insert_id}.")
                        st.session_state['last_pdf_bytes'] = pdf_bytes
                        st.session_state['last_pdf_name'] = local_pdf_name
                        st.session_state['gasto_guardado_exito'] = True
                        st.rerun()
                    else:
                        st.error(f"Error al registrar gasto: {insert_id}")
                else:
                    st.error("Debe seleccionar una cuenta de cargo válida.")
        else:
            st.info("No hay gastos programados pendientes por ejecutar.")

    # ─── TAB 3.3: EXPORTAR EXCEL DE FLUJO ───
    with tab_export:
        st.markdown("### **Descargar Reporte Quincenal Formateado**")
        st.markdown("Obtenga el archivo de Excel completamente estilizado. Cuenta con formato condicional de colores (verde y rosa), subtotales y fórmulas incorporadas de forma automática.")
        
        try:
            df_values_e, df_status_e, _, _ = calculate_cashflow_matrix(quincenas, saldo_inicial_real)
            
            excel_bytes = excel_h.export_cashflow_matrix_excel(
                quincenas=quincenas,
                row_names=df_values_e.index.tolist(),
                df_values=df_values_e,
                df_status=df_status_e,
                saldo_inicial=saldo_inicial_real
            )
            
            st.download_button(
                label="📥 Descargar Flujo de Caja Corporativo J&D (.xlsx)",
                data=excel_bytes,
                file_name=f"Flujo_de_Caja_JD_Automation_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success("¡Archivo listo para descarga!")
        except Exception as e:
            st.error(f"Error al estructurar el Excel: {str(e)}")

    # ─── TAB 3.4: PROGRAMACIÓN GENERAL ───
    with tab_setup:
        st.markdown("### **Mantenimiento y Registro de Plantillas Financieras**")
        
        df_g_prog = db.get_gastos_programados_df()
        df_i_prog = db.get_ingresos_programados_df()
        
        tab_egresos_p, tab_ingresos_p = st.tabs(["📤 Egresos Fijos Recurrentes", "📥 Ingresos de Clientes (Hitos)"])
        
        with tab_egresos_p:
            col_eg1, col_eg2 = st.columns([1, 2])
            
            with col_eg1:
                st.markdown("#### **Registrar Plantilla de Salida**")
                with st.form("form_add_gasto_p"):
                    concepto_g = st.text_input("Concepto / Servicio", placeholder="Ej. Renta Oficina Monterrey")
                    monto_g = st.number_input("Monto Estimado", min_value=0.01, step=100.0, format="%.2f")
                    fecha_g = st.date_input("Fecha Límite / Compromiso", datetime.date.today())
                    categoria_g = st.selectbox("Rubro", ["Nómina", "Servicios", "SAT", "IMSS", "Infonavit", "Gasolina", "Otros"])
                    recurrente_g = st.checkbox("Gasto mensual recurrente", value=True)
                    frecuencia_g = st.selectbox("Frecuencia de Pago", ["Mensual", "Bimestral", "Única"])
                    
                    submit_g = st.form_submit_button("Programar Gasto")
                    if submit_g:
                        if concepto_g:
                            rec_val = 1 if recurrente_g else 0
                            succ, msg = db.insert_gasto_programado(
                                concepto=concepto_g,
                                monto=monto_g,
                                fecha_compromiso=fecha_g.strftime('%Y-%m-%d'),
                                categoria=categoria_g,
                                recurrente=rec_val,
                                frecuencia=frecuencia_g,
                                estado='Pendiente'
                            )
                            if succ:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("El concepto es obligatorio.")
                            
            with col_eg2:
                st.markdown("#### **Editar Gastos Programados**")
                if not df_g_prog.empty:
                    df_g_prog_disp = df_g_prog.copy()
                    df_g_prog_disp['recurrente'] = df_g_prog_disp['recurrente'].map({1: True, 0: False})
                    df_g_prog_disp['Eliminar'] = False
                    df_g_prog_disp.columns = ['ID', 'Concepto', 'Monto', 'Fecha Compromiso', 'Categoría', 'Recurrente', 'Frecuencia', 'Estado', 'Eliminar']
                    
                    edited_g = st.data_editor(
                        df_g_prog_disp,
                        column_config={
                            "ID": st.column_config.NumberColumn(disabled=True),
                            "Monto": st.column_config.NumberColumn(format="$%.2f"),
                            "Recurrente": st.column_config.CheckboxColumn(),
                            "Categoría": st.column_config.SelectboxColumn(options=["Nómina", "Servicios", "SAT", "IMSS", "Infonavit", "Gasolina", "Otros"]),
                            "Frecuencia": st.column_config.SelectboxColumn(options=["Mensual", "Bimestral", "Única"]),
                            "Estado": st.column_config.SelectboxColumn(options=["Pendiente", "Pagado"]),
                            "Eliminar": st.column_config.CheckboxColumn()
                        },
                        use_container_width=True,
                        hide_index=True,
                        key="editor_gastos_prog"
                    )
                    
                    if st.button("💾 Guardar Cambios en Egresos"):
                        for _, row in edited_g.iterrows():
                            g_id = row['ID']
                            if row['Eliminar']:
                                db.delete_gasto_programado(g_id)
                            else:
                                rec_int = 1 if row['Recurrente'] else 0
                                db.update_gasto_programado_row(
                                    gasto_id=g_id,
                                    concepto=row['Concepto'],
                                    monto=row['Monto'],
                                    fecha_compromiso=row['Fecha Compromiso'],
                                    categoria=row['Categoría'],
                                    recurrente=rec_int,
                                    frecuencia=row['Frecuencia'],
                                    estado=row['Estado']
                                )
                        st.success("Cambios guardados con éxito.")
                        st.rerun()
                else:
                    st.info("No hay gastos programados.")
                    
        with tab_ingresos_p:
            col_in1, col_in2 = st.columns([1, 2])
            
            with col_in1:
                st.markdown("#### **Registrar Cobro / Venta**")
                df_p_activos = db.get_proyectos(only_active=True)
                with st.form("form_add_ingreso_p"):
                    concepto_i = st.text_input("Concepto del Ingreso", placeholder="Ej. Cobro Hito 3 - PLC")
                    monto_i = st.number_input("Monto de Entrada", min_value=0.01, step=100.0, format="%.2f")
                    fecha_i = st.date_input("Fecha Proyectada", datetime.date.today())
                    
                    if not df_p_activos.empty:
                        proj_opts = dict(zip('[' + df_p_activos['codigo'] + '] ' + df_p_activos['nombre'], df_p_activos['id']))
                        proj_name_i = st.selectbox("Asociar a Proyecto", ["— Venta General —"] + list(proj_opts.keys()))
                        proj_id_i = proj_opts[proj_name_i] if proj_name_i != "— Venta General —" else None
                    else:
                        proj_id_i = None
                        st.info("No hay proyectos activos registrados.")
                        
                    submit_i = st.form_submit_button("Programar Ingreso")
                    if submit_i:
                        if concepto_i:
                            succ, msg = db.insert_ingreso_programado(
                                proyecto_id=proj_id_i,
                                concepto=concepto_i,
                                monto=monto_i,
                                fecha_esperada=fecha_i.strftime('%Y-%m-%d'),
                                estado='Pendiente'
                            )
                            if succ:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("El concepto es obligatorio.")
                            
            with col_in2:
                st.markdown("#### **Editar Ingresos Programados**")
                if not df_i_prog.empty:
                    df_i_prog_disp = df_i_prog.copy()
                    df_i_prog_disp['Eliminar'] = False
                    df_i_prog_disp.columns = ['ID', 'ProyectoID', 'Proyecto', 'Concepto', 'Monto', 'Fecha Esperada', 'Estado', 'Eliminar']
                    
                    edited_i = st.data_editor(
                        df_i_prog_disp,
                        column_config={
                            "ID": st.column_config.NumberColumn(disabled=True),
                            "ProyectoID": st.column_config.NumberColumn(disabled=True),
                            "Proyecto": st.column_config.TextColumn(disabled=True),
                            "Monto": st.column_config.NumberColumn(format="$%.2f"),
                            "Estado": st.column_config.SelectboxColumn(options=["Pendiente", "Cobrado"]),
                            "Eliminar": st.column_config.CheckboxColumn()
                        },
                        use_container_width=True,
                        hide_index=True,
                        key="editor_ingresos_prog"
                    )
                    
                    if st.button("💾 Guardar Cambios en Ingresos"):
                        for _, row in edited_i.iterrows():
                            i_id = row['ID']
                            if row['Eliminar']:
                                db.delete_ingreso_programado(i_id)
                            else:
                                db.update_ingreso_programado_row(
                                    ingreso_id=i_id,
                                    proyecto_id=row['ProyectoID'] if pd.notna(row['ProyectoID']) else None,
                                    concepto=row['Concepto'],
                                    monto=row['Monto'],
                                    fecha_esperada=row['Fecha Esperada'],
                                    estado=row['Estado']
                                )
                        st.success("Cambios guardados con éxito.")
                        st.rerun()
                else:
                    st.info("No hay ingresos programados.")
