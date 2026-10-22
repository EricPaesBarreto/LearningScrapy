import scrapy

class NewsSpider(scrapy.Spider):
    name = "news"

    allowed_domains = ["notesfrompoland.com"]
    start_urls = ["https://notesfrompoland.com/category/news/page/1/"]

    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 1,      # stop the spider after scraping 1000 items (double check this)!!!!!!!!!!!!!!!
        "DOWNLOAD_DELAY": 1,              # delay between download requests --> may help to not get blocked by the server
        "DEPTH_PRIORITY": 1,                # prioritize depth over breadth when crawling
        "FEEDS": {
            "outputs/NFP_articles.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
            }
        }
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

        # (getall(x) returns an iterable (like range(a, b)))

        # get all href links from <a class="newsLink"> elements
        for href in response.css("h2.entry-title a::attr(href)").getall():        # get all href links from <a class="newslink"> elements --> iterable
            # links are returned as relative links (doesn't include the base url)!!!

            yield response.follow(href, callback=self.parse_article)    # follow the link and parse the article

        if response.css("a.nextpostslink::attr(href)").get():               # check if there is a next page link
            next_page = response.css("a.nextpostslink::attr(href)").get()   # get the next page link
            yield response.follow(next_page, callback=self.crawl_articles)  # follow the next page link and crawl articles

    def parse_article(self, article): # response = article element
        # this is called by crawl_articles when an article link is found, the following is yielded from each article:

        # yield the elements from the article page, which can be stored as a file later: (stored as a dict by default)
        yield{
            "title": article.css("h1.entry-title::text").get(),
            "date": article.css("p.post-meta span.published::text").get(),
            "author": article.css("a.vcard.author span.fn::text").get(),
            "categories": ", ".join(article.css("div.et_post_meta_wrapper p.post-meta a[rel='category tag']::text").getall()), 
            # these can later be accessed via the links https://notesfrompoland.com/category/{category}/

            # using xpath here to get all the nested element text: response.css doesn't get the nested elements :(
            "content": "\n\n".join(text.strip()
                                    for text in article.xpath("//div[contains(@class, 'entry-content')]//p[not(ancestor::blockquote)]//text()") # disregard blockquotes --> seperate thing for that
                                    .getall()), # ensure no random empty text
                                    # "div.entry-content p::text"
                                    # by paragraph, by <p> element, otherwise text is seperated by \n too often :)

            "quotes": "\n\n".join(text.strip()
                                    for text in article.xpath("//div[contains(@class, 'entry-content')]//blockquote//p//text()")
                                    .getall())
                                    # "div.entry-content blockquote p::text"
        }
