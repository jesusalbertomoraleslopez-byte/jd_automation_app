"""
modules/manual.py — Sección de Manual de Operación del Sistema
"""
import streamlit as st
from modules.pdf_generator import generar_pdf_manual

def render_manual():
    st.markdown("""
    <div style="border-left: 3px solid #FE8C29; padding-left: 20px; margin-bottom: 20px;">
      <h2 style="margin: 0; color: #434E62; font-family: 'Montserrat', sans-serif; font-size: 24px; font-weight: 700;">Manual de Operación del Sistema</h2>
      <p style="margin: 3px 0 0 0; color: #8C96A6; font-family: 'Montserrat', sans-serif; font-size: 13px;">Guía de usuario, procedimientos, reglas fiscales y formatos del sistema.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📖 7.1 Guía de Usuario por Módulo",
        "🧾 7.2 Reglas de Negocio Fiscales",
        "📥 7.3 Descarga de Manual en PDF"
    ])

    with tab1:
        st.markdown("""
        ### **Guía Rápida de Operación**
        
        #### **1. Módulo 1 — Registro de Gastos y Proyectos**
        * **Registrar un Proyecto**: Vaya a *1.1 Proyectos*, introduzca el nombre, descripción e ingreso contratado (monto neto). Presione *Guardar*.
        * **Registrar un Gasto Manual**: Vaya a *1.3 Captura de Gasto*. Rellene los campos obligatorios. 
          * Si el gasto es **Facturado**, deberá adjuntar el archivo XML (CFDI) y PDF correspondientes. El sistema validará que los montos coincidan.
          * Las clasificaciones (Rubro Principal, Subrubro y Concepto Detallado) son opcionales y pueden dejarse en blanco.
          * Al guardar se generará automáticamente un recibo PDF del registro en la barra lateral o confirmación de pantalla.
        * **Backorder de OC**: Permite ingresar folios de órdenes de compra con fecha compromiso de pago para proyectar el flujo de efectivo.

        #### **2. Módulo 2 — Carga Masiva (Excel)**
        1. Presione **"Descargar Plantilla"** para generar un archivo Excel en blanco con las listas de validación conectadas a la base de datos de J&D.
        2. Llene los campos en la hoja **Gastos** (fecha, concepto general, monto, rubros, proyecto, método de pago, etc.).
        3. Suba el archivo en **"Importar Gastos"**. El sistema validará que la jerarquía (Rubro -> Subrubro -> Concepto) sea correcta antes de insertar los registros.

        #### **3. Módulo 3 — Flujo de Caja Proyectado y Ejecución de Gastos (Flujo Secuencial 1 ➔ 2 ➔ 3 ➔ 4)**
        
        ##### **🔄 Flujo Completo de Información: De Programado a Ejecutado**
        
        ```
        [ PASO 1: Programar Compromiso ] ➔ [ PASO 2: Visualizar Matriz ] ➔ [ PASO 3: Ejecución & Pago Real ] ➔ [ PASO 4: Exportación & Correo ]
        (Módulo 3.1 - Estado: Pendiente 🌸) (Módulo 3.2 - Matriz Verde/Rosa) (Módulo 3.3 - Asignación Banco/PDF) (Módulo 3.4 - Excel / EML)
        ```
        
        1. **Paso 1 — ⚙️ 3.1 Programación General (Compromiso Futuro)**:
           * Ingrese a **3. Flujo de Caja Proyectado ➔ ⚙️ 3.1 Programación General** (o *Egresos Fijos Recurrentes / Ingresos*).
           * Registre el compromiso introduciendo: Concepto/Servicio, Monto Estimado, Fecha Compromiso y Rubro.
           * **Estatus Inicial:** El gasto queda como **Pendiente 🌸** y se refleja en la Matriz Semanal (3.2) en celda de color **Rosa**.

        2. **Paso 2 — 📊 3.2 Matriz de Flujo Semanal (Vista Proyectada)**:
           * Evalúe la proyección financiera a 12 semanas.
           * Las celdas verdes corresponden a gastos pagados/ejecutados y las celdas rosas a compromisos pendientes.

        3. **Paso 3 — ⚡ 3.3 Ejecutar Gastos Planeados (Opción A - Liquidación y Pago Real)**:
           * Al realizar el pago real, vaya a **3. Flujo de Caja Proyectado ➔ ⚡ 3.3 Ejecutar Gastos Planeados**.
           * Seleccione el gasto pendiente de la lista desplegable.
           * Confirme/Ajuste los datos reales de la transacción:
             * **Monto Real Pagado** (en caso de variación respecto al estimado).
             * **Fecha Real de Pago**.
             * **Cuenta / Banco de Salida** (ej. *BBVA Empresa*, *Caja Chica*, etc.).
             * **Método de Pago** (*Transferencia*, *Tarjeta*, *Efectivo*).
             * **Estado Fiscal** (*Facturado* / *No Facturado*).
           * Presione **"Confirmar Ejecución y Pago"**.

        4. **Paso 4 — 📥 3.4 Exportación & Envío Ejecutivo (Reportes Excel & .EML)**:
           * Descargue la hoja de flujo semanal en Excel o genere el correo corporativo `.eml` listo para enviar en Outlook.

        #### **4. Módulo 8 — Mantenimiento del Sistema (Solo Administrador)**
        * **CRUD y Edición de Clasificaciones**: Catálogo dinámico para agregar, editar directamente en celdas, renumerar IDs consecitivamente (1..N), exportar en PDF/Excel e importar masivamente.
        * **Gestión de Usuarios**: Permite crear usuarios, asignarles roles (Administrador, Capturista, Consultor), cambiar contraseñas y desactivar cuentas.
        * **Edición de Registros**: Permite corregir o eliminar registros de gastos específicos directamente en una tabla interactiva.
        """)

    with tab2:
        st.markdown("""
        ### **Reglas Fiscales Homologadas**
        
        * **Monto Neto con IVA Incluido**: Todos los importes en el sistema de J&D se manejan con IVA incluido para homogeneizar los cálculos.
        * **Regla Fiscal de Facturación**: Si un egreso se marca en estado **"Facturado"**, es obligatorio adjuntar el archivo XML y PDF. El sistema validará que:
          1. El archivo sea un XML de CFDI válido.
          2. El total del XML coincida con el monto neto ingresado (margen de tolerancia de $0.05 MXN).
        * **Cálculo de EBITDA**:
          * El EBITDA se calcula restando a los ingresos totales contratados el gasto acumulado operativo.
          * Se excluye del cálculo operativo el subrubro **"Equipo Mayor y Renta"** (bajo Herramientas y Maquinaria) debido a que representa depreciación y costos de capital de activos fijos.
        """)

    with tab3:
        st.markdown("### **Descargar Manual Oficial de J&D**")
        st.markdown("Descargue el manual de operación completo estructurado en formato PDF para impresión o distribución interna.")
        
        try:
            pdf_bytes = generar_pdf_manual()
            st.download_button(
                label="📥 Descargar Manual de Operación en PDF",
                data=pdf_bytes,
                file_name="Manual_Operacion_JD_Automation.pdf",
                mime="application/pdf"
            )
            st.success("¡Manual PDF listo para su descarga!")
        except Exception as e:
            st.error(f"Error al generar el manual en PDF: {str(e)}")
