import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_gastos_dashboard(df_gastos):
    """
    Renderiza los gráficos de Plotly para el análisis de Gastos.
    """
    if df_gastos.empty:
        st.info("No hay datos de gastos registrados para mostrar gráficas.")
        return

    # Convertir fecha a datetime para filtros y ordenamiento
    df_gastos['fecha_dt'] = pd.to_datetime(df_gastos['fecha'])
    
    # 1. Tarjetas de Resumen Rápido (KPIs)
    total_gastado = df_gastos['monto_neto'].sum()
    deducibles = df_gastos[df_gastos['deducible'] == 'Sí']['monto_neto'].sum()
    no_deducibles = df_gastos[df_gastos['deducible'] == 'No']['monto_neto'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gasto Total (IVA Incluido)", f"${total_gastado:,.2f} MXN")
    col2.metric("Gasto Facturable/Deducible", f"${deducibles:,.2f} MXN", f"{deducibles/total_gastado*100:.1f}% del total" if total_gastado > 0 else "0%")
    col3.metric("Gasto No Deducible", f"${no_deducibles:,.2f} MXN", f"-{no_deducibles/total_gastado*100:.1f}% del total" if total_gastado > 0 else "0%", delta_color="inverse")
    
    st.markdown("---")
    
    # 2. Fila de Gráficos Circulares (Rubro, Deducible, Método de Pago)
    col_chart1, col_chart2, col_chart3 = st.columns(3)
    
    with col_chart1:
        st.subheader("Gastos por Rubro")
        fig_rubro = px.pie(
            df_gastos, 
            values='monto_neto', 
            names='rubro',
            color='rubro',
            color_discrete_sequence=px.colors.qualitative.Prism,
            hole=0.4
        )
        fig_rubro.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, showlegend=True)
        fig_rubro.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_rubro, use_container_width=True)
        
    with col_chart2:
        st.subheader("Estatus Fiscal")
        fig_deduc = px.pie(
            df_gastos, 
            values='monto_neto', 
            names='deducible',
            color='deducible',
            color_discrete_map={'Sí': '#2b5c8f', 'No': '#e05c5c'},
            hole=0.4
        )
        fig_deduc.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, showlegend=True)
        fig_deduc.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_deduc, use_container_width=True)
        
    with col_chart3:
        st.subheader("Método de Pago")
        fig_pago = px.pie(
            df_gastos, 
            values='monto_neto', 
            names='metodo_pago',
            color='metodo_pago',
            color_discrete_sequence=px.colors.qualitative.Safe,
            hole=0.4
        )
        fig_pago.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, showlegend=True)
        fig_pago.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pago, use_container_width=True)
        
    st.markdown("---")
    
    # 3. Evolución del Gasto a lo largo del tiempo
    st.subheader("Tendencia Mensual de Gastos")
    # Agrupar gastos por Año-Mes
    df_gastos['Año-Mes'] = df_gastos['fecha_dt'].dt.to_period('M').astype(str)
    df_monthly = df_gastos.groupby(['Año-Mes', 'rubro'])['monto_neto'].sum().reset_index()
    df_monthly = df_monthly.sort_values('Año-Mes')
    
    fig_line = px.bar(
        df_monthly,
        x='Año-Mes',
        y='monto_neto',
        color='rubro',
        title="Gastos Mensuales por Rubro",
        labels={'monto_neto': 'Monto Neto (MXN)', 'Año-Mes': 'Mes de Registro'},
        barmode='stack',
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_line.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_line, use_container_width=True)


