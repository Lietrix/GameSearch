# db/create_db.py
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "steamcharts.db"
SCHEMA_PATH = ROOT / "schema.sql"

try:
    if not SCHEMA_PATH.exists():
        print(f"❌ Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as con, open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        con.executescript(f.read())

    print(f"✅ Database schema created or updated successfully.")
    print(f"   Location: {DB_PATH}")

except Exception as e:
    print(f"❌ Failed to create/update schema: {e}")
    sys.exit(1)
