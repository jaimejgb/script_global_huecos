import pandas as pd
import requests

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
    # def __init__(self, nombre, fecha_venta, grupo_compra, precio, atributo, profundidad):
    def __init__(self, nombre, fecha_venta, grupo_compra, atributo):
        self.nombre = nombre
        self.fecha_venta = fecha_venta
        self.grupo_compra = grupo_compra
        # self.precio = precio
        self.atributo = atributo
        # self.profundidad = profundidad

    def __repr__(self):
        return (f"Hueco(nombre={self.nombre}, fecha_venta={self.fecha_venta}, "
        #         f"grupo_compra={self.grupo_compra}, precio={self.precio}, "
        #         f"atributo={self.atributo}, profundidad={self.profundidad})")
                f"grupo_compra={self.grupo_compra}, atributo={self.atributo})")

# Diccionario de equivalencias de URNs para grupos compradores
urns_grupo_comprador = {
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
}

# Diccionario de equivalencias de URNs para atributos
urns_atributos = {
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
}

# Función para obtener el token de autenticación
def obtener_token():
    token = input("Por favor, introduce tu token de autenticación: ")
    return token
import uuid

def crear_coleccion_api(coleccion, token, campaign_urn, base_url):
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
    payload = {
        "id": coleccion_id,
        "name": coleccion.nombre,
        "salesDate": coleccion.fecha_venta.isoformat() if hasattr(coleccion.fecha_venta, "isoformat") else str(coleccion.fecha_venta),
        "owners": owners,
        "campaign": campaign_urn,
        "type": "REGULAR"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"Colección '{coleccion.nombre}' creada con éxito.")
        coleccion.id_coleccion = coleccion_id  # Actualiza el id en el objeto
    else:
        print(f"Error al crear la colección '{coleccion.nombre}': {response.status_code} - {response.text}")

# Función para crear un hueco a través del API
def crear_hueco_api(hueco, token, base_url, collection_id, campaign_urn):
    url = f"{base_url}/icbcpupla/v1/assortment-planning/purchase-variables"  # Endpoint del API
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    attribute_urn = urns_atributos.get(hueco.atributo, "")
    payload = {
        "name": hueco.nombre,
        # "price": hueco.precio,
        "collectionId": collection_id,
        "categories": [attribute_urn],  # URN relativa al atributo
        "campaigns": [campaign_urn],
        "objectivePlans": [{
            "launchDate": hueco.fecha_venta.strftime("%Y-%m-%dT00:00:00Z"),
            "buyDepth": 0,
            "timeDimension": campaign_urn,
            "positionDimension": "urn:MARKET:2d87237e-2503-46c5-8eee-9f4dbe6c789c"
        }]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"Hueco '{hueco.nombre}' creado con éxito.")
    else:
        print(f"Error al crear el hueco '{hueco.nombre}': {response.status_code} - {response.text}")
        print(url)

# Cargar el archivo Excel y seleccionar la hoja "LISTADO MCC"
file_path = 'GLB ESTIMACIÓN VENTA V26 20250908.xlsx'
df = pd.read_excel(file_path, sheet_name='LISTADO MCC', skiprows=1)  # Ajusta el número de filas a saltar si es necesario

# Diccionario para almacenar las colecciones
colecciones_dict = {}

print(df.keys)
print(df.columns)

# Crear colecciones y huecos
for index, row in df.iterrows():
    nombre_coleccion = row['Colección']
    if pd.notna(nombre_coleccion):  # Verificar que el campo "Colección" no esté vacío
        fecha_venta = row['Fecha en tienda']  # Ajusta el nombre de la columna según corresponda
        grupo_compra = row['Grupo Comprador']  # Ajusta el nombre de la columna según corresponda
        # precio = row['PVP Venta']  # Ajusta el nombre de la columna según corresponda
        nombre = row['Descripción']  # Ajusta el nombre de la columna según corresponda
        atributo = row['Atributo']  # Ajusta el nombre de la columna según corresponda
        # profundidad = row['Compra total']  # Ajusta el nombre de la columna según corresponda

        # Crear o actualizar la colección
        if nombre_coleccion not in colecciones_dict:
            # Aquí deberías obtener el ID de la colección creada
            id_coleccion = "id_de_la_coleccion"  # Reemplaza con el ID real
            coleccion = Coleccion(nombre_coleccion, fecha_venta, grupo_compra, id_coleccion)
            colecciones_dict[nombre_coleccion] = coleccion
        else:
            coleccion = colecciones_dict[nombre_coleccion]

        # Crear el hueco y añadirlo a la colección
        # hueco = Hueco(nombre, fecha_venta, grupo_compra, precio, atributo, profundidad)
        hueco = Hueco(nombre, fecha_venta, grupo_compra, atributo)
        coleccion.add_hueco(hueco)

# Crear un archivo de texto con el resultado de la ejecución
with open('resultado_colecciones.txt', 'w') as file:
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
                f"Atributo: {hueco.atributo}\n"
            )
        file.write("\n")

print("El archivo 'resultado_colecciones.txt' ha sido creado con éxito.")

# Solicitar confirmación del usuario
confirmacion = input("¿Deseas proceder con la creación de las colecciones y huecos en el sistema? (sí/no): ")

# Llamar a las APIs si se confirma
if confirmacion.lower() == 'sí':
    token = obtener_token()
    if token:
        # Definir la base URL según el entorno
        entorno = input("Indica el entorno (PRE/PRO): ").strip().upper()
        base_url = "https://apigw-pre.apps.purchaseweuocp1pre.paas01weu.iopcompclo-pre.azcl.inditex.com" if entorno == "PRE" else "https://apigw.apps.purchaseweuocp1.paas01weu.iopcompclo.azcl.inditex.com"
        campaign_urn = "urn:CAMPAIGN:c1849669-7700-493f-809f-96b03aca9516"  # Reemplaza con la URN real de la campaña
        for coleccion in colecciones_dict.values():
            # Crear colecciones
            crear_coleccion_api(coleccion, token, campaign_urn, base_url)
            # Crear huecos
            for hueco in coleccion.huecos:
                crear_hueco_api(hueco, token, base_url, coleccion.id_coleccion, campaign_urn)
else:
    print("Operación cancelada.")