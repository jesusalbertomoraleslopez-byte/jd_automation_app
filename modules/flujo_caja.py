import streamlit as st
import pandas as pd
import datetime
import database as db

def render_flujo_caja_tab():
    st.subheader("Flujo de Caja Proyectado a 3 Meses")
    st.markdown(
        "Proyecte la salud financiera de la empresa integrando ingresos programados, gastos de operación fijos y facturación en backorder."
    )

    # 1. Obtener Saldo Inicial Predeterminado
    saldo_inicial_real = 500000.0

    col_init_bal, col_space = st.columns([1, 2])
    with col_init_bal:
        saldo_inicial_caja = st.number_input(
            "💰 Saldo Inicial de Caja (Efectivo disponible)",
            min_value=0.0,
            value=float(saldo_inicial_real),
            step=10000.0,
            help="Suma inicial estimada de efectivo disponible en bancos y caja."
        )

    # 2. Calcular Periodos Mensuales
    today = datetime.date.today()
    months = []
    for i in range(4):  # Mes actual + 3 meses a futuro
        year = today.year + (today.month + i - 1) // 12
        month = (today.month + i - 1) % 12 + 1
        months.append((year, month))

    # Obtener catálogos desde la base de datos
    df_g_prog = db.get_gastos_programados_df()
    df_i_prog = db.get_ingresos_programados_df()
    df_backorder = db.get_backorders_df()
    df_gastos_reales = db.get_gastos_df()

    # Formatear fechas de gastos reales y backorder para filtrado fácil
    if not df_gastos_reales.empty:
        df_gastos_reales['fecha_dt'] = pd.to_datetime(df_gastos_reales['fecha'])
    if not df_backorder.empty:
        df_backorder['fecha_dt'] = pd.to_datetime(df_backorder['fecha_compromiso'])

    # Estructura para almacenar resultados del Cash Flow
    projection_data = []
    
    saldo_acumulado = saldo_inicial_caja
    
    chart_data_list = []

    for year, month in months:
        month_name = datetime.date(year, month, 1).strftime('%B %Y').capitalize()
        # Mapeo a español rápido
        months_es = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
            'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
            'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        for eng, esp in months_es.items():
            if eng in month_name:
                month_name = month_name.replace(eng, esp)

        # ─── INFLOWS (INGRESOS) ───
        # Ingresos programados en este periodo (Cobrados o Pendientes)
        inflows = 0.0
        if not df_i_prog.empty:
            df_i_prog['fecha_dt'] = pd.to_datetime(df_i_prog['fecha_esperada'])
            mask = (df_i_prog['fecha_dt'].dt.year == year) & (df_i_prog['fecha_dt'].dt.month == month)
            inflows = df_i_prog[mask]['monto'].sum()

        # ─── OUTFLOWS (EGRESOS) ───
        # 1. Gastos Reales (Registrados en la operación diaria)
        real_outflows = 0.0
        if not df_gastos_reales.empty:
            mask = (df_gastos_reales['fecha_dt'].dt.year == year) & (df_gastos_reales['fecha_dt'].dt.month == month)
            real_outflows = df_gastos_reales[mask]['monto_neto'].sum()

        # 2. Gastos Fijos/Recurrentes Programados (Solo los Pendientes del periodo)
        fixed_outflows = 0.0
        if not df_g_prog.empty:
            df_g_prog['fecha_dt'] = pd.to_datetime(df_g_prog['fecha_compromiso'])
            mask = (df_g_prog['fecha_dt'].dt.year == year) & (df_g_prog['fecha_dt'].dt.month == month) & (df_g_prog['estado'] == 'Pendiente')
            fixed_outflows = df_g_prog[mask]['monto'].sum()

        # 3. Backorder OCs (Solo las Pendientes del periodo)
        backorder_outflows = 0.0
        if not df_backorder.empty:
            mask = (df_backorder['fecha_dt'].dt.year == year) & (df_backorder['fecha_dt'].dt.month == month) & (df_backorder['estado'] == 'Pendiente')
            backorder_outflows = df_backorder[mask]['monto_oc'].sum()

        total_outflows = real_outflows + fixed_outflows + backorder_outflows
        net_flow = inflows - total_outflows
        
        saldo_inicial_periodo = saldo_acumulado
        saldo_final_periodo = saldo_inicial_periodo + net_flow
        saldo_acumulado = saldo_final_periodo  # Pasa al siguiente mes

        projection_data.append({
            "Periodo": month_name,
            "Saldo Inicial": saldo_inicial_periodo,
            "(+) Ingresos Programados": inflows,
            "(-) Gastos Reales": real_outflows,
            "(-) Gastos Fijos Programados": fixed_outflows,
            "(-) Backorder OCs": backorder_outflows,
            "(=) Saldo Final Estimado": saldo_final_periodo
        })
        
        chart_data_list.append({
            "Periodo": month_name,
            "Entradas": inflows,
            "Salidas": total_outflows
        })

    # Mostrar KPIs de la Proyección
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    total_ingresos_proy = sum(x['(+) Ingresos Programados'] for x in projection_data[1:])
    total_egresos_proy = sum(x['(-) Gastos Fijos Programados'] + x['(-) Backorder OCs'] for x in projection_data[1:])
    saldo_final_proy = projection_data[-1]['(=) Saldo Final Estimado']
    
    col_kpi1.metric("Caja Inicial", f"${saldo_inicial_caja:,.2f}")
    col_kpi2.metric("Ingresos Esperados (3m)", f"${total_ingresos_proy:,.2f}")
    col_kpi3.metric("Egresos Programados (3m)", f"${total_egresos_proy:,.2f}")
    
    if saldo_final_proy >= 0:
        col_kpi4.metric("Saldo Estimado Final", f"${saldo_final_proy:,.2f}", delta="Superávit", delta_color="normal")
    else:
        col_kpi4.metric("Saldo Estimado Final", f"${saldo_final_proy:,.2f}", delta="Déficit de Flujo", delta_color="inverse")

    st.markdown("---")
    
    # ─── SECCIÓN 1: PROYECCIÓN FINANCIERA ───
    st.markdown("### **1. Tabla Comparativa de Proyección Mensual**")
    
    # Formatear la tabla de Cash Flow
    df_proj = pd.DataFrame(projection_data)
    df_proj_display = df_proj.copy()
    
    currency_cols = [
        "Saldo Inicial", "(+) Ingresos Programados", "(-) Gastos Reales", 
        "(-) Gastos Fijos Programados", "(-) Backorder OCs", "(=) Saldo Final Estimado"
    ]
    for col in currency_cols:
        df_proj_display[col] = df_proj_display[col].map('${:,.2f}'.format)
        
    st.dataframe(df_proj_display, use_container_width=True, hide_index=True)
    
    # Alertar sobre déficit de flujo
    for row in projection_data:
        if row['(=) Saldo Final Estimado'] < 0:
            st.error(f"⚠️ **Alerta de Caja:** Se estima un déficit de caja en **{row['Periodo']}** (Saldo final estimado: **${row['(=) Saldo Final Estimado']:,.2f} MXN**). Planifique cobranzas o postergue egresos.")

    # Gráfico de barras de Entradas vs Salidas
    st.markdown("### **Entradas vs Salidas por Periodo**")
    df_chart = pd.DataFrame(chart_data_list)
    df_chart_melted = df_chart.set_index('Periodo')
    st.bar_chart(df_chart_melted, use_container_width=True)

    st.markdown("---")

    # ─── SECCIÓN 2: EGRESOS FIJOS / RECURRENTES ───
    st.markdown("### **2. Programación de Egresos Fijos / Recurrentes (OpEx)**")
    
    col_add_g, col_list_g = st.columns([1, 2])
    
    with col_add_g:
        st.markdown("#### **Registrar Gasto Fijo / Recurrente**")
        with st.form("add_fixed_expense_form"):
            g_concepto = st.text_input("Concepto del Gasto", placeholder="Ej. Pago de Nómina, Renta, etc.")
            g_monto = st.number_input("Monto Neto (IVA Incluido)", min_value=0.01, step=100.0, format="%.2f")
            g_fecha = st.date_input("Fecha de Compromiso de Pago", datetime.date.today())
            g_categoria = st.selectbox("Categoría del Gasto", ["Nómina", "Servicios", "SAT", "IMSS", "Infonavit", "Gasolina", "Otros"])
            g_recurrente = st.checkbox("¿Es gasto recurrente?", value=True)
            g_frecuencia = st.selectbox("Frecuencia", ["Mensual", "Bimestral", "Única"])
            
            submit_g = st.form_submit_button("Guardar Programación")
            if submit_g:
                if g_concepto:
                    recurrente_val = 1 if g_recurrente else 0
                    success, msg = db.insert_gasto_programado(
                        concepto=g_concepto,
                        monto=g_monto,
                        fecha_compromiso=g_fecha.strftime('%Y-%m-%d'),
                        categoria=g_categoria,
                        recurrente=recurrente_val,
                        frecuencia=g_frecuencia,
                        estado='Pendiente'
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Ingrese el concepto del gasto.")

    with col_list_g:
        st.markdown("#### **Lista de Gastos Programados**")
        st.markdown("Modifique montos, fechas o marque como **Pagado** directamente en la tabla y presione guardar.")
        if not df_g_prog.empty:
            df_g_prog_disp = df_g_prog.copy()
            df_g_prog_disp['recurrente'] = df_g_prog_disp['recurrente'].map({1: True, 0: False})
            df_g_prog_disp['Eliminar'] = False
            df_g_prog_disp.columns = ['ID', 'Concepto', 'Monto', 'Fecha Compromiso', 'Categoría', 'Recurrente', 'Frecuencia', 'Estado', 'Eliminar']
            
            edited_g_df = st.data_editor(
                df_g_prog_disp,
                column_config={
                    "ID": st.column_config.NumberColumn(disabled=True),
                    "Concepto": st.column_config.TextColumn(),
                    "Monto": st.column_config.NumberColumn(format="$%.2f"),
                    "Fecha Compromiso": st.column_config.TextColumn(),
                    "Categoría": st.column_config.SelectboxColumn(options=["Nómina", "Servicios", "SAT", "IMSS", "Infonavit", "Gasolina", "Otros"]),
                    "Recurrente": st.column_config.CheckboxColumn(),
                    "Frecuencia": st.column_config.SelectboxColumn(options=["Mensual", "Bimestral", "Única"]),
                    "Estado": st.column_config.SelectboxColumn(options=["Pendiente", "Pagado"]),
                    "Eliminar": st.column_config.CheckboxColumn()
                },
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("💾 Guardar Cambios en Gastos Programados", use_container_width=True):
                any_error = False
                for _, row in edited_g_df.iterrows():
                    g_id = row['ID']
                    if row['Eliminar']:
                        db.delete_gasto_programado(g_id)
                    else:
                        recurrente_int = 1 if row['Recurrente'] else 0
                        db.update_gasto_programado_row(
                            gasto_id=g_id,
                            concepto=row['Concepto'],
                            monto=row['Monto'],
                            fecha_compromiso=row['Fecha Compromiso'],
                            categoria=row['Categoría'],
                            recurrente=recurrente_int,
                            frecuencia=row['Frecuencia'],
                            estado=row['Estado']
                        )
                st.success("¡Gastos programados actualizados!")
                st.rerun()
        else:
            st.info("No hay gastos programados.")

    st.markdown("---")

    # ─── SECCIÓN 3: INGRESOS / COBRANZAS ───
    st.markdown("### **3. Programación de Ingresos (Cobranzas de Proyectos & Ventas)**")
    
    col_add_i, col_list_i = st.columns([1, 2])
    
    with col_add_i:
        st.markdown("#### **Registrar Ingreso Proyectado**")
        df_p_activos = db.get_proyectos(only_active=True)
        
        with st.form("add_project_income_form"):
            i_concepto = st.text_input("Concepto del Ingreso", placeholder="Ej. Anticipo 50% Proyecto")
            i_monto = st.number_input("Monto de Ingreso", min_value=0.01, step=1000.0, format="%.2f")
            i_fecha = st.date_input("Fecha Esperada de Cobro", datetime.date.today())
            
            # Selector de proyectos activos
            if not df_p_activos.empty:
                proyecto_options_i = dict(zip('[' + df_p_activos['codigo'] + '] ' + df_p_activos['nombre'], df_p_activos['id']))
                i_proy_name = st.selectbox("Asociar a Proyecto (Opcional)", ["— Venta General —"] + list(proyecto_options_i.keys()))
                i_proy_id = proyecto_options_i[i_proy_name] if i_proy_name != "— Venta General —" else None
            else:
                i_proy_id = None
                st.info("No hay proyectos activos registrados.")
                
            submit_i = st.form_submit_button("Guardar Ingreso")
            if submit_i:
                if i_concepto:
                    success, msg = db.insert_ingreso_programado(
                        proyecto_id=i_proy_id,
                        concepto=i_concepto,
                        monto=i_monto,
                        fecha_esperada=i_fecha.strftime('%Y-%m-%d'),
                        estado='Pendiente'
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Ingrese el concepto del ingreso.")

    with col_list_i:
        st.markdown("#### **Lista de Ingresos Proyectados**")
        st.markdown("Modifique montos, fechas o marque como **Cobrado** directamente en la tabla y presione guardar.")
        if not df_i_prog.empty:
            df_i_prog_disp = df_i_prog.copy()
            df_i_prog_disp['Eliminar'] = False
            df_i_prog_disp.columns = ['ID', 'ProyectoID', 'Proyecto Asociado', 'Concepto', 'Monto', 'Fecha Esperada', 'Estado', 'Eliminar']
            
            edited_i_df = st.data_editor(
                df_i_prog_disp,
                column_config={
                    "ID": st.column_config.NumberColumn(disabled=True),
                    "ProyectoID": st.column_config.NumberColumn(disabled=True),
                    "Proyecto Asociado": st.column_config.TextColumn(disabled=True),
                    "Concepto": st.column_config.TextColumn(),
                    "Monto": st.column_config.NumberColumn(format="$%.2f"),
                    "Fecha Esperada": st.column_config.TextColumn(),
                    "Estado": st.column_config.SelectboxColumn(options=["Pendiente", "Cobrado"]),
                    "Eliminar": st.column_config.CheckboxColumn()
                },
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("💾 Guardar Cambios en Ingresos Programados", use_container_width=True):
                for _, row in edited_i_df.iterrows():
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
                st.success("¡Ingresos programados actualizados!")
                st.rerun()
        else:
            st.info("No hay ingresos programados.")
