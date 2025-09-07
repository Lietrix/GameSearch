import re
import scrapy
from datetime import datetime


class SteamChartsTopAllSpider(scrapy.Spider):
    name = "steamcharts_top_all"
    allowed_domains = ["steamcharts.com"]

    # Usage: scrapy crawl steamcharts_top_all -O data/top.json -a min_players=60000
    def __init__(self, min_players=None, max_pages=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_players = int(min_players) if min_players is not None else None
        self.max_pages = int(max_pages) if max_pages is not None else None
        self.page_count = 0

    start_urls = ["https://steamcharts.com/top/p.1"]

    def parse(self, response):
        self.page_count += 1
        rows = response.css("table.common-table tbody tr")
        if not rows:
            self.logger.info(f"[DONE] No rows found at {response.url} — stopping.")
            return

        crossed_threshold = False
        min_seen = None

        for row in rows:
            rank_txt   = self.clean_text(row.css("td:nth-child(1)::text").get())
            name_txt   = self.clean_text(row.css("td:nth-child(2) a::text").get())
            detail_rel = row.css("td:nth-child(2) a::attr(href)").get()
            avg_txt    = self.clean_text(row.css("td:nth-child(3)::text").get())
            peak_txt   = self.clean_text(row.css("td:nth-child(5)::text").get())

            avg_players  = self.clean_int(avg_txt)
            peak_players = self.clean_int(peak_txt)

            # NEW: app_id from the href (/app/<id>)
            app_id = None
            if detail_rel:
                m = re.search(r"/app/(\d+)", detail_rel)
                if m:
                    app_id = m.group(1)

            if avg_players is not None:
                min_seen = avg_players if min_seen is None else min(min_seen, avg_players)

            # Threshold: stop *before* following next if this page dips below
            if self.min_players is not None and avg_players is not None and avg_players < self.min_players:
                crossed_threshold = True
                break

            yield {
                "rank": self.clean_int(rank_txt.strip(".") if rank_txt else None),
                "name": name_txt,
                "detail_url": response.urljoin(detail_rel) if detail_rel else None,
                "app_id": app_id,  # <-- critical for DB
                "avg_players": avg_players,
                "peak_players": peak_players,
                "timestamp": datetime.utcnow().isoformat(),
            }

        self.logger.info(f"[PAGE {self.page_count}] url={response.url} min_avg_on_page={min_seen}")

        if crossed_threshold:
            self.logger.info(
                f"[STOP] Avg players fell below {self.min_players} on {response.url} — stopping."
            )
            return

        if self.max_pages is not None and self.page_count >= self.max_pages:
            self.logger.info(f"[STOP] Reached max_pages={self.max_pages} — stopping.")
            return

        # More robust “Next” detection (covers rel=next, class, and text cases)
        next_href = (
            response.css('a[rel="next"]::attr(href)').get()
            or response.css("a.page-link.next::attr(href)").get()
            or response.xpath('//a[contains(normalize-space(.), "Next")]/@href').get()
            or response.xpath('//li[contains(@class,"next")]/a/@href').get()
        )

        if next_href:
            self.logger.info(f"[NEXT] Following: {response.urljoin(next_href)}")
            yield response.follow(next_href, callback=self.parse)
        else:
            self.logger.info(f"[DONE] No next link found at {response.url} — crawl finished.")

    # Helpers
    def clean_text(self, value):
        return value.strip() if value else None

    def clean_int(self, value):
        if value is None:
            return None
        try:
            return int(value.replace(",", "").replace("+", "").replace("−", "-").replace(" ", ""))
        except ValueError:
            return None
