# db/load_snapshot.py
import json, sqlite3, sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python load_snapshot.py <path-to-snapshot.json>")
        sys.exit(1)

    snap_path = Path(sys.argv[1]).resolve()
    if not snap_path.exists():
        print(f"❌ File not found: {snap_path}")
        sys.exit(1)

    db_path = Path(__file__).resolve().parent / "steamcharts.db"
    try:
        rows = json.loads(snap_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Failed to read/parse JSON: {e}")
        sys.exit(1)

    # Support either a list of objects or a single object
    if isinstance(rows, dict):
        rows = [rows]

    total = len(rows)
    inserted_snapshots = 0
    seeded_apps = 0
    skipped_no_appid = 0

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute("PRAGMA foreign_keys = ON")

        for r in rows:
            app_id = r.get("app_id")
            if not app_id:
                skipped_no_appid += 1
                continue

            # Seed/refresh minimal app name from snapshot (non-destructive)
            cur.execute("""
                INSERT INTO apps (app_id, name)
                VALUES (?, ?)
                ON CONFLICT(app_id) DO UPDATE SET
                  name = COALESCE(excluded.name, apps.name)
            """, (int(app_id), r.get("name")))
            seeded_apps += 1

            # Insert/replace snapshot row
            cur.execute("""
                INSERT OR REPLACE INTO snapshots
                  (ts, app_id, rank, avg_players, peak_players, detail_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                r.get("timestamp"),
                int(app_id),
                r.get("rank"),
                r.get("avg_players"),
                r.get("peak_players"),
                r.get("detail_url"),
            ))
            inserted_snapshots += 1

        con.commit()

    print(f"✅ Loaded snapshot into {db_path}")
    print(f"   Read records:          {total}")
    print(f"   Inserted snapshots:    {inserted_snapshots}")
    print(f"   Seeded/updated apps:   {seeded_apps}")
    print(f"   Skipped (no app_id):   {skipped_no_appid}")

if __name__ == "__main__":
    main()
