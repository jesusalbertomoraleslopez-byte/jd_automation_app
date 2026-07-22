import io
import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Configurar backend no interactivo
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders

def generate_eml_with_report(excel_bytes, excel_filename, semanas, df_values, df_status, saldo_inicial):
    """Genera los bytes de un archivo .eml con reporte de flujo y gráficos incrustados."""
    # 1. Cálculos de indicadores globales
    labels = [s['label'] for s in semanas]
    
    inflow_rows = [r for r in df_values.index if r.startswith("💼") or "Ingresos" in r]
    outflow_rows = [r for r in df_values.index if not (r.startswith("💼") or "Ingresos" in r) and r not in ('TOTAL ENTRADAS', 'TOTAL SALIDAS', 'BALANCE (NETO)', 'SALDO ACUMULADO')]
    
    total_entradas_ser = df_values.loc[inflow_rows].sum()
    total_salidas_ser = df_values.loc[outflow_rows].sum()
    balance_ser = total_entradas_ser - total_salidas_ser
    
    saldo_acumulado = []
    caja_corr = saldo_inicial
    for b_val in balance_ser:
        caja_corr += b_val
        saldo_acumulado.append(caja_corr)
        
    total_entradas = total_entradas_ser.sum()
    total_salidas = total_salidas_ser.sum()
    balance_neto = total_entradas - total_salidas
    saldo_final = saldo_acumulado[-1]
    
    # ─── Gráfico 1: Tendencia de Saldo Acumulado de Caja ───
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    ax.plot(labels, saldo_acumulado, marker='o', color='#1F4E79', linewidth=2.5, markerfacecolor='#E35E14', markeredgecolor='#1F4E79', markersize=6)
    ax.axhline(0, color='#C00000', linestyle='--', linewidth=1.2, alpha=0.8, label='Límite de Caja')
    ax.set_title('Proyección Semanal de Saldo en Caja (12 Semanas)', fontsize=11, fontweight='bold', pad=10, color='#1F4E79')
    ax.set_ylabel('Saldo Neto (MXN)', fontsize=9, fontweight='bold', color='#1F4E79')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    plt.xticks(rotation=20, ha='right', fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()
    
    buf_chart1 = io.BytesIO()
    plt.savefig(buf_chart1, format='png', dpi=120)
    buf_chart1.seek(0)
    chart1_bytes = buf_chart1.getvalue()
    plt.close(fig)
    
    # ─── Gráfico 2: Distribución de Egresos por Rubro ───
    expense_totals = df_values.loc[outflow_rows].sum(axis=1)
    expense_totals = expense_totals[expense_totals > 0]
    
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    if not expense_totals.empty:
        expense_totals = expense_totals.sort_values()
        clean_labels = [l.replace("👥 ", "").replace("🏛️ ", "").replace("🏥 ", "").replace("🔧 ", "").replace("⚡ ", "").replace("⛽ ", "").replace("📦 ", "") for l in expense_totals.index]
        
        bars = ax.barh(clean_labels, expense_totals.values, color='#1F4E79', edgecolor='#E35E14', height=0.55)
        for bar in bars:
            width = bar.get_width()
            ax.text(width + (expense_totals.values.max() * 0.01), bar.get_y() + bar.get_height()/2, f" ${width:,.2f}", 
                    va='center', ha='left', fontsize=8, color='#333333', fontweight='bold')
            
        ax.set_title('Distribución de Egresos Proyectados por Rubro', fontsize=11, fontweight='bold', pad=10, color='#1F4E79')
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax.grid(True, axis='x', linestyle=':', alpha=0.6)
    else:
        ax.text(0.5, 0.5, 'Sin egresos programados', va='center', ha='center', fontsize=11)
        
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()
    
    buf_chart2 = io.BytesIO()
    plt.savefig(buf_chart2, format='png', dpi=120)
    buf_chart2.seek(0)
    chart2_bytes = buf_chart2.getvalue()
    plt.close(fig)
    
    # ─── Construir Tablas HTML ───
    income_table_rows = ""
    for rname in inflow_rows:
        val = df_values.loc[rname].sum()
        pct = (val / total_entradas * 100) if total_entradas > 0 else 0
        if val > 0:
            income_table_rows += f"""
            <tr style="border-bottom: 1px solid #E0E0E0;">
                <td style="padding: 8px; font-size: 13px; color: #333333;">{rname}</td>
                <td style="padding: 8px; font-size: 13px; text-align: right; font-weight: bold; color: #155724;">${val:,.2f}</td>
                <td style="padding: 8px; font-size: 13px; text-align: right; color: #666666;">{pct:.1f}%</td>
            </tr>
            """
            
    expense_table_rows = ""
    for rname in outflow_rows:
        val = df_values.loc[rname].sum()
        pct = (val / total_salidas * 100) if total_salidas > 0 else 0
        if val > 0:
            expense_table_rows += f"""
            <tr style="border-bottom: 1px solid #E0E0E0;">
                <td style="padding: 8px; font-size: 13px; color: #333333;">{rname}</td>
                <td style="padding: 8px; font-size: 13px; text-align: right; font-weight: bold; color: #C00000;">${val:,.2f}</td>
                <td style="padding: 8px; font-size: 13px; text-align: right; color: #666666;">{pct:.1f}%</td>
            </tr>
            """

    # ─── Formatear Cuerpo del Correo ───
    color_balance = '#155724' if balance_neto >= 0 else '#C00000'
    color_saldo = '#1F4E79' if saldo_final >= 0 else '#C00000'
    
    warning_box = ""
    if any(s < 0 for s in saldo_acumulado):
        warning_box = """
        <div style="background-color: #F8D7DA; color: #721C24; padding: 12px; border-radius: 6px; margin: 20px 0; border: 1px solid #F5C6CB; font-size: 13.5px; font-weight: bold; text-align: center;">
            ⚠️ ADVERTENCIA: Se detectan semanas con déficit proyectado de caja en el período. Revise el plan de cobranzas y priorice egresos no críticos.
        </div>
        """

    html_summary = f"""
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Calibri, Arial, sans-serif; color: #333333; line-height: 1.5; margin: 0; padding: 20px; background-color: #F9FBFD;">
        <div style="max-width: 700px; margin: 0 auto; background-color: #FFFFFF; border: 1px solid #DDE2E6; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.06);">
            <!-- Header -->
            <div style="background-color: #434E62; padding: 22px 28px; border-bottom: 4px solid #FE8C29;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="vertical-align: middle;">
                            <img src="cid:logo_jd" alt="J&D Automation" height="40" width="auto" style="height: 40px; width: auto; display: block; border: 0;" />
                        </td>
                        <td style="text-align: right; vertical-align: middle;">
                            <h1 style="color: #FFFFFF; margin: 0; font-size: 17px; font-weight: bold; text-transform: uppercase;">Reporte Ejecutivo de Flujo de Caja</h1>
                            <p style="color: #FE8C29; margin: 3px 0 0 0; font-size: 12px; font-weight: bold;">J&D AUTOMATION INDUSTRIES — DIRECCIÓN GENERAL</p>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Body -->
            <div style="padding: 25px;">
                <p style="font-size: 15px;">Estimada Dirección,</p>
                <p style="font-size: 15px;">Compartimos el resumen ejecutivo de la proyección del Flujo de Caja Corporativo de J&D Automation para las siguientes 12 semanas. El archivo Excel detallado se encuentra adjunto a este mensaje.</p>
                
                <!-- Indicators Grid -->
                <div style="margin: 20px 0; background-color: #F8F9FA; padding: 15px; border-radius: 6px; border-left: 4px solid #1F4E79; box-shadow: inset 0 1px 3px rgba(0,0,0,0.02);">
                    <h3 style="margin-top: 0; color: #1F4E79; font-size: 14px; text-transform: uppercase; font-weight: bold;">Indicadores Financieros Proyectados</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 6px 0; font-size: 13.5px;">💰 <b>Saldo de Caja Inicial (Bancos):</b></td>
                            <td style="padding: 6px 0; font-size: 13.5px; text-align: right; font-weight: bold;">${saldo_inicial:,.2f} MXN</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; font-size: 13.5px;">📥 <b>Entradas Totales Proyectadas:</b></td>
                            <td style="padding: 6px 0; font-size: 13.5px; text-align: right; font-weight: bold; color: #155724;">${total_entradas:,.2f} MXN</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; font-size: 13.5px;">📤 <b>Egresos Totales Proyectados:</b></td>
                            <td style="padding: 6px 0; font-size: 13.5px; text-align: right; font-weight: bold; color: #C00000;">${total_salidas:,.2f} MXN</td>
                        </tr>
                        <tr style="border-top: 1px solid #D9D9D9; border-bottom: 1px solid #D9D9D9;">
                            <td style="padding: 8px 0; font-size: 13.5px;">⚖️ <b>Flujo Neto del Periodo:</b></td>
                            <td style="padding: 8px 0; font-size: 13.5px; text-align: right; font-weight: bold; color: {color_balance};">${balance_neto:,.2f} MXN</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-size: 14.5px;">🏦 <b>Saldo Final de Caja Proyectado:</b></td>
                            <td style="padding: 8px 0; font-size: 14.5px; text-align: right; font-weight: bold; color: {color_saldo}; font-size: 15.5px;">${saldo_final:,.2f} MXN</td>
                        </tr>
                    </table>
                </div>

                {warning_box}

                <!-- Inline Charts -->
                <div style="margin: 30px 0; text-align: center;">
                    <h3 style="color: #1F4E79; border-bottom: 2px solid #E35E14; padding-bottom: 5px; text-align: left; font-size: 14px; text-transform: uppercase; font-weight: bold;">📈 Análisis Visual de Tendencias</h3>
                    <div style="margin: 20px 0;">
                        <img src="cid:chart_caja_line" alt="Tendencia del Saldo en Caja" style="max-width: 100%; height: auto; border: 1px solid #E0E0E0; border-radius: 4px;"/>
                    </div>
                    <div style="margin: 20px 0;">
                        <img src="cid:chart_gastos_bar" alt="Distribución de Egresos por Rubro" style="max-width: 100%; height: auto; border: 1px solid #E0E0E0; border-radius: 4px;"/>
                    </div>
                </div>

                <!-- Income Details Table -->
                <div style="margin: 30px 0;">
                    <h3 style="color: #1F4E79; border-bottom: 2px solid #E35E14; padding-bottom: 5px; font-size: 14px; text-transform: uppercase; font-weight: bold;">📥 Cobranzas e Ingresos por Proyecto</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <thead>
                            <tr style="background-color: #1F4E79; color: #FFFFFF; text-align: left;">
                                <th style="padding: 8px; font-size: 12.5px;">Concepto / Proyecto</th>
                                <th style="padding: 8px; font-size: 12.5px; text-align: right;">Ingreso Acumulado</th>
                                <th style="padding: 8px; font-size: 12.5px; text-align: right;">Part. %</th>
                            </tr>
                        </thead>
                        <tbody>
                            {income_table_rows if income_table_rows else '<tr><td colspan="3" style="padding: 10px; font-size: 13px; text-align: center; color: #777;">Sin cobros registrados en la proyección.</td></tr>'}
                        </tbody>
                    </table>
                </div>

                <!-- Expense Details Table -->
                <div style="margin: 30px 0;">
                    <h3 style="color: #1F4E79; border-bottom: 2px solid #E35E14; padding-bottom: 5px; font-size: 14px; text-transform: uppercase; font-weight: bold;">📤 Detalle de Egresos por Rubro</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <thead>
                            <tr style="background-color: #800000; color: #FFFFFF; text-align: left;">
                                <th style="padding: 8px; font-size: 12.5px;">Rubro de Egresos</th>
                                <th style="padding: 8px; font-size: 12.5px; text-align: right;">Egreso Acumulado</th>
                                <th style="padding: 8px; font-size: 12.5px; text-align: right;">Part. %</th>
                            </tr>
                        </thead>
                        <tbody>
                            {expense_table_rows if expense_table_rows else '<tr><td colspan="3" style="padding: 10px; font-size: 13px; text-align: center; color: #777;">Sin egresos registrados en la proyección.</td></tr>'}
                        </tbody>
                    </table>
                </div>

                <p style="font-size: 13px; color: #7F8C8D; margin-top: 40px; border-top: 1px solid #E0E0E0; padding-top: 15px; text-align: center;">
                    Este correo en formato .eml fue generado por el Módulo de Control de Flujo de J&D Automation.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # Build MIMEMultipart
    msg = MIMEMultipart('mixed')
    subject_date = datetime.date.today().strftime('%d-%m-%Y')
    msg['Subject'] = f"Reporte de Flujo de Caja y Analisis Financiero J&D - {subject_date}"
    msg['From'] = "finanzas@jydautomation.mx"
    msg['To'] = "direccion@jydautomation.mx"
    
    # Alternative body (plain + html)
    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)
    
    msg_alt.attach(MIMEText("Este reporte requiere soporte HTML. Por favor use un cliente de correo moderno.", 'plain', 'utf-8'))
    msg_alt.attach(MIMEText(html_summary, 'html', 'utf-8'))
    
    # Inline Image 0 (CID logo_jd) - Logo naranja, alto contraste sobre fondo Charcoal
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brand', 'logo_naranja.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brand', 'logo_blanco.png')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            img_logo = MIMEImage(f.read())
            img_logo.add_header('Content-ID', '<logo_jd>')
            img_logo.add_header('Content-Disposition', 'inline', filename='logo_jd.png')
            msg.attach(img_logo)

    # Inline Image 1 (CID chart_caja_line)
    img_caja = MIMEImage(chart1_bytes)
    img_caja.add_header('Content-ID', '<chart_caja_line>')
    img_caja.add_header('Content-Disposition', 'inline', filename='chart_caja_line.png')
    msg.attach(img_caja)
    
    # Inline Image 2 (CID chart_gastos_bar)
    img_gastos = MIMEImage(chart2_bytes)
    img_gastos.add_header('Content-ID', '<chart_gastos_bar>')
    img_gastos.add_header('Content-Disposition', 'inline', filename='chart_gastos_bar.png')
    msg.attach(img_gastos)
    
    # Attachment excel
    excel_part = MIMEBase('application', 'octet-stream')
    excel_part.set_payload(excel_bytes)
    encoders.encode_base64(excel_part)
    excel_part.add_header('Content-Disposition', f'attachment; filename="{excel_filename}"')
    msg.attach(excel_part)
    
    return msg.as_bytes()
