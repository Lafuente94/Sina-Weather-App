import requests

# Pega tu API key entre las comillas
API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGV4bGFmdWVudGU5NEBnbWFpbC5jb20iLCJqdGkiOiJmOWE2MDY3ZC02Mjk0LTQ4ZTUtYjEwYy05OWY5YzJmMWNmODgiLCJpc3MiOiJBRU1FVCIsImlhdCI6MTc4Mzk0MzQzMCwidXNlcklkIjoiZjlhNjA2N2QtNjI5NC00OGU1LWIxMGMtOTlmOWMyZjFjZjg4Iiwicm9sZSI6IiJ9.dZU0L-hphATVHfZQsGY4cBHgBRjfnWAVayiIUu3Q1CQ"

BASE = "https://opendata.aemet.es/opendata/api"
HEADERS = {"api_key": API_KEY}

# Paso 1: pedir el inventario. AEMET nos devuelve una URL, no los datos.
url = f"{BASE}/valores/climatologicos/inventarioestaciones/todasestaciones"
r = requests.get(url, headers=HEADERS)
print("Respuesta inicial de AEMET:", r.status_code)
respuesta = r.json()
print(respuesta)  # veremos el campo 'datos' con la URL temporal

# Paso 2: bajar los datos reales de la URL que nos dio
url_datos = respuesta["datos"]
datos = requests.get(url_datos).json()
print(f"\nTotal de estaciones recibidas: {len(datos)}\n")

# Paso 3: filtrar las de Soria
for est in datos:
    nombre = est.get("nombre", "")
    provincia = est.get("provincia", "")
    if "SORIA" in nombre.upper() or "SORIA" in provincia.upper():
        print(f"idema={est.get('indicativo')}  nombre={nombre}  provincia={provincia}")