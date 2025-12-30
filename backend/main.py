# backend/main.py
import os
import re
import sqlite3
from typing import List, Literal, Optional, Tuple
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ======== CONFIG ========
DB_PATH = os.getenv("GSE_DB", r"C:\\GameSearch\\steamcharts_scraper\\db\\steamcharts.db")
TABLE_NAME = os.getenv("GSE_TABLE", "steamcharts_top")

# Column mapping — edit if your table uses different names
COL_APP_ID   = os.getenv("GSE_COL_APP_ID",   "app_id")
COL_NAME     = os.getenv("GSE_COL_NAME",     "name")
COL_CUR      = os.getenv("GSE_COL_CUR",      "current_players")
COL_PEAK24   = os.getenv("GSE_COL_PEAK24",   "peak_24h")
COL_PEAK_ALL = os.getenv("GSE_COL_PEAK_ALL", "all_time_peak")

SORT_KEYS = {
    "name": f"LOWER({COL_NAME}) ASC",
    "-name": f"LOWER({COL_NAME}) DESC",
    "current": f"{COL_CUR} DESC",
    "-current": f"{COL_CUR} ASC",
    "peak24": f"{COL_PEAK24} DESC",
    "-peak24": f"{COL_PEAK24} ASC",
    "peak": f"{COL_PEAK_ALL} DESC",
    "-peak": f"{COL_PEAK_ALL} ASC",
}

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def _assert_ident(x: str) -> str:
    if not IDENT_RE.match(x):
        raise ValueError(f"Invalid identifier: {x}")
    return x

# Validate identifiers early (defense-in-depth against env misconfig)
for ident in [TABLE_NAME, COL_APP_ID, COL_NAME, COL_CUR, COL_PEAK24, COL_PEAK_ALL]:
    _assert_ident(ident)

app = FastAPI(title="GameSearch API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Game(BaseModel):
    app_id: int
    name: str
    current: Optional[int] = None
    peak24: Optional[int] = None
    peak: Optional[int] = None

class PagedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[Game]

def get_conn() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail=f"DB not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/games", response_model=PagedResponse)
def list_games(
    q: Optional[str] = Query(None, description="Search by name substring"),
    sort: Optional[Literal["name","-name","current","-current","peak24","-peak24","peak","-peak"]] = "current",
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
):
    offset = (page - 1) * size
    where = []
    params: Tuple = tuple()

    if q:
        where.append(f"LOWER({COL_NAME}) LIKE ?")
        params += (f"%{q.lower()}%",)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    order_sql = f" ORDER BY {SORT_KEYS.get(sort or 'current')}"

    base_cols = f"{COL_APP_ID} AS app_id, {COL_NAME} AS name, " \
                f"{COL_CUR} AS current, {COL_PEAK24} AS peak24, {COL_PEAK_ALL} AS peak"

    with get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM {_assert_ident(TABLE_NAME)}{where_sql}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT {base_cols} FROM {TABLE_NAME}{where_sql}{order_sql} LIMIT ? OFFSET ?",
            params + (size, offset),
        ).fetchall()

    items = [Game(**dict(r)) for r in rows]
    return PagedResponse(total=total, page=page, size=size, items=items)

@app.get("/games/{app_id}", response_model=Game)
def get_game(app_id: int):
    base_cols = f"{COL_APP_ID} AS app_id, {COL_NAME} AS name, {COL_CUR} AS current, {COL_PEAK24} AS peak24, {COL_PEAK_ALL} AS peak"
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT {base_cols} FROM {TABLE_NAME} WHERE {COL_APP_ID} = ?",
            (app_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return Game(**dict(row))

@app.on_event("startup")
def ensure_indexes():
    with get_conn() as conn:
        # Helpful indexes on the REAL tables
        conn.execute("CREATE INDEX IF NOT EXISTS idx_apps_name ON apps(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_app_id ON snapshots(app_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(ts)")
        conn.commit()

        # View that matches what the API expects (latest snapshot per app)
        conn.execute("DROP VIEW IF EXISTS steamcharts_top")
        conn.execute("""
        CREATE VIEW IF NOT EXISTS steamcharts_top AS
        SELECT
        a.app_id            AS app_id,
        a.name              AS name,
        s.avg_players       AS current_players,
        s.peak_players      AS peak_24h,
        s.peak_players      AS all_time_peak
        FROM apps a
        JOIN snapshots s
        ON s.app_id = a.app_id
        WHERE s.ts = (
        SELECT MAX(s2.ts)
        FROM snapshots s2
        WHERE s2.app_id = a.app_id
        )
        """)
        conn.commit()
