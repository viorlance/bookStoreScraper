import scrapy


class BookscrapeItem(scrapy.Item):
    pass

class BookItem(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    img_src = scrapy.Field()
    stock = scrapy.Field()
    price = scrapy.Field()
    old_price = scrapy.Field()
    discount_procent = scrapy.Field()
    properties = scrapy.Field()