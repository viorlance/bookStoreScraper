from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import signals
from scrapy.signalmanager import dispatcher

from bookScrape.spiders.shopSpider import ShopspiderSpider
from bookScrape.spiders.bookSpider import BookspiderSpider

from dotenv import load_dotenv
load_dotenv()

def spider_closed(spider, reason):
    print(f"Spider {spider.name} closed: {reason}")

dispatcher.connect(spider_closed, signal=signals.spider_closed)

process = CrawlerProcess(get_project_settings())

process.crawl(ShopspiderSpider)
process.crawl(BookspiderSpider)

process.start()
