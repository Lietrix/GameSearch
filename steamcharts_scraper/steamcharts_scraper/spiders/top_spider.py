import scrapy
from datetime import datetime
from steamcharts_scraper.items import SteamchartsScraperItem

class AllTopGamesSpider(scrapy.Spider):
    name = "steamcharts_top"
    allowed_domains = ["steamcharts.com"]

    def start_requests(self):
        base_url = "https://steamcharts.com/top/p."
        for page in range(1, 101):  # adjust max page as needed
            yield scrapy.Request(url=f"{base_url}{page}", callback=self.parse)

    def parse(self, response):
        for row in response.css("table#top-games.common-table tbody tr"):
            cells = row.xpath("./td")
            item = SteamchartsScraperItem(
                app_id    = cells[1].xpath("a/@href").re_first(r"/app/(\d+)"),
                name      = cells[1].xpath("normalize-space(.//a/text())").get(),
                current   = cells[2].xpath("normalize-space(.)").get().replace(",", ""),
                peak      = cells[4].xpath("normalize-space(.)").get().replace(",", ""),
                hours     = cells[5].xpath("normalize-space(.)").get().replace(",", ""),
                timestamp = datetime.utcnow().isoformat()
            )
            yield item