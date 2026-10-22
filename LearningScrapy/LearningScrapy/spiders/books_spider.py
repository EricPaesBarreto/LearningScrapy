import scrapy

class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["gutenburg.org"]
    start_urls = ["https://www.gutenberg.org"]