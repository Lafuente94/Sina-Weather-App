import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env

API_KEY = os.getenv("AEMET_API_KEY")

BASE = "https://opendata.aemet.es/opendata/api"
HEADERS = {"api_key": API_KEY}

IDEMA = "2030"  # Soria capital

# Paso 1: pedir la observación. Como siempre, AEMET nos da una URL primero.
url = f"{BASE}/observacion/convencional/datos/estacion/{IDEMA}"
r = requests.get(url, headers=HEADERS)
print("Respuesta inicial de AEMET:", r.status_code)
respuesta = r.json()
print(respuesta)

# Paso 2: bajar los datos reales
url_datos = respuesta["datos"]
datos = requests.get(url_datos).json()

print(f"\nNúmero de observaciones recibidas: {len(datos)}\n")

# AEMET devuelve varias observaciones (una por cada hora disponible).
# Miramos la última (la más reciente) con todos sus campos.
ultima = datos[-1]
print("=== ÚLTIMA OBSERVACIÓN, todos los campos ===")
print(json.dumps(ultima, indent=2, ensure_ascii=False))