import logging

scrapingLogger = logging.getLogger('scrapingLogger')
handler = logging.FileHandler('scraping.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
scrapingLogger.addHandler(handler)
scrapingLogger.setLevel(logging.INFO)