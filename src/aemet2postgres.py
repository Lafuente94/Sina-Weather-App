import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os

load_dotenv()  # Carga las variables de entorno desde el archivo .env

API_KEY = os.getenv("AEMET_API_KEY")
DB_URL = os.getenv("DB_URL")

BASE = "https://opendata.aemet.es/opendata/api"
HEADERS = {"api_key": API_KEY}
IDEMA = "2030"

# --- Crear la tabla (solo la primera vez; si ya existe, no hace nada) ---
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS observaciones (
    idema     TEXT NOT NULL,
    fint      TIMESTAMPTZ NOT NULL,
    ta        DOUBLE PRECISION,
    tamin     DOUBLE PRECISION,
    tamax     DOUBLE PRECISION,
    hr        DOUBLE PRECISION,
    prec      DOUBLE PRECISION,
    vv        DOUBLE PRECISION,
    vmax      DOUBLE PRECISION,
    dv        DOUBLE PRECISION,
    dmax      DOUBLE PRECISION,
    stdvv     DOUBLE PRECISION,
    stddv     DOUBLE PRECISION,
    pres      DOUBLE PRECISION,
    tpr       DOUBLE PRECISION,
    ts        DOUBLE PRECISION,
    tss5cm    DOUBLE PRECISION,
    tss20cm   DOUBLE PRECISION,
    vis       DOUBLE PRECISION,
    inso      DOUBLE PRECISION,
    pacutp    DOUBLE PRECISION,
    geo850    DOUBLE PRECISION,
    lon       DOUBLE PRECISION,
    lat       DOUBLE PRECISION,
    alt       DOUBLE PRECISION,
    ubi       TEXT,
    PRIMARY KEY (idema, fint)
);
"""

# Campos que vamos a extraer de cada observación, en orden
CAMPOS = ["idema","fint","ta","tamin","tamax","hr","prec","vv","vmax","dv","dmax",
          "stdvv","stddv","pres","tpr","ts","tss5cm","tss20cm","vis","inso",
          "pacutp","geo850","lon","lat","alt","ubi"]

def bajar_observaciones():
    url = f"{BASE}/observacion/convencional/datos/estacion/{IDEMA}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    url_datos = r.json()["datos"]
    return requests.get(url_datos).json()

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # 1. Crear tabla
    cur.execute(CREATE_SQL)
    conn.commit()
    print("Tabla lista.")

    # 2. Bajar observaciones
    datos = bajar_observaciones()
    print(f"Recibidas {len(datos)} observaciones de AEMET.")

    # 3. Preparar filas (usamos .get para que un campo ausente sea NULL)
    filas = [tuple(obs.get(c) for c in CAMPOS) for obs in datos]

    # 4. Insertar. ON CONFLICT evita duplicados si volvemos a meter la misma hora.
    insert_sql = f"""
        INSERT INTO observaciones ({",".join(CAMPOS)})
        VALUES %s
        ON CONFLICT (idema, fint) DO NOTHING
    """
    execute_values(cur, insert_sql, filas)
    conn.commit()
    print(f"Insertadas (nuevas): {cur.rowcount}")

    # 5. Comprobar cuántas hay en total
    cur.execute("SELECT COUNT(*) FROM observaciones;")
    print(f"Total en la tabla ahora: {cur.fetchone()[0]}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()