import scrapy
from bookScrape.items import ShopItem

class ShopspiderSpider(scrapy.Spider):
    name = "shopSpider"
    allowed_domains = ["librarius.md", "www.librarius.md"]
    start_urls = ["https://librarius.md/ro/points-of-sales"]

    custom_settings = {
        "ITEM_PIPELINES": {
            "bookScrape.pipelines.ShopscrapePipeline": 300,
            "bookScrape.pipelines.SaveShopToMySQLPipeline": 400 
        }
    }


    def parse(self, response):

        shopDivs = response.css("div.shop-item")
        for shopDiv in shopDivs:
            shop = ShopItem()

            shop["id"] = shopDiv.css("label a::text").get(default="")
            shop["address"] = shopDiv.xpath('./div[1]//a[@title="address"]//text()').get(default="")
            shop["phone"] = shopDiv.xpath('./div[2]//a[@title="phone"]//text()').get(default="")
            shop["schedule"] = shopDiv.xpath('./div[3]/small/text()').getall()

            yield shop