def render_backorder_dashboard(df_backorder):
    """
    Renderiza los gráficos y proyecciones de Backorder de OC.
    """
    if df_backorder.empty:
        st.info("No hay órdenes de compra registradas en el backorder.")
        return
        
    df_backorder['fecha_dt'] = pd.to_datetime(df_backorder['fecha_compromiso'])
    
    # KPIs de Backorder
    oc_pendientes = df_backorder[df_backorder['estado'] == 'Pendiente']
    oc_pagadas = df_backorder[df_backorder['estado'] == 'Pagado']
    
    total_pendiente = oc_pendientes['monto_oc'].sum()
    total_pagado = oc_pagadas['monto_oc'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Compromisos Pendientes", f"${total_pendiente:,.2f} MXN", f"{len(oc_pendientes)} OCs")
    col2.metric("Monto Pagado Histórico", f"${total_pagado:,.2f} MXN", f"{len(oc_pagadas)} OCs")
    col3.metric("Monto Total de Backorder", f"${(total_pendiente + total_pagado):,.2f} MXN")
    
    st.markdown("---")
    
    # Proyección en Línea de Tiempo (Solo Pendientes de Pago)
    st.subheader("Proyección Mensual de Compromisos de Pago (OCs Pendientes)")
    
    if oc_pendientes.empty:
        st.success("¡No hay compromisos pendientes de pago futuros!")
    else:
        oc_pendientes['Mes_Compromiso'] = oc_pendientes['fecha_dt'].dt.to_period('M').astype(str)
        df_proj = oc_pendientes.groupby('Mes_Compromiso')['monto_oc'].sum().reset_index()
        df_proj = df_proj.sort_values('Mes_Compromiso')
        
        fig_proj = px.bar(
            df_proj,
            x='Mes_Compromiso',
            y='monto_oc',
            text='monto_oc',
            labels={'monto_oc': 'Monto Comprometido (MXN)', 'Mes_Compromiso': 'Mes de Compromiso de Pago'},
            color_discrete_sequence=['#ff9f40']
        )
        fig_proj.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
        fig_proj.update_layout(height=400, yaxis_range=[0, df_proj['monto_oc'].max() * 1.15])
        st.plotly_chart(fig_proj, use_container_width=True)
        
        # Detalle de OCs en backorder
        st.subheader("Listado de Órdenes de Compra Pendientes")
        st.dataframe(
            oc_pendientes[['numero_oc', 'proveedor', 'fecha_compromiso', 'monto_oc', 'proyecto_nombre']]
            .rename(columns={
                'numero_oc': 'Orden de Compra',
                'proveedor': 'Proveedor',
                'fecha_compromiso': 'Fecha Límite',
                'monto_oc': 'Monto Neto',
                'proyecto_nombre': 'Proyecto'
            }),
            use_container_width=True,
            hide_index=True
        )


def render_proyectos_dashboard(df_proyectos, df_gastos):
    """
    Dibuja la comparativa Ingresos vs Gastos y la Rentabilidad por Proyecto.
    """
    if df_proyectos.empty:
        st.info("No hay proyectos cargados para analizar rentabilidad.")
        return
        
    st.subheader("Comparativa de Ingresos vs Gastos por Proyecto")
    
    # Agrupar gastos por proyecto_id
    if not df_gastos.empty:
        df_g_sum = df_gastos.groupby('proyecto_id')['monto_neto'].sum().reset_index()
        df_g_sum.columns = ['id', 'total_gastos']
    else:
        df_g_sum = pd.DataFrame(columns=['id', 'total_gastos'])
        
    # Unir con la lista de proyectos
    df_merge = df_proyectos.merge(df_g_sum, on='id', how='left')
    df_merge['total_gastos'] = df_merge['total_gastos'].fillna(0.0)
    df_merge['utilidad'] = df_merge['monto_ingreso'] - df_merge['total_gastos']
    df_merge['margen_pct'] = df_merge.apply(
        lambda r: (r['utilidad'] / r['monto_ingreso'] * 100) if r['monto_ingreso'] > 0 else 0.0, 
        axis=1
    )
    
    # Gráfico de barras agrupadas: Ingresos vs Gastos
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_merge['nombre'],
        y=df_merge['monto_ingreso'],
        name='Ingresos del Proyecto',
        marker_color='#2b5c8f'
    ))
    
    fig.add_trace(go.Bar(
        x=df_merge['nombre'],
        y=df_merge['total_gastos'],
        name='Gastos Asignados',
        marker_color='#e05c5c'
    ))
    
    fig.update_layout(
        barmode='group',
        height=400,
        xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Tabla de Rentabilidad
    st.subheader("Matriz de Rentabilidad Financiera por Proyecto")
    
    df_rentabilidad = df_merge[['nombre', 'monto_ingreso', 'total_gastos', 'utilidad', 'margen_pct', 'activo']].copy()
    df_rentabilidad['activo'] = df_rentabilidad['activo'].map({1: 'Activo', 0: 'Inactivo'})
    
    # Dar formato amigable
    df_rentabilidad_formatted = df_rentabilidad.copy()
    df_rentabilidad_formatted['monto_ingreso'] = df_rentabilidad_formatted['monto_ingreso'].map('${:,.2f}'.format)
    df_rentabilidad_formatted['total_gastos'] = df_rentabilidad_formatted['total_gastos'].map('${:,.2f}'.format)
    df_rentabilidad_formatted['utilidad'] = df_rentabilidad_formatted['utilidad'].map('${:,.2f}'.format)
    df_rentabilidad_formatted['margen_pct'] = df_rentabilidad_formatted['margen_pct'].map('{:.1f}%'.format)
    
    df_rentabilidad_formatted.columns = [
        'Proyecto', 'Ingreso Contratado', 'Gasto Acumulado', 'Utilidad Operativa', 'Margen de Utilidad', 'Estado'
    ]
    
    st.dataframe(df_rentabilidad_formatted, use_container_width=True, hide_index=True)
