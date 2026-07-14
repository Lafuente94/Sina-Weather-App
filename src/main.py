"""
API de datos meteo de Soria.
Lee de Neon (Postgres) y expone JSON para la web app.

Ejecutar en local:
    pip install fastapi "uvicorn[standard]" psycopg2-binary python-dotenv
    export DATABASE_URL="postgresql://...neon..."
    uvicorn main:app --reload

La app NUNCA se conecta a Neon directamente: solo llama a esta API.
"""

import os
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# La misma variable que ya usas en tu workflow / script.
DB_URL = os.environ["DB_URL"]

# ---- AJUSTA AQUI SI TUS NOMBRES NO COINCIDEN ----
TABLA = "observaciones"      # <-- nombre real de tu tabla
COL_FECHA = "fint"           # columna timestamp de la observacion
# Campos numericos que quieres poder graficar (nombre en la tabla)
CAMPOS = ["ta", "tamax", "tamin", "hr", "pres", "vv", "vmax", "prec", "ts", "tpr", "vis", "inso"]
# -------------------------------------------------

app = FastAPI(title="Meteo Soria API")

# Permite que la web (desde otro dominio) llame a la API.
# Para empezar dejamos "*"; luego conviene restringir al dominio real de tu web.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_conn():
    return psycopg2.connect(DB_URL)


@app.get("/health")
def health():
    """Comprueba que la API arranca y conecta a la base."""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/latest")
def latest():
    """Ultima observacion registrada (todos los campos)."""
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(f"SELECT * FROM {TABLA} ORDER BY {COL_FECHA} DESC LIMIT 1")
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sin datos")
    return _jsonable(row)


@app.get("/api/series")
def series(
    campo: str = Query("ta", description="Campo a graficar, p.ej. ta, hr, pres"),
    horas: int = Query(48, ge=1, le=24 * 30, description="Cuantas horas hacia atras"),
):
    """
    Serie temporal de un campo, de las ultimas N horas.
    Devuelve una lista de {t, v} lista para pintar una grafica.
    """
    if campo not in CAMPOS:
        raise HTTPException(
            status_code=400,
            detail=f"Campo no permitido. Validos: {', '.join(CAMPOS)}",
        )

    sql = f"""
        SELECT {COL_FECHA} AS t, {campo} AS v
        FROM {TABLA}
        WHERE {COL_FECHA} >= now() - make_interval(hours => %s)
          AND {campo} IS NOT NULL
        ORDER BY {COL_FECHA} ASC
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (horas,))
        rows = cur.fetchall()

    return {
        "campo": campo,
        "horas": horas,
        "puntos": [{"t": _iso(t), "v": float(v)} for (t, v) in rows],
    }


def _iso(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _jsonable(row: dict):
    out = {}
    for k, v in row.items():
        out[k] = _iso(v) if isinstance(v, datetime) else v
    return out