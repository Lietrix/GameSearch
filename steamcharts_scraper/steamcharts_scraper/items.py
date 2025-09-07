# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class SteamchartsScraperItem(scrapy.Item):
    app_id    = scrapy.Field()
    name      = scrapy.Field()
    current   = scrapy.Field()
    peak      = scrapy.Field()
    hours     = scrapy.Field()      # ← add this line
    timestamp = scrapy.Field()