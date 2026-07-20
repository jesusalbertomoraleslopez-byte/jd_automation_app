import io
import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from database import get_db_connection, get_proyectos, get_cuentas, add_gasto

def generate_excel_template():
    """
    Genera un archivo Excel en memoria con formato y validaciones de datos (listas desplegables).
    Retorna los bytes del archivo generado.
    """
    wb = Workbook()
    
    # 1. Crear las hojas
    ws_gastos = wb.active
    ws_gastos.title = "Gastos"
    ws_lists = wb.create_sheet("Listas_Config")
    
    # Ocultar la hoja de listas para limpieza visual
    # ws_lists.sheet_state = 'hidden' # La podemos ocultar, o dejarla visible. Dejémosla visible pero con advertencia.
    
    # 2. Rellenar las listas en Listas_Config
    # Obtener proyectos activos
    df_proy = get_proyectos(only_active=True)
    proyectos = df_proy['nombre'].tolist() if not df_proy.empty else ["Sin Proyectos Activos"]
    
    rubros = ['Materiales', 'Mano de obra', 'Supervisión', 'Gastos generales', 'Herramienta', 'Maquinaria']
    deducibles = ['Sí', 'No']
    estados_fact = ['Pendiente', 'Facturado']
    metodos_pago = ['Tarjeta de Crédito', 'Transferencia Bancaria', 'Efectivo']
    
    # Escribir en Listas_Config
    ws_lists.cell(row=1, column=1, value="Proyectos").font = Font(bold=True)
    ws_lists.cell(row=1, column=2, value="Rubros").font = Font(bold=True)
    ws_lists.cell(row=1, column=3, value="Deducible").font = Font(bold=True)
    ws_lists.cell(row=1, column=4, value="Estado Facturación").font = Font(bold=True)
    ws_lists.cell(row=1, column=5, value="Método Pago").font = Font(bold=True)
    
    # Escribir proyectos
    for idx, p in enumerate(proyectos, start=2):
        ws_lists.cell(row=idx, column=1, value=p)
        
    # Escribir rubros
    for idx, r in enumerate(rubros, start=2):
        ws_lists.cell(row=idx, column=2, value=r)
        
    # Escribir deducible
    for idx, d in enumerate(deducibles, start=2):
        ws_lists.cell(row=idx, column=3, value=d)
        
    # Escribir estados
    for idx, e in enumerate(estados_fact, start=2):
        ws_lists.cell(row=idx, column=4, value=e)
        
    # Escribir metodos de pago
    for idx, m in enumerate(metodos_pago, start=2):
        ws_lists.cell(row=idx, column=5, value=m)
        
    # 3. Diseñar la hoja de Gastos
    headers = [
        "Fecha (AAAA-MM-DD)",
        "Concepto",
        "Monto Neto (IVA Incluido)",
        "Rubro",
        "Proyecto",
        "Deducible (Sí/No)",
        "Estado Facturación",
        "Método Pago",
        "RFC Proveedor (Opcional)",
        "UUID Fiscal (Opcional)"
    ]
    
    # Estilo de cabeceras
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    ws_gastos.row_dimensions[1].height = 28
    
    for col_idx, header in enumerate(headers, start=1):
        cell = ws_gastos.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    # Ajustar anchos de columnas
    col_widths = {
        'A': 18, 'B': 30, 'C': 25, 'D': 20, 'E': 35, 
        'F': 15, 'G': 20, 'H': 25, 'I': 22, 'J': 38
    }
    for col, width in col_widths.items():
        ws_gastos.column_dimensions[col].width = width

    # 4. Crear Validaciones de Datos
    # Proyecto
    dv_proy = DataValidation(type="list", formula1=f"=Listas_Config!$A$2:$A${len(proyectos)+1}", allow_blank=True)
    dv_proy.error ='El proyecto seleccionado no es válido'
    dv_proy.errorTitle = 'Proyecto Inválido'
    dv_proy.prompt = 'Selecciona un proyecto de la lista'
    dv_proy.promptTitle = 'Proyecto'
    
    # Rubro
    dv_rubro = DataValidation(type="list", formula1=f"=Listas_Config!$B$2:$B${len(rubros)+1}", allow_blank=True)
    dv_rubro.error ='El rubro seleccionado no es válido'
    dv_rubro.errorTitle = 'Rubro Inválido'
    dv_rubro.prompt = 'Selecciona el rubro correspondiente'
    dv_rubro.promptTitle = 'Rubro'
    
    # Deducible
    dv_deduc = DataValidation(type="list", formula1=f"=Listas_Config!$C$2:$C${len(deducibles)+1}", allow_blank=True)
    dv_deduc.error ='Valor inválido (Sí / No)'
    dv_deduc.errorTitle = 'Deducible Inválido'
    dv_deduc.prompt = 'Selecciona si es deducible/facturable'
    dv_deduc.promptTitle = 'Deducible'
    
    # Estado Facturacion
    dv_est = DataValidation(type="list", formula1=f"=Listas_Config!$D$2:$D${len(estados_fact)+1}", allow_blank=True)
    dv_est.error ='El estado seleccionado no es válido'
    dv_est.errorTitle = 'Estado Inválido'
    dv_est.prompt = 'Selecciona si ya está Facturado o Pendiente'
    dv_est.promptTitle = 'Estado de Facturación'
    
    # Método Pago
    dv_met = DataValidation(type="list", formula1=f"=Listas_Config!$E$2:$E${len(metodos_pago)+1}", allow_blank=True)
    dv_met.error ='El método de pago no es válido'
    dv_met.errorTitle = 'Método Inválido'
    dv_met.prompt = 'Selecciona el método de pago'
    dv_met.promptTitle = 'Método de Pago'

    # Agregar validaciones a la hoja de Gastos
    ws_gastos.add_data_validation(dv_proy)
    ws_gastos.add_data_validation(dv_rubro)
    ws_gastos.add_data_validation(dv_deduc)
    ws_gastos.add_data_validation(dv_est)
    ws_gastos.add_data_validation(dv_met)

    # Asignar rangos de aplicación de validación (filas 2 a 500)
    range_cells = "2:500"
    dv_proy.add(f"E{range_cells}")
    dv_rubro.add(f"D{range_cells}")
    dv_deduc.add(f"F{range_cells}")
    dv_est.add(f"G{range_cells}")
    dv_met.add(f"H{range_cells}")

    # Guardar en memoria y retornar bytes
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out.getvalue()

