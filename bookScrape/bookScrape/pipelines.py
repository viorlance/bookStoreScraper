from itemadapter import ItemAdapter
import re
from scrapy.exceptions import DropItem
import os
from dotenv import load_dotenv
from configs import scrapingLogger
import mysql.connector
import json

load_dotenv()

class BookscrapePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        adapter["name"] = adapter.get("name", "").strip()

        img = adapter.get("img_src", "")
        if img and img.startswith("/"):
            adapter["img_src"] = "https://librarius.md" + img
        elif not img:
            adapter["img_src"] = None

        adapter["stock"] = adapter.get("stock", "").strip()

        adapter['price'] = self.parse_price(adapter.get('price'))
        adapter['old_price'] = self.parse_price(adapter.get('old_price'))
        adapter['discount_procent'] = self.parse_price(adapter.get('discount_procent'))


        try:
            adapter["properties"] = {
                k.strip(): v.strip()
                for k, v in adapter.get("properties", {}).items()
            }
        except Exception:
            scrapingLogger.exception(
                "Drop item %s while processing properties",
                adapter.get("url")
            )
            raise DropItem()

        adapter["id"] = adapter.get("properties", {}).pop("Cod produs", None)
        if not adapter["id"]:
            scrapingLogger.warning(
                "Drop item %s invalid id",
                adapter.get("url")
            )
            raise DropItem()
        
        try:
            adapter["id"] = int(adapter["id"])
        except (TypeError, ValueError):
            scrapingLogger.warning(
                "Drop item %s invalid id",
                adapter.get("url")
            )
            raise DropItem()
        
        availability = {}
        for key,value in adapter.get("availability", {}).items():
            shopId = re.search(r"\b\d+\b", key)
            stock = value.strip()
            if shopId and stock:
                availability[int(shopId.group())] = stock
            else:
                scrapingLogger.warning(f"Can't process book's availability, processing shopId: {key}, processing stock: {value}, book: {adapter.get('url')}")
        
        adapter["availability"] = availability


        return item


    def parse_price(self, value):
        if not value:
            return None
        value = value.replace(',', '.')
        m = re.search(r'\b\d+(\.\d+)?\b', value)
        return float(m.group()) if m else None

class SaveBookToMySQLPipeline:
    
    def __init__(self):
        self.conn = mysql.connector.connect(
            host = os.getenv("DB_HOST"),
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD"),
            database = os.getenv("DB_NAME"),
            autocommit = True
        )

        self.cur = self.conn.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS books(
                id INT NOT NULL,
                url TEXT,
                name VARCHAR(255),
                img_src TEXT,
                stock VARCHAR(20),
                price DECIMAL(10,2),
                old_price DECIMAL(10,2),
                discount_procent DECIMAL(10,2),
                properties JSON,
                PRIMARY KEY(id)
            )
        """
        )

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS books_shops(
                bookId INT NOT NULL,
                shopId INT NOT NULL,
                stock VARCHAR(20),
                PRIMARY KEY(bookId, shopId),
                FOREIGN KEY (bookId) REFERENCES books(id),
                FOREIGN KEY (shopId) REFERENCES shops(id)
            )
        """)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        self.cur.execute("""
            INSERT INTO books (id, url, name, img_src, stock, price, old_price, discount_procent, properties)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                url = VALUES(url),
                name = VALUES(name),
                img_src = VALUES(img_src),
                stock = VALUES(stock),
                price = VALUES(price),
                old_price = VALUES(old_price),
                discount_procent = VALUES(discount_procent),
                properties = VALUES(properties)
        """,
            (
                adapter.get("id"),
                adapter.get("url"),
                adapter.get("name"),
                adapter.get("img_src"),
                adapter.get("stock"),
                adapter.get("price"),
                adapter.get("old_price"),
                adapter.get("discount_procent"),
                json.dumps(adapter.get("properties", {})),
            )
        )

        availabilities = adapter.get("availability", {})
        if availabilities:

            values = [(adapter["id"], shopId, stock) for shopId, stock in availabilities.items()]

            self.cur.executemany("""
                INSERT INTO books_shops (bookId, shopId, stock)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    stock = VALUES(stock)
            """, values)

        return item
        
    
    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

class ShopscrapePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        idDigits = re.search(r'\b\d+\b', adapter.get("id", ""))
        if idDigits :
            adapter["id"] = int(idDigits.group())
        else:
            if "online" in adapter.get("id", ""):
                scrapingLogger.warning(f"Can't process shop id, input data:{adapter['id']}")
            raise DropItem()
        
        adapter["address"] = adapter.get("address", "").strip()
        adapter["phone"] = adapter.get("phone", "").strip()
        try:
            schedule = adapter.get("schedule", [])
            schedule = [ row.strip() for row in schedule]
            adapter["schedule"] = ", ".join(schedule)
        except Exception:
            scrapingLogger.exception(f"Schedule process error at {adapter['id']}: ")
            adapter["schedule"] = ""


        return item
    
class SaveShopToMySQLPipeline:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host = os.getenv("DB_HOST"),
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD"),
            database = os.getenv("DB_NAME"),
            autocommit = True   
        )

        self.cur = self.conn.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS shops(
                id INT NOT NULL,
                address VARCHAR(255),
                phone VARCHAR(50),
                schedule VARCHAR(255),
                PRIMARY KEY(id)
            )
        """)


    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        self.cur.execute("""
            INSERT INTO shops (id, address, phone, schedule)
            VALUES(%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                address = VALUES(address),
                phone = VALUES(phone),
                schedule = VALUES(schedule)
        """,(
                adapter.get("id"),
                adapter.get("address"),
                adapter.get("phone"),
                adapter.get("schedule")
            )
        )

        return item


    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()