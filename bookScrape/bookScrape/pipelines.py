from itemadapter import ItemAdapter
import re
from scrapy.exceptions import DropItem
import os
from dotenv import load_dotenv

load_dotenv()

class BookscrapePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        price = adapter['price']
        old_price = adapter['old_price']
        discount = adapter['discountProcent']

        price = price.replace(',','.')
        old_price = old_price.replace(',','.')
        discount = discount.replace(',','.')

        price = re.search(r'\b\d+(\.\d+)?\b', price)
        old_price = re.search(r'\b\d+(\.\d+)?\b', old_price)
        discount = re.search(r'\b\d+(\.\d+)?\b', discount)

        if price:
            price = float(price.group())
        if old_price:
            old_price = float(old_price.group())
        if discount:
            discount = float(discount.group())
        
        adapter['price'] = price
        adapter['old_price'] = old_price
        adapter['discountProcent'] = discount

        props = adapter.get('props', {})
        item_dict = dict(adapter.asdict())
        adapter = ItemAdapter(item_dict)
        for key,value in props.items():
            if key and value:
                clean_key = key.strip().replace(' ','_')
                adapter[clean_key] = value
        adapter.pop('props', None)

        for key in adapter.keys():
            adapter[key] = self.clean(adapter[key])

        try:
            if adapter['img_src'][0] == '/':
                adapter['img_src'] = 'https://librarius.md' + adapter["img_src"]
        except:
            adapter['img_src'] = None

        adapter['id'] = int(adapter.pop('Cod_produs', None))
        if not adapter.get('id'):
            raise DropItem(f"Item fără ID eliminat: {adapter.get('url')}")

        return item_dict
    

    def clean(self, value):
        if isinstance(value, str):
            return value.strip()
        else:
            return value

import mysql.connector

class SaveToMySQLPipeline:
    
    def __init__(self):
        self.conn = mysql.connector.connect(
            host = os.getenv("DB_HOST"),
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD"),
            database = os.getenv("DB_NAME")
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
                discountProcent DECIMAL(10,2),
                PRIMARY KEY(id)
            )
        """
        )

        self.conn.commit()

    def process_item(self, item, spider):

        self.cur.execute("SHOW COLUMNS FROM books")
        existing_columns = {row[0] for row in self.cur.fetchall()}
        for key in item.keys():
            if key not in existing_columns:
                self.cur.execute(f"ALTER TABLE books ADD COLUMN `{key}` VARCHAR(255)")

        item_cols = ', '.join(item.keys())
        placeholders = ', '.join(['%s'] * len(item))
        update_clause = ", ".join([f"{k}=VALUES({k})" for k in item.keys() if k != "id"])
        sql = f"""
            INSERT INTO books ({item_cols}) VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause}
        """
        self.cur.execute(sql, list(item.values()))

        self.conn.commit()
        return item
    
    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
