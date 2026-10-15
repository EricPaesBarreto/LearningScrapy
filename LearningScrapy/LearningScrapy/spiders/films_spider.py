import scrapy
import scrapy_selenium4
from scrapy_selenium4 import SeleniumRequest
from selenium.webdriver.common.by import By

class infscrSpider(scrapy.Spider):
    name = "films"
    allowed_domains = ["infiniteajaxscroll.com"]
    start_urls = ["https://infiniteajaxscroll.com/examples/json/"]

    # custom settings for this spider
    contentWaitTime = 3  # seconds to wait for new content to load after scrolling

    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 100, # stop the spider after scraping 100 items
        "DOWNLOAD_DELAY": 1,
        "DEPTH_PRIORITY": 1,
        "FEEDS": {
            "outputs/films.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
            }
        }
    }

    def start(self):
        for url in self.start_urls:
            yield from SeleniumRequest(url=url, callback=self.parse, wait_time=3)


    def parse(self, response):
        # callback from start()
        yield from self.crawl_films(response)


    def crawl_films(self, response):
        # called by parse() - crawls films and yields results

        prior_element_count = 0 # xpath indexing starts from 1

        while True:        
            current_element_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div.container div.item")) # count of all loaded items, becomes our upper bound

            for film in response.xpath("//div[contains(@class='container')]//div[contains(@class='item')]")[prior_element_count:]:
                yield from self.parse_film(film)

            response = self.scroll_and_wait(self.contentWaitTime)  # scroll down and wait for new items to load

            prior_element_count = current_element_count  # update the prior element count, becomes the lower bound for the next iteration

            if prior_element_count >= current_element_count: break # end the loop once no new items are loaded (end of infinite scroll)
        

    def parse_film(self, film):
        # called by crawl_films() - parses each film and yields results
        yield {
            "title": film.css("a.item__link h1.item__title::text").get(),
            "year": film.css("a.item__link span.item__year::text").get(),
            "rating": film.css("a.item__link span.item__rating::text").get(),
            "link": film.css("a.item__link::attr(href)").get(),
            "image_link": film.css("a.item__link div.item__img img.item__img__img::attr(src)").get()
        }
        

    def scroll_and_wait(self, timeout):
        # called by crawl_films() - scrolls down the page and waits for new items to load

        # scroll to the botto of the page

        # wait for new items to load OR until timeout is reached

        raise NotImplementedError("scroll_and_wait() is not implemented yet.")