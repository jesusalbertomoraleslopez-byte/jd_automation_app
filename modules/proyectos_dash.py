"""
modules/proyectos_dash.py — Dashboard de Estado y Pareto por Proyecto
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

BRAND_COLORS = ['#434E62', '#FE8C29', '#8C96A6', '#FFA654', '#B4BCC6', '#FFC38C', '#2C3E50', '#E67E22']

def render_estado_proyectos(df_proy: pd.DataFrame, df_gastos: pd.DataFrame):
    """Renderiza el estado financiero de cada proyecto con semáforos y KPIs."""
    st.markdown("### 📊 Estado General de Proyectos")

    if df_proy.empty:
        st.info("No hay proyectos registrados.")
        return

    # Calcular gasto por proyecto
    gasto_map = {}
    if not df_gastos.empty and 'proyecto_id' in df_gastos.columns:
        gasto_map = df_gastos.groupby('proyecto_id')['monto_neto'].sum().to_dict()

    for _, proy in df_proy.iterrows():
        total_gasto = gasto_map.get(proy['id'], 0.0)
        ingreso = proy['monto_ingreso']
        utilidad = ingreso - total_gasto
        pct = (total_gasto / ingreso * 100) if ingreso > 0 else 0
        activo = proy.get('activo', 1)

        # Semáforo de salud
        if pct < 60:
            sem_color = "#62C462"; sem_txt = "🟢 Saludable"
        elif pct < 85:
            sem_color = "#F7A800"; sem_txt = "🟡 En Revisión"
        else:
            sem_color = "#E05C5C"; sem_txt = "🔴 Alerta"

        with st.expander(f"{'🟢' if activo else '⚪'} **{proy['nombre']}**  |  {sem_txt}", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ingreso Contratado", f"${ingreso:,.0f}")
            c2.metric("Gasto Acumulado", f"${total_gasto:,.0f}", delta=f"{pct:.1f}% del presupuesto", delta_color="inverse")
            c3.metric("Utilidad Estimada", f"${utilidad:,.0f}", delta="Positiva" if utilidad >= 0 else "Negativa",
                      delta_color="normal" if utilidad >= 0 else "inverse")
            c4.metric("Estado", sem_txt)

            # Barra de progreso
            st.markdown(f"**Ejecución presupuestal: {pct:.1f}%**")
            progress_val = min(pct / 100, 1.0)
            bar_color = sem_color
            st.markdown(f"""
            <div style="background:#EDEDED; border-radius:8px; height:16px; overflow:hidden;">
              <div style="width:{progress_val*100:.1f}%; background:{bar_color}; height:16px; border-radius:8px;
                          transition:width 0.5s;"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"*{proy.get('descripcion','Sin descripción')}*")


def render_pareto_proyecto(df_gastos: pd.DataFrame, proyecto_id=None, proyecto_nombre="Todos los Proyectos"):
    """Gráfico de Pareto de costos por Concepto Detallado dentro de un proyecto."""
    st.markdown(f"### 📉 Análisis Pareto de Costos — {proyecto_nombre}")

    df = df_gastos.copy()
    if proyecto_id and proyecto_id != "Todos":
        df = df[df['proyecto_id'] == proyecto_id]

    if df.empty:
        st.info("No hay gastos registrados para este proyecto.")
        return

    # Agrupar por el nivel más específico disponible
    label_col = 'concepto_detallado'
    if df[label_col].replace('', pd.NA).dropna().empty:
        label_col = 'subrubro'
    if df[label_col].replace('', pd.NA).dropna().empty:
        label_col = 'rubro'
    if df[label_col].replace('', pd.NA).dropna().empty:
        label_col = 'concepto'

    df_grouped = df.groupby(label_col)['monto_neto'].sum().reset_index()
    df_grouped = df_grouped[df_grouped[label_col].notna() & (df_grouped[label_col] != '')]
    df_grouped = df_grouped.sort_values('monto_neto', ascending=False).reset_index(drop=True)

    if df_grouped.empty:
        df_grouped = df.groupby('concepto')['monto_neto'].sum().reset_index()
        df_grouped = df_grouped.sort_values('monto_neto', ascending=False).reset_index(drop=True)
        label_col = 'concepto'

    # Calcular acumulado
    total = df_grouped['monto_neto'].sum()
    df_grouped['pct'] = df_grouped['monto_neto'] / total * 100
    df_grouped['acumulado'] = df_grouped['pct'].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_grouped[label_col],
        y=df_grouped['monto_neto'],
        name='Monto (MXN)',
        marker_color='#434E62',
        text=df_grouped['monto_neto'].map('${:,.0f}'.format),
        textposition='outside'
    ))
    fig.add_trace(go.Scatter(
        x=df_grouped[label_col],
        y=df_grouped['acumulado'],
        name='% Acumulado',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#FE8C29', width=3),
        marker=dict(size=7)
    ))
    fig.add_hline(y=80, yref='y2', line_dash='dash', line_color='#E05C5C',
                  annotation_text='80% (Regla de Pareto)', annotation_position='top right')

    fig.update_layout(
        yaxis=dict(title='Monto (MXN)', titlefont_color='#434E62'),
        yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 105], titlefont_color='#FE8C29'),
        xaxis_tickangle=-35,
        height=450,
        legend=dict(orientation='h', y=1.12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla resumen
    st.markdown("**Detalle de Costos:**")
    df_show = df_grouped[[label_col, 'monto_neto', 'pct', 'acumulado']].copy()
    df_show['monto_neto'] = df_show['monto_neto'].map('${:,.2f}'.format)
    df_show['pct'] = df_show['pct'].map('{:.1f}%'.format)
    df_show['acumulado'] = df_show['acumulado'].map('{:.1f}%'.format)
    df_show.columns = ['Concepto / Clasificación', 'Monto', '% del Total', '% Acumulado']
    st.dataframe(df_show, use_container_width=True, hide_index=True)


def render_progreso_presupuesto(df_proy: pd.DataFrame, df_gastos: pd.DataFrame):
    """Gráfico de barras horizontales de presupuesto vs gasto por proyecto."""
    st.markdown("### 📊 Presupuesto vs Gasto por Proyecto")

    gasto_map = {}
    if not df_gastos.empty and 'proyecto_id' in df_gastos.columns:
        gasto_map = df_gastos.groupby('proyecto_id')['monto_neto'].sum().to_dict()

    rows = []
    for _, p in df_proy.iterrows():
        rows.append({
            'Proyecto': p['nombre'][:30],
            'Ingreso Contratado': p['monto_ingreso'],
            'Gasto Acumulado': gasto_map.get(p['id'], 0.0)
        })

    if not rows:
        st.info("No hay datos suficientes para mostrar el gráfico.")
        return

    df_chart = pd.DataFrame(rows)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Ingreso Contratado',
        x=df_chart['Ingreso Contratado'],
        y=df_chart['Proyecto'],
        orientation='h',
        marker_color='#434E62',
    ))
    fig.add_trace(go.Bar(
        name='Gasto Acumulado',
        x=df_chart['Gasto Acumulado'],
        y=df_chart['Proyecto'],
        orientation='h',
        marker_color='#FE8C29',
    ))
    fig.update_layout(
        barmode='group',
        height=max(250, len(rows) * 70),
        xaxis_title='Monto (MXN)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)
