import scrapy
from bookScrape.items import BookItem
from configs import scrapingLogger
class BookspiderSpider(scrapy.Spider):
    name = "bookSpider"
    allowed_domains = ["librarius.md", "www.librarius.md"]
    start_urls = ["https://librarius.md/ro/books/page/1"]



    def parse(self, response):
        book_urls = response.css('div.anyproduct-card a::attr(href)').getall()
        scrapingLogger.info(f"{len(book_urls)} book urls at {response.url}")
        for book_url in book_urls:
            if book_url:
                yield response.follow(response.urljoin(book_url), callback=self.parse_book)

        next_page = response.css('li.page-item.active + li.page-item')
        if next_page:
            next_page_num = next_page.css('::text').get()
            if int(next_page_num) < 11:
                next_page_url = next_page.css('a::attr(href)').get()
                yield response.follow(next_page_url, callback = self.parse)

    def parse_book(self, response):
        book = BookItem()

        book['url'] = response.url
        book['name'] = response.css('h1.main-title::text').get(default = "")
        book['img_src'] = response.css('div._book__cover img::attr(src)').get(default = "")
        book['stock'] = response.css('div.product-book-price__stock ::text').get(default="")

        book['price'] = response.css('#addToCartButton::attr(data-price)').get(default="")
        discountDiv = response.css('div.product-book-price__discount')

        if discountDiv:
            book['old_price'] = discountDiv.css('del::text').get(default="")
            book['discount_procent'] = discountDiv.css('span.discount-badge::text').get(default="")
        else:
            book['old_price'] = ""
            book['discount_procent'] = ""

        properties = {}
        properties_rows = response.css('div.book-props-item')
        for row in properties_rows:
            key = row.css('div.book-prop-name *::text').get(default = "")
            value = row.css('div.book-prop-value *::text').get(default = "")
            if key and value:
                properties[key] = value
                
        book['properties'] = properties

        yield book