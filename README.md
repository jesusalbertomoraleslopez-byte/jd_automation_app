# J&D Automation Industries - Sistema de Control Financiero

Este repositorio contiene una aplicación web financiera interna desarrollada para la PYME **J&D Automation Industries** utilizando el stack de **Python, Streamlit, Pandas, openpyxl, Plotly y SQLite**. El sistema está diseñado para operar localmente en la red de la empresa de forma ágil y segura.

---

## 🚀 Características del Sistema

1. **Gestión de Egresos y Comprobantes SAT (XML/PDF)**:
   - Permite la captura manual de gastos homologados en **Monto Neto con IVA Incluido**.
   - Integra un cargador de archivos XML (CFDI) y PDF para gastos "Facturados".
   - Valida automáticamente el RFC del proveedor, el UUID fiscal y que el total registrado coincida con el del XML.

2. **Integración con Excel Dinámico**:
   - Generación dinámica de plantillas de Excel (`.xlsx`) que incluyen listas de validación de datos (dropdowns en celdas) basadas en los proyectos activos y rubros.
   - Carga masiva de gastos diarios validada por renglón con reporte preciso de errores de formato o consistencia.

3. **Dashboards Interactivos**:
   - **Egresos**: Distribución por Rubros, Estatus Fiscal (Deducible vs No Deducible) e instrumento de pago (Tarjetas, Transferencias, Efectivo).
   - **Backorder**: Proyección mensual de flujos de pago futuros comprometidos mediante Órdenes de Compra (OC).
   - **Rentabilidad**: Vista comparativa directa entre ingresos cotizados vs gastos acumulados por cada proyecto.

4. **Análisis de EBITDA**:
   - Muestra el rendimiento de la operación restando al ingreso total los gastos operativos (excluyendo adquisición/depreciación de maquinaria).
   - Reportes descargables en CSV para movimientos específicos en Tarjetas de Crédito, Transferencias Bancarias y Efectivo.

---

## 📁 Estructura del Repositorio

```text
jd_automation_app/
│
├── app.py                 # Punto de entrada de Streamlit (Interfaz y menús)
├── requirements.txt       # Librerías y dependencias necesarias
├── database.py            # Esquema y control CRUD de SQLite3 (incluye semillas demo)
├── ejemplo_factura.xml    # Archivo XML de muestra para pruebas de validación SAT
├── .gitignore             # Archivos omitidos de control de versiones
├── data/
│   └── jd_finanzas.db     # Base de datos SQLite local (Autogenerada al iniciar)
└── modules/
    ├── excel_handler.py   # Lógica para plantillas e importador de Excel
    ├── xml_parser.py      # Lógica de lectura y parseo del XML del SAT
    └── dashboards.py      # Visualización de métricas en Plotly Express/GO
```

---

## 🛠️ Instalación y Uso Local

### 1. Clonar el repositorio
```bash
git clone <URL-DE-TU-REPOSITORIO>
cd jd_automation_app
```

### 2. Configurar el Entorno Virtual
Se recomienda crear un entorno virtual para no interferir con otras librerías de su sistema:
```bash
python -m venv venv
# Activar en Windows (PowerShell):
.\venv\Scripts\Activate
# Activar en Windows (CMD):
.\venv\Scripts\activate.bat
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Lanzar la Aplicación
```bash
streamlit run app.py
```
La aplicación se abrirá en su navegador por defecto en la dirección `http://localhost:8501`.
