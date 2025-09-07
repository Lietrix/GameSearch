# db/upsert_catalog.py
import json, sqlite3, sys
from pathlib import Path

def to_json_text(x):
    import json as _j
    return None if x in (None, [], {}) else _j.dumps(x, ensure_ascii=False)

def main():
    if len(sys.argv) < 2:
        print("Usage: python upsert_catalog.py <path-to-catalog.json>")
        sys.exit(1)

    cat_path = Path(sys.argv[1]).resolve()
    if not cat_path.exists():
        print(f"File not found: {cat_path}")
        sys.exit(1)

    db_path = Path(__file__).resolve().parent / "steamcharts.db"
    rows = json.loads(cat_path.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = [rows]

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        for r in rows:
            app_id = r.get("app_id")
            if not app_id:
                continue

            cur.execute("""
                INSERT INTO apps (
                  app_id, name, short_description, release_date,
                  developers, publishers, genres, categories,
                  store_app_url, last_refreshed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(app_id) DO UPDATE SET
                  name = COALESCE(excluded.name, apps.name),
                  short_description = COALESCE(excluded.short_description, apps.short_description),
                  release_date = COALESCE(excluded.release_date, apps.release_date),
                  developers = COALESCE(excluded.developers, apps.developers),
                  publishers = COALESCE(excluded.publishers, apps.publishers),
                  genres = COALESCE(excluded.genres, apps.genres),
                  categories = COALESCE(excluded.categories, apps.categories),
                  store_app_url = COALESCE(excluded.store_app_url, apps.store_app_url),
                  last_refreshed = excluded.last_refreshed
            """, (
                int(app_id),
                r.get("name"),
                r.get("short_description"),
                r.get("release_date"),
                to_json_text(r.get("developers")),
                to_json_text(r.get("publishers")),
                to_json_text(r.get("genres")),
                to_json_text(r.get("categories")),
                r.get("store_app_url"),
                r.get("last_refreshed"),
            ))
        con.commit()

    print(f"✅ Upserted catalog into {db_path}")

if __name__ == "__main__":
    main()
