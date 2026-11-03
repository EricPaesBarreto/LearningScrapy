import scrapy
import re

class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["gutenburg.org"]
    start_urls = ["https://www.gutenberg.org/ebooks/categories"]

    
    def __init__(self, category=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category

    custom_settings = {
            "CLOSESPIDER_ITEMCOUNT": 1,
            "DOWNLOAD_DELAY": 1,
            "DEPTH_PRIORITY": 1,
            "FEEDS": {
                "outputs/NFP_articles.json": {
                    "format": "json",
                    "encoding": "utf-8",
                    "overwrite": True,
                }
            }
        }

    async def start(self):
        for url in self.start_urls:
            yield scrapy.request(url=url, callback=self.parse)

    def parse(self, response):
        yield from self.crawl_categories(response)

    def crawl_categories(self, response):
        if self.category:
            # crawl the specified category
            category_link = category_link = response.css(f"a[href*='{self.category}']::attr(href)").get() # get the link to the category page
            if category_link:
                yield self.parse_books(response.follow(category_link))

        else:
            # crawl all categories
            for href in response.css("div.book-list ul li a::attr(href)").getall():
                yield self.parse_books(response.follow(href))

    def parse_books(self, response):
        # <a class="link" href="/ebooks/2701" accesskey="1">
        for href in response.css("li.booklink a.link::attr(href)").getall():
            yield response.follow(href, callback=self.parse_book)

        if response.css("a[title*='Go to the next page of results.']::attr(href)").get():
            next_page = response.css("a.next_page::attr(href)").get()
            yield response.follow(next_page, callback=self.parse_books)

    def parse_book(self, book):
        author_text = book.xpath("//tr[./th[normalize-space()='Author']]//td//a/text()").get()

        author = None
        author_birth = None
        author_death = None

        if author_text:
            match = re.match(r"^\s*([^,]+),\s*([^,]+)(?:,\s*(\d{4})-(\d{4})?)?",author_text)

        if match:
            author = match.group(1) + " " + match.group(2)
            author_birth = match.group(3)
            author_death = match.group(4)

        yield {
            "title": book.css("h1#book_title::text").get(),
            "language": book.xpath("//tr[./th[normalize-space()='Language']]//td/text()").get(),
            "author": author,
            "author-birth": author_birth,
            "author-death": author_death,
            "ISBN": book.xpath("//tr[./th[normalize-space()='ISBN (HTML)']]//td/text()").get(),
            "copyright": book.xpath("//tr[./th[normalize-space()='Copyright']]//td/text()").get(),

            # seems to be: sub_topic -- genre
            # can also be: sub_topic
            "topics": (self.get_topics(book)),
        }

    def get_topics(self, book):
        subjects = book.xpath("//tr[./th[normalize-space()='Subject']]//td//a/text()").getall()

        topics = {}

        for topic in subjects:
            # filter out non-standard topic descriptions
            if re.match(r"^[^,]+,\s*[^,]+,\s*\d{4}-\d{4}$", topic):
                continue

            split = topic.split(" -- ", 1)

            if (len(split) > 1):
                topics[split[1]] = ""
                topics[split[0]] = split[1]
            else:
                topics[split[0]] = ""
            
        return topics