import pandas as pd
import requests
import json
import os
import argparse
import uuid
from datetime import datetime

nColecciones = 0
nHuecos = 0
nHuecosError = 0
nColeccionesError = 0

ids_log_file = "ids_creados.txt"

# Definir la clase Coleccion
class Coleccion:
    def __init__(self, nombre, fecha_venta, grupo_compra, id_coleccion):
        self.nombre = nombre
        self.fecha_venta = fecha_venta
        self.grupo_compra = grupo_compra
        self.id_coleccion = id_coleccion
        self.huecos = []

    def add_hueco(self, hueco):
        self.huecos.append(hueco)

    def __repr__(self):
        return (f"Coleccion(nombre={self.nombre}, fecha_venta={self.fecha_venta}, "
                f"grupo_compra={self.grupo_compra}, id_coleccion={self.id_coleccion}, huecos={self.huecos})")

# Definir la clase Hueco
class Hueco:
    def __init__(self, nombre, fecha_venta, grupo_compra, atributo, familias=None):
        self.nombre = nombre
        self.fecha_venta = fecha_venta
        self.grupo_compra = grupo_compra
        self.atributo = atributo
        # familias: lista de URNs (obtenidas del JSON)
        self.familias = familias or []

    def __repr__(self):
        return (f"Hueco(nombre={self.nombre}, fecha_venta={self.fecha_venta}, "
                f"grupo_compra={self.grupo_compra}, atributo={self.atributo}, familias={self.familias})")

# cargar URNs desde json editable
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "urns_config.json")
DEFAULT_URNS = {
    "urns_grupo_comprador": {
        "GLB ATEMPORARY": [
            "urn:BUYERCODE:569c2cb0-419e-466e-b305-ef56a353991b",
            "urn:BUYERCODE:df90c92d-c051-4e50-b72b-07e240c61978",
            "urn:BUYERCODE:75f2b737-06dd-4399-9206-a6c11b65138e"
        ],
        "GLB URBAN": [
            "urn:BUYERCODE:8ce397b0-ec91-46d9-a464-eba4f35f4fb2",
            "urn:BUYERCODE:7cdbb25c-6721-42e4-b97e-5bd22f7f746d",
            "urn:BUYERCODE:79963f0c-b7dd-425b-9fe3-9297d02d0c2e"
        ],
        "GLB TREND": [
            "urn:BUYERCODE:dfa75494-dd6c-4ae2-94dc-51a6cc849ddb",
            "urn:BUYERCODE:7011326d-9a72-4d56-8a02-22fdf5b0ad6b",
            "urn:BUYERCODE:5c5c7f24-f476-4438-bbbc-624c6285257e"
        ]
    },
    "urns_atributos": {
        "GB - SOBRECAMISA": "urn:ATTRIBUTE:0baada16-05b0-401f-8ac4-c13b2e99b54b",
        "GB - CAMISERÍA BÁSICA": "urn:ATTRIBUTE:21406f1c-ca9f-41d2-afcb-1107930e0439",
        "GB - CAMISERÍA ALTO VERANO": "urn:ATTRIBUTE:3307e5e5-bab0-4c66-9e7a-8fef52148878",
        "GB - CAMISERÍA COLECCIÓN": "urn:ATTRIBUTE:4577b157-e147-4eea-a041-188544991f09",
        "GB - PANTALÓN BÁSICO": "urn:ATTRIBUTE:8d82dbc4-5aed-416c-a879-d0ed438fdfa2",
        "GB - PRENDA EXTERIOR BÁSICA": "urn:ATTRIBUTE:b45deeb8-944e-4ee4-b390-401eeecf0d6b",
        "GB - BERMUDA": "urn:ATTRIBUTE:dcd6e348-2d1d-4cb7-a979-19d568a7fc69",
        "GB - PRENDA EXTERIOR COLECCIÓN": "urn:ATTRIBUTE:f1e15909-3dd0-4b06-88c5-86f1a3f688d2",
        "GB - PANTALÓN COLECCIÓN": "urn:ATTRIBUTE:f7677733-420f-4f25-a366-47c0a67abe4d",
        "GB - CHALECO": "urn:ATTRIBUTE:fdddbcd7-cb33-46f5-bb82-aba567a12d39"
    },
    "urn_familias": {
        "FAMILIA_A": "urn:FAMILY:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "FAMILIA_B": "urn:FAMILY:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    },
    "campaign_urn": "urn:CAMPAIGN:c1849669-7700-493f-809f-96b03aca9516",
    "market_urn": "urn:MARKET:2d87237e-2503-46c5-8eee-9f4dbe6c789c"
}

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
except Exception as e:
    print(f"Warning: no se pudo leer {CONFIG_FILE} ({e}), usando valores por defecto")
    cfg = {}

