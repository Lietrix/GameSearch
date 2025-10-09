# app.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Optional
from datetime import datetime

DB_PATH = r"C:\GameSearch\steamcharts_scraper\data\steamcharts.db"  # <- adjust if needed

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameRow(BaseModel):
    app_id: str
    name: str
    current: int
    peak: int
    hours: Optional[int] = None
    timestamp: str

class ApiResponse(BaseModel):
    data: List[GameRow]
    total: int
    page: int
    page_size: int

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Optional: run once to create helpful indexes
# CREATE INDEX IF NOT EXISTS idx_items_appid ON steam_items(app_id);
# CREATE INDEX IF NOT EXISTS idx_items_name ON steam_items(name);
# CREATE INDEX IF NOT EXISTS idx_items_timestamp ON steam_items(timestamp);
# CREATE INDEX IF NOT EXISTS idx_items_current ON steam_items(current);
# Adjust table/column names to your schema.

@app.get("/api/search", response_model=ApiResponse)
def search(
    q: str = Query("", description="Name substring or exact App ID"),
    sort: str = Query("-current"),
    page: int = 1,
    page_size: int = 25,
    min_current: int = 0,
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = None,
):
    # Map sort keys to SQL
    key = "current"
    direction = "DESC"
    if sort.startswith("+") or not sort.startswith(("+", "-")):
        direction = "ASC"
    raw_key = sort[1:] if sort[:1] in {"+", "-"} else sort
    if raw_key in {"current", "peak", "timestamp", "name"}:
        key = raw_key

    where, params = [], []

    # Text / AppID query
    if q:
        if q.isdigit():
            where.append("(app_id = ? OR name LIKE ?)")
            params.extend([q, f"%{q}%"])
        else:
            where.append("name LIKE ?")
            params.append(f"%{q}%")

    # Min current
    if min_current > 0:
        where.append("current >= ?")
        params.append(min_current)

    # Date range
    if from_:
        where.append("timestamp >= ?")
        params.append(from_)
    if to:
        where.append("timestamp <= ?")
        params.append(to)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    order_sql = f"ORDER BY {key} {direction}"
    limit_sql = "LIMIT ? OFFSET ?"

    conn = get_conn()
    cur = conn.cursor()

    # total count
    total_sql = f"SELECT COUNT(*) AS c FROM steam_items {where_sql};"
    cur.execute(total_sql, params)
    total = cur.fetchone()["c"]

    # page results
    offset = (page - 1) * page_size
    data_sql = f"""
        SELECT app_id, name, current, peak, hours, timestamp
        FROM steam_items
        {where_sql}
        {order_sql}
        {limit_sql};
    """
    cur.execute(data_sql, (*params, page_size, offset))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    # ensure types / formatting
    normalized = []
    for r in rows:
        normalized.append(
            GameRow(
                app_id=str(r["app_id"]),
                name=r["name"],
                current=int(r["current"]),
                peak=int(r["peak"]),
                hours=(int(r["hours"]) if r.get("hours") is not None else None),
                timestamp=(r["timestamp"] if isinstance(r["timestamp"], str) else datetime.utcfromtimestamp(r["timestamp"]).isoformat()),
            )
        )

    return ApiResponse(data=normalized, total=total, page=page, page_size=page_size)
