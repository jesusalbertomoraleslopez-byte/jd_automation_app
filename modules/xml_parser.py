import xml.etree.ElementTree as ET
import re

def parse_cfdi_xml(file_contents):
    """
    Parsea el contenido de un archivo XML de CFDI de Factura del SAT.
    Extrae:
      - RFC del Emisor (Proveedor)
      - UUID (Folio Fiscal)
      - Total (Monto Neto con IVA)
      
    Parámetros:
      file_contents (bytes o str): Contenido del archivo XML.
      
    Retorna:
      dict: Con las llaves 'rfc_proveedor', 'uuid', 'total', y opcionalmente 'error' si falla.
    """
    try:
        if isinstance(file_contents, bytes):
            # Decodificar manejando BOM si existe
            xml_text = file_contents.decode('utf-8-sig', errors='ignore')
        else:
            xml_text = file_contents

        # Parsear XML
        root = ET.fromstring(xml_text)
        
        # Eliminar namespaces para simplificar la búsqueda (o buscar de forma genérica)
        def clean_tag(tag):
            return re.sub(r'\{.*\}', '', tag)
            
        rfc_proveedor = None
        uuid = None
        total = None
        
        # Extraer el total del nodo raíz (Comprobante)
        for attr_key, attr_val in root.attrib.items():
            if clean_tag(attr_key).lower() == 'total':
                try:
                    total = float(attr_val)
                except ValueError:
                    total = 0.0
                break
                
        # Iterar para buscar Emisor y TimbreFiscalDigital
        for elem in root.iter():
            local_tag = clean_tag(elem.tag)
            
            if local_tag == 'Emisor':
                # Buscar el RFC en los atributos
                for attr_key, attr_val in elem.attrib.items():
                    if clean_tag(attr_key).lower() == 'rfc':
                        rfc_proveedor = attr_val
                        break
                        
            elif local_tag == 'TimbreFiscalDigital':
                # Buscar el UUID en los atributos
                for attr_key, attr_val in elem.attrib.items():
                    if clean_tag(attr_key).lower() == 'uuid':
                        uuid = attr_val
                        break
                        
        return {
            'rfc_proveedor': rfc_proveedor,
            'uuid': uuid,
            'total': total,
            'success': True
        }
    except Exception as e:
        return {
            'rfc_proveedor': None,
            'uuid': None,
            'total': None,
            'success': False,
            'error': f"Error al procesar el archivo XML: {str(e)}"
        }