urns_grupo_comprador = cfg.get("urns_grupo_comprador", DEFAULT_URNS["urns_grupo_comprador"])
urns_atributos = cfg.get("urns_atributos", DEFAULT_URNS["urns_atributos"])
urns_familias = cfg.get("urns_familias", cfg.get("urn_familias", DEFAULT_URNS.get("urn_familias", DEFAULT_URNS.get("urn_familias", {}))))
# soportar clave alternativa para subfamilias: 'urns_subfamilias' o 'urns:subfamilias'
urns_subfamilias = cfg.get("urns_subfamilias", cfg.get("urns:subfamilias", {}))
DEFAULT_CAMPAIGN_URN = cfg.get("campaign_urn", DEFAULT_URNS["campaign_urn"])
MARKET_URN = cfg.get("market_urn", DEFAULT_URNS["market_urn"])

# Función para obtener el token de autenticación
def obtener_token():
    token = input("Por favor, introduce tu token de autenticación: ").strip()
    return token

def crear_coleccion_api(coleccion, token, campaign_urn, base_url):
    global nColecciones, nColeccionesError

    url = f"{base_url}/icdmdscol/api/v4/collections"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Generar un nuevo UUID para el id de la colección
    coleccion_id = str(uuid.uuid4())
    # Obtener los owners (URNs) según el grupo de compra
    owners = urns_grupo_comprador.get(coleccion.grupo_compra, [])
    # Preparar el payload
    sales_date = coleccion.fecha_venta.isoformat() if hasattr(coleccion.fecha_venta, "isoformat") else str(coleccion.fecha_venta)
    payload = {
        "id": coleccion_id,
        "name": coleccion.nombre,
        "salesDate": sales_date,
        "owners": owners,
        "campaign": campaign_urn,
        "type": "REGULAR"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        coleccion.id_coleccion = coleccion_id  # Actualiza el id en el objeto
        nColecciones += 1
        with open(ids_log_file, "a", encoding="utf-8") as f:
            f.write(f"COLECCION: {coleccion.nombre} | ID: {coleccion_id}\n")
    else:
        print(f"Error al crear la colección '{coleccion.nombre}': {response.status_code} - {response.text}")
        nColeccionesError += 1

# Función para crear un hueco a través del API
def crear_hueco_api(hueco, token, base_url, collection_id, campaign_urn):
    global nHuecos, nHuecosError

    url = f"{base_url}/icbcpupla/v2/assortment-planning/purchase-variables"  # Endpoint del API
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    attribute_urn = urns_atributos.get(hueco.atributo, "")
    grupo_comprador_urn = urns_grupo_comprador.get(hueco.grupo_compra, [])
    # construir lista de categories: atributo + grupo comprador + familias (URNs)
    categories = [attribute_urn] + list(grupo_comprador_urn or []) + list(hueco.familias or [])
    # filtrar valores vacíos
    categories = [c for c in categories if c]
    launch_date = hueco.fecha_venta.strftime("%Y-%m-%dT00:00:00Z") if hasattr(hueco.fecha_venta, "strftime") else str(hueco.fecha_venta)
    payload = {
        "productPlaceholder": {
            "name": hueco.nombre,
            "collectionId": collection_id,
            "categories": categories,  # atributo + grupo comprador + familias
            "campaigns": [campaign_urn],
        },
        "objectivePlans": [{
            "launchDate": launch_date,
            "timeDimension": campaign_urn,
            "positionDimension": MARKET_URN
        }]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        try:
            hueco_id = response.json().get("id", "NO_ID")
            item_uuid = str(uuid.uuid4())
            items_url = f"{base_url}/icdmdscol/api/v4/collections/{collection_id}/items"
            items_payload = {
                "id": item_uuid,
                "targetReference": {
                    "id": hueco_id,
                    "type": "PRODUCT_PLACEHOLDER"
                }
            }
            items_response = requests.post(items_url, headers=headers, json=items_payload)
            if items_response.status_code != 201:
                print(f"\nError al asociar hueco '{hueco.nombre}' (ID: {hueco_id}) a la colección {collection_id}: {items_response.status_code} - {items_response.text}")

            nHuecos += 1
            with open(ids_log_file, "a", encoding="utf-8") as f:
                f.write(f"- HUECO: {hueco.nombre} | ID: {hueco_id} | ITEM_ID: {item_uuid}\n")
        except Exception:
            print(f"Error {response.status_code} - {response.text}, hueco sin ID {payload}")
            nHuecosError += 1
    else:
        print(f"Error {response.status_code} - {response.text} al crear el hueco {payload}")
        print(url)
        nHuecosError += 1

# Parse input arguments for the Excel file, sheet and skiprows
parser = argparse.ArgumentParser(description="Crear colecciones y huecos desde un Excel")
parser.add_argument("input_file", nargs="?", default="test.xlsx",
                    help="Ruta del fichero Excel de entrada")
parser.add_argument("--sheet", default="LISTADO MCC", help="Nombre de la hoja en el Excel")
parser.add_argument("--skiprows", type=int, default=1, help="Número de filas a saltar al leer el Excel")
args = parser.parse_args()

file_path = args.input_file
sheet_name = args.sheet
skiprows = args.skiprows

if not os.path.isfile(file_path):
    print(f"Error: fichero de entrada no encontrado: {file_path}")
    exit(1)

# Cargar el archivo Excel y seleccionar la hoja indicada
df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)  # Ajusta el número de filas a saltar si es necesario

# Diccionario para almacenar las colecciones
colecciones_dict = {}

# Crear colecciones y huecos
for index, row in df.iterrows():
    nombre_coleccion = row.get('Colección') if isinstance(row, (dict,)) else row['Colección']
    fecha_venta = row.get('Fecha en tienda') if isinstance(row, (dict,)) else row['Fecha en tienda']

    # Evitar crear objetos si la fecha es NaT o vacía
    if pd.notna(nombre_coleccion) and pd.notna(fecha_venta):
        grupo_compra = row.get('Grupo Comprador') if isinstance(row, (dict,)) else row['Grupo Comprador']
        nombre = row.get('Descripción') if isinstance(row, (dict,)) else row['Descripción']
        atributo = row.get('Atributo') if isinstance(row, (dict,)) else row['Atributo']

        # Leer familias desde la columna "Familias" (separadas por ',') y mapear a URNs desde urns_familias
        familias_cell = row.get('Familias', '') if isinstance(row, (dict,)) else row.get('Familias', '')
        familias_urns = []
        if pd.notna(familias_cell) and str(familias_cell).strip():
            familias_names = [f.strip() for f in str(familias_cell).split(',') if f.strip()]
            familias_urns = [urns_familias.get(name) for name in familias_names]
            familias_urns = [u for u in familias_urns if u]  # eliminar None

        # Leer Subfamilia opcional y mapear a URN desde urns_subfamilias
        subfamilia_cell = row.get('Subfamilia', '') if isinstance(row, (dict,)) else row.get('Subfamilia', '')
        if pd.notna(subfamilia_cell) and str(subfamilia_cell).strip():
            sub_name = str(subfamilia_cell).strip()
            sub_urn = urns_subfamilias.get(sub_name) or urns_subfamilias.get(sub_name.upper()) or urns_subfamilias.get(sub_name.lower())
            if sub_urn:
                familias_urns.append(sub_urn)

        # Crear o actualizar la colección
        if nombre_coleccion not in colecciones_dict:
            id_coleccion = None
            coleccion = Coleccion(nombre_coleccion, fecha_venta, grupo_compra, id_coleccion)
            colecciones_dict[nombre_coleccion] = coleccion
        else:
            coleccion = colecciones_dict[nombre_coleccion]

        # Crear el hueco y añadirlo a la colección
        hueco = Hueco(nombre, fecha_venta, grupo_compra, atributo, familias=familias_urns)
        coleccion.add_hueco(hueco)

# Crear un archivo de texto con el resultado de la ejecución
with open('resultado_colecciones.txt', 'w', encoding="utf-8") as file:
    file.write("Colecciones, Fecha de Venta y Huecos:\n\n")
    for coleccion in colecciones_dict.values():
        file.write(f"Colección: {coleccion.nombre}\n")
        file.write(f"Fecha de Venta: {coleccion.fecha_venta}\n")
        file.write(f"Grupo de compra: {coleccion.grupo_compra}\n")
        file.write(f"Número de Huecos: {len(coleccion.huecos)}\n")
        for hueco in coleccion.huecos:
            file.write(
                f"  - Hueco: {hueco.nombre}, Fecha Venta: {hueco.fecha_venta}, "
                f"Grupo Compra: {hueco.grupo_compra},  "
                f"Atributo: {hueco.atributo}, Familias(URNs): {hueco.familias}\n"
            )
        file.write("\n")

print("El archivo 'resultado_colecciones.txt' ha sido creado con éxito.")

# Solicitar confirmación del usuario
confirmacion = input("¿Deseas proceder con la creación de las colecciones y huecos en el sistema? (sí/no): ")

# Llamar a las APIs si se confirma
if confirmacion.strip().lower() == 'sí':
    token = obtener_token()
    total_colecciones = len(colecciones_dict)
    total_huecos = sum(len(coleccion.huecos) for coleccion in colecciones_dict.values())
    if token:
        # Definir la base URL según el entorno
        entorno = input("Indica el entorno (PRE/PRO): ").strip().upper()
        base_url = "https://apigw-pre.apps.purchaseweuocp1pre.paas01weu.iopcompclo-pre.azcl.inditex.com" if entorno == "PRE" else "https://apigw.apps.purchaseweuocp1.paas01weu.iopcompclo.azcl.inditex.com"
        campaign_urn = DEFAULT_CAMPAIGN_URN
        for coleccion in colecciones_dict.values():
            # Crear colecciones
            crear_coleccion_api(coleccion, token, campaign_urn, base_url)
            # Crear huecos
            for hueco in coleccion.huecos:
                crear_hueco_api(hueco, token, base_url, coleccion.id_coleccion, campaign_urn)
                print(f"Colecciones creadas {nColecciones} de {total_colecciones}. Huecos creados: {nHuecos} de {total_huecos}", end='\r', flush=True)
        # resumen final
        print()
        print(f"Operación finalizada. {nColecciones} colecciones creadas y {nHuecos} huecos creados.")
else:
    print("Operación cancelada.")