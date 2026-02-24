import requests
from datetime import datetime

URNS_GRUPO_COMPRA = [
    "urn:BUYERCODE:569c2cb0-419e-466e-b305-ef56a353991b",
    "urn:BUYERCODE:df90c92d-c051-4e50-b72b-07e240c61978",
    "urn:BUYERCODE:75f2b737-06dd-4399-9206-a6c11b65138e"
]
URN_CAMPAIGN = "urn:CAMPAIGN:c1849669-7700-493f-809f-96b03aca9516"

def pedir_entorno_y_token():
    entorno = input("Indica el entorno (PRE/PRO): ").strip().upper()
    token = input("Introduce el token de acceso: ").strip()
    if entorno == "PRE":
        base_url = "https://apigw-pre.apps.purchaseweuocp1pre.paas01weu.iopcompclo-pre.azcl.inditex.com"
    else:
        base_url = "https://apigw.apps.purchaseweuocp1.paas01weu.iopcompclo.azcl.inditex.com"
    return base_url, token

def obtener_huecos_glb_atemporary(base_url, token):
    url = f"{base_url}/icbcpupla/v1/assortment-planning/product-placeholders/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "categories": [URNS_GRUPO_COMPRA],
        "campaigns": [[URN_CAMPAIGN]],
        "offset": 0,
        "limit": 100
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            print("ERROR al consultar huecos:")
            print("URL:", url)
            print("HEADERS:", headers)
            print("PAYLOAD:", payload)
            print("STATUS CODE:", resp.status_code)
            print("RESPONSE TEXT:", resp.text)
            resp.raise_for_status()
        # Los huecos están dentro de data
        return resp.json().get("data", [])
    except Exception as e:
        print("EXCEPCIÓN:", e)
        raise

def obtener_coleccion(base_url, token, collection_id):
    url = f"{base_url}/icdmdscol/api/v4/collections/{collection_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def misma_fecha(fecha1, fecha2):
    """Devuelve True si ambas fechas representan el mismo día."""
    try:
        d1 = datetime.fromisoformat(fecha1.replace("Z", "")) if fecha1 else None
        d2 = datetime.fromisoformat(fecha2.replace("Z", "")) if fecha2 else None
        if d1 and d2:
            return d1.date() == d2.date()
    except Exception:
        pass
    return False

def print_rojo(texto):
    print(f"\n\033[91m{texto}\033[0m")

def main():
    base_url, token = pedir_entorno_y_token()
    huecos = obtener_huecos_glb_atemporary(base_url, token)
    with open("checkpoint_charlie.txt", "w", encoding="utf-8") as f:
        f.write(f"Huecos encontrados: {len(huecos)}\n\n")
        for hueco in huecos:
            nombre_hueco = hueco.get("name")
            # La fecha de venta está en purchaseVariable: objectivePlans: launchDate
            fecha_venta_hueco = None
            purchase_variable = hueco.get("purchaseVariable", {})
            if purchase_variable:
                objective_plans = purchase_variable.get("objectivePlans", [])
                if objective_plans and isinstance(objective_plans, list):
                    fecha_venta_hueco = objective_plans[0].get("launchDate")
            

            collection_id = hueco.get("collectionId")
            if collection_id:
                coleccion = obtener_coleccion(base_url, token, collection_id)
                nombre_coleccion = coleccion.get("name")
                sales_date = coleccion.get("salesDate")
                coleccion_info = f"  -> Colección: {nombre_coleccion} | Fecha de primera venta: {sales_date}"
            else:
                sales_date = None
                coleccion_info = "  -> Colección: No encontrada"

            linea = f"Hueco: {nombre_hueco} | Fecha de venta: {fecha_venta_hueco}\n{coleccion_info}\n{'-'*40}\n"
            
            # Solo mostrar discrepancia si no es el mismo día (ignorando formato)
            if fecha_venta_hueco and sales_date and not misma_fecha(fecha_venta_hueco, sales_date):
                print_rojo(linea)
            else:
                f.write(linea)

if __name__ == "__main__":
    main()