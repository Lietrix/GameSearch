# steamcharts_scraper/db/make_app_ids.py
import argparse, sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# DB lives in this folder; data/ lives two levels up (GameSearch/)
DB_PATH = Path(__file__).resolve().parent / "steamcharts.db"
ROOT    = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def main():
    p = argparse.ArgumentParser(description="Export app_ids from SQLite to a text file.")
    p.add_argument("--source", choices=["apps", "snapshots", "union"], default="apps",
                   help="Where to read ids from: apps table, snapshots table, or union of both.")
    p.add_argument("--stale-days", type=int, default=0,
                   help="If >0, include only apps with NULL last_refreshed or older than N days (apps table).")
    p.add_argument("--out", default=str(DATA_DIR / "app_ids_from_db.txt"),
                   help="Output file (one app_id per line).")
    args = p.parse_args()

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        if args.source == "apps":
            base_sql = "SELECT app_id FROM apps"
        elif args.source == "snapshots":
            base_sql = "SELECT DISTINCT app_id FROM snapshots"
        else:
            base_sql = """
                SELECT app_id FROM apps
                UNION
                SELECT DISTINCT app_id FROM snapshots
            """

        params = ()
        if args.stale_days and args.source != "snapshots":
            cutoff = (datetime.utcnow() - timedelta(days=args.stale_days)).isoformat()
            base_sql = f"""
                SELECT t.app_id
                FROM ({base_sql}) AS t
                LEFT JOIN apps a ON a.app_id = t.app_id
                WHERE a.last_refreshed IS NULL OR a.last_refreshed < ?
            """
            params = (cutoff,)

        rows = cur.execute(base_sql, params).fetchall()

    ids = sorted({int(r[0]) for r in rows if r and r[0] is not None})
    out_path = Path(args.out)
    out_path.write_text("\n".join(map(str, ids)), encoding="utf-8")

    print(f"Wrote {len(ids)} app_ids -> {out_path}")

if __name__ == "__main__":
    main()