def import_excel_expenses(file_bytes):
    """
    Lee un archivo Excel cargado por el usuario, valida cada fila y la importa a la base de datos.
    Retorna un diccionario con:
      - 'success': bool
      - 'imported_count': int
      - 'errors': list of strings con detalles de errores encontrados en filas específicas.
    """
    try:
        # Leer el excel
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Gastos")
    except Exception as e:
        return {'success': False, 'imported_count': 0, 'errors': [f"Error al leer el archivo Excel: {str(e)}"]}
        
    # Verificar columnas esperadas
    expected_cols = [
        "Fecha (AAAA-MM-DD)",
        "Concepto",
        "Monto Neto (IVA Incluido)",
        "Rubro",
        "Proyecto",
        "Deducible (Sí/No)",
        "Estado Facturación",
        "Método Pago",
        "RFC Proveedor (Opcional)",
        "UUID Fiscal (Opcional)"
    ]
    
    # Limpiar nombres de columnas por si acaso tienen espacios extra
    df.columns = [c.strip() for c in df.columns]
    
    # Validar que existan las columnas principales
    missing_cols = [col for col in expected_cols[:8] if col not in df.columns]
    if missing_cols:
        return {
            'success': False,
            'imported_count': 0,
            'errors': [f"Faltan las siguientes columnas obligatorias en la hoja 'Gastos': {', '.join(missing_cols)}"]
        }

    # Obtener proyectos de base de datos para mapeo de nombres a IDs
    df_projects = get_proyectos()
    project_map = dict(zip(df_projects['nombre'], df_projects['id']))
    
    # Obtener cuentas de base de datos para asignar cuenta por tipo de pago
    df_accounts = get_cuentas()
    # Mapeamos tipo de cuenta a una lista de IDs de cuenta, tomaremos la primera disponible
    account_map = {}
    for _, row in df_accounts.iterrows():
        tipo = row['tipo']
        if tipo not in account_map:
            account_map[tipo] = []
        account_map[tipo].append(row['id'])

    errors = []
    rows_to_insert = []
    
    # Validaciones permitidas
    allowed_rubros = {'Materiales', 'Mano de obra', 'Supervisión', 'Gastos generales', 'Herramienta', 'Maquinaria'}
    allowed_deduc = {'Sí', 'No'}
    allowed_est = {'Pendiente', 'Facturado'}
    allowed_met = {'Tarjeta de Crédito', 'Transferencia Bancaria', 'Efectivo'}

    for idx, row in df.iterrows():
        row_num = idx + 2 # Fila 1 es cabecera, pandas index 0 es Fila 2
        
        # Ignorar filas completamente vacías
        if row.isna().all():
            continue
            
        fecha_val = row.get("Fecha (AAAA-MM-DD)")
        concepto_val = row.get("Concepto")
        monto_val = row.get("Monto Neto (IVA Incluido)")
        rubro_val = row.get("Rubro")
        proyecto_val = row.get("Proyecto")
        deduc_val = row.get("Deducible (Sí/No)")
        est_val = row.get("Estado Facturación")
        met_val = row.get("Método Pago")
        
        # Opcionales
        rfc_val = row.get("RFC Proveedor (Opcional)")
        uuid_val = row.get("UUID Fiscal (Opcional)")
        
        # Validar Campos Vacíos requeridos
        if pd.isna(fecha_val) or pd.isna(concepto_val) or pd.isna(monto_val) or pd.isna(rubro_val) or pd.isna(proyecto_val) or pd.isna(deduc_val) or pd.isna(est_val) or pd.isna(met_val):
            errors.append(f"Fila {row_num}: Contiene campos obligatorios vacíos.")
            continue
            
        # Formatear y Validar Fecha
        fecha_str = ""
        if isinstance(fecha_val, (datetime.datetime, datetime.date)):
            fecha_str = fecha_val.strftime('%Y-%m-%d')
        else:
            # Intentar parsear texto
            try:
                date_parsed = pd.to_datetime(str(fecha_val).strip(), format='%Y-%m-%d')
                fecha_str = date_parsed.strftime('%Y-%m-%d')
            except Exception:
                errors.append(f"Fila {row_num}: Formato de fecha inválido. Utilice AAAA-MM-DD (recibido: '{fecha_val}').")
                continue
                
        # Validar Monto
        try:
            monto_float = float(monto_val)
            if monto_float <= 0:
                errors.append(f"Fila {row_num}: El monto debe ser mayor a cero (recibido: {monto_val}).")
                continue
        except ValueError:
            errors.append(f"Fila {row_num}: El monto debe ser un número válido (recibido: '{monto_val}').")
            continue
            
        # Validar strings con listas
        rubro_str = str(rubro_val).strip()
        if rubro_str not in allowed_rubros:
            errors.append(f"Fila {row_num}: Rubro '{rubro_str}' no es válido. Opciones: {list(allowed_rubros)}")
            continue
            
        deduc_str = str(deduc_val).strip()
        if deduc_str not in allowed_deduc:
            errors.append(f"Fila {row_num}: Deducible '{deduc_str}' no es válido. Debe ser Sí o No.")
            continue
            
        est_str = str(est_val).strip()
        if est_str not in allowed_est:
            errors.append(f"Fila {row_num}: Estado Facturación '{est_str}' no es válido. Debe ser Pendiente o Facturado.")
            continue
            
        met_str = str(met_val).strip()
        if met_str not in allowed_met:
            errors.append(f"Fila {row_num}: Método Pago '{met_str}' no es válido. Opciones: {list(allowed_met)}")
            continue
            
        # Validar Proyecto
        proy_str = str(proyecto_val).strip()
        if proy_str not in project_map:
            errors.append(f"Fila {row_num}: Proyecto '{proy_str}' no existe en la base de datos o está inactivo.")
            continue
        proy_id = project_map[proy_str]
        
        # Validar y limpiar RFC/UUID opcionales
        rfc_str = str(rfc_val).strip() if not pd.isna(rfc_val) else None
        uuid_str = str(uuid_val).strip() if not pd.isna(uuid_val) else None
        
        if est_str == 'Facturado':
            if not rfc_str or not uuid_str:
                # Advertencia o error? Dejémoslo como advertencia o requiramos que si es Facturado, idealmente tenga RFC/UUID.
                # De acuerdo a la especificación, los comprobantes cargados en Facturado deben poder subir XML/PDF.
                # Por ahora, si suben por excel, permitimos omitirlo pero arrojamos advertencia o insertamos. Requeriremos que en excel al menos se procese.
                pass
                
        # Asignar cuenta asociada
        cuenta_id = None
        if met_str in account_map and len(account_map[met_str]) > 0:
            cuenta_id = account_map[met_str][0] # Asignamos la primera cuenta de ese tipo
            
        rows_to_insert.append({
            'fecha': fecha_str,
            'concepto': str(concepto_val).strip(),
            'monto_neto': monto_float,
            'rubro': rubro_str,
            'proyecto_id': proy_id,
            'deducible': deduc_str,
            'estado_facturacion': est_str,
            'metodo_pago': met_str,
            'cuenta_id': cuenta_id,
            'rfc_proveedor': rfc_str,
            'uuid_fiscal': uuid_str
        })

    # Si hay errores en alguna fila, no importamos nada para mantener consistencia transaccional
    if errors:
        return {
            'success': False,
            'imported_count': 0,
            'errors': errors
        }
        
    # Insertar registros
    imported_count = 0
    for r in rows_to_insert:
        success, _ = add_gasto(
            fecha=r['fecha'],
            concepto=r['concepto'],
            monto_neto=r['monto_neto'],
            rubro=r['rubro'],
            proyecto_id=r['proyecto_id'],
            deducible=r['deducible'],
            estado_facturacion=r['estado_facturacion'],
            metodo_pago=r['metodo_pago'],
            cuenta_id=r['cuenta_id'],
            rfc_proveedor=r['rfc_proveedor'],
            uuid_fiscal=r['uuid_fiscal']
        )
        if success:
            imported_count += 1
            
    return {
        'success': True,
        'imported_count': imported_count,
        'errors': []
    }
