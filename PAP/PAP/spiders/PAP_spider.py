import scrapy

class ArticlesSpider(scrapy.Spider):
    name = "articles"

    allowed_domains = ["pap.pl"]
    start_urls = ["https://www.pap.pl/"]

    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 1,      # stop the spider after scraping 1000 items (double check this)!!!!!!!!!!!!!!!
        "DOWNLOAD_DELAY": 1,              # delay between download requests --> may help to not get blocked by the server
        "DEPTH_PRIORITY": 1,                # prioritize depth over breadth when crawling
    }

    async def start(self):
        # this is where the spider gets the request
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # callback from start takes us to this function, each callback takes us to a new function we can define
        yield from self.crawl_articles(response) # crawl articles and yield results here

    def crawl_articles(self, response):
        # this function follows all article links on the given page and parses them 
        # (parse_articles calls this function recursively to follow links inside articles) so set a limit on the number of items to scrape

        # article links are listed in a <a class="newsLink"> element
        # (getall(x) returns an iterable (like range(a, b)))

        # get all href links from <a class="newsLink"> elements
        for href in response.css("a.newsLink::attr(href)").getall():        # get all href links from <a class="newslink"> elements --> iterable
            # links are returned as relative links (doesn't include https://www.pap.pl)!!!

            if href.startswith("/aktualnosci/"):                            # check if the link is an article link
                yield response.follow(href, callback=self.parse_article)    # follow the link and parse the article

    def parse_article(self, response):
        # this is called by crawl_articles when an article link is found, the following is yielded from each article:

        # the content of the article is stored in an <article id="article"> element

        # yield the elements from the article page, which can be stored as a file later: (stored as a dict by default)
        yield{
            "title": response.css("h1::text").get(),
            "description": response.css("p.field--name-field-lead::text").get(),
            "date": response.css("div.articleInfo div.date::text").get(),
            "updated": response.css("div.articleInfo div.actualDate::text").get(),
            "content": "\n\n".join(response.css("article#article p::text").getall()) # joins all the content into a single string with double newlines between the <p> elements
        }

        # find links inside current article and repeat the process recursively:
        yield from self.crawl_articles(response)