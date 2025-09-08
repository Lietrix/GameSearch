import json
from datetime import datetime, timezone
from pathlib import Path

import scrapy

APPDETAILS = "https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"


class SteamAppCatalogSpider(scrapy.Spider):
    name = "steam_app_catalog"
    allowed_domains = ["store.steampowered.com"]

    # Usage:
    # scrapy crawl steam_app_catalog -O data/catalog.json -a app_ids_file=data/latest_app_ids.txt -a stale_days=30
    def __init__(self, app_ids_file=None, stale_days="30", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_ids_file = app_ids_file
        self.stale_days = int(stale_days)

    def start_requests(self):
        if not self.app_ids_file:
            raise RuntimeError("Provide -a app_ids_file=<path> (one app_id per line).")

        path = Path(self.app_ids_file)
        if not path.exists():
            raise RuntimeError(f"app_ids_file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                appid = line.strip()
                if not appid or not appid.isdigit():
                    continue
                url = APPDETAILS.format(appid=appid)
                # keep it polite, use JSON accept header
                yield scrapy.Request(
                    url,
                    headers={"Accept": "application/json"},
                    cb_kwargs={"appid": appid},
                    dont_filter=True,
                )

    def parse(self, response, appid):
        try:
            payload = json.loads(response.text)
            node = payload.get(str(appid), {})
        except Exception:
            node = {}

        if not node.get("success") or "data" not in node:
            # Missing/age-gated/delisted: skip silently
            return

        d = node["data"]

        # Helper to pull list-of-dicts -> list of descriptions
        def _desc_list(key):
            return [x.get("description") for x in d.get(key, []) if isinstance(x, dict) and x.get("description")] or None

        item = {
            "app_id": int(appid),
            "name": d.get("name"),
            "short_description": (d.get("short_description") or "").strip() or None,
            "release_date": (d.get("release_date") or {}).get("date"),
            "developers": d.get("developers") or None,   # lists
            "publishers": d.get("publishers") or None,   # lists
            "genres": _desc_list("genres"),
            "categories": _desc_list("categories"),
            "price_overview": d.get("price_overview") or None,  # dict or None
            "store_app_url": f"https://store.steampowered.com/app/{appid}/",
            "last_refreshed": datetime.now(timezone.utc).isoformat(),
        }
        yield item
