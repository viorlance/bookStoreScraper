import scrapy
from bookScrape.items import BookItem

class BookspiderSpider(scrapy.Spider):
    name = "bookSpider"
    allowed_domains = ["librarius.md"]
    start_urls = ["https://librarius.md/ro/books"]



    def parse(self, response):
        books = response.css('div.anyproduct-card')
        for book in books:
            book_url = book.css('a::attr(href)').get()
            yield response.follow(book_url, callback = self.parse_book)

    def parse_book(self, response):
        book = BookItem()

        book['url'] = response.url
        book['name'] = response.css('h1.main-title::text').get(default = "")
        book['img_src'] = response.css('div._book__cover img::attr(src)').get(default = "")
        book['stock'] = response.css('div.product-book-price__stock ::text').get(default='')

        book['price'] = response.css('#addToCartButton::attr(data-price)').get(default="")
        discountDiv = response.css('div.product-book-price__discount')

        if discountDiv:
            book['old_price'] = discountDiv.css('del::text').get(default="")
            book['discountProcent'] = discountDiv.css('span.discount-badge::text').get(default="")
        else:
            book['old_price'] = ""
            book['discountProcent'] = ""

        props = {}
        props_rows = response.css('div.book-props-item')
        for row in props_rows:
            key = row.css('div.book-prop-name::text').get(default = '')
            value = row.css('div.book-prop-value::text').get(default = '')
            if key and value:
                props[key] = value
        book['props'] = props

        yield book