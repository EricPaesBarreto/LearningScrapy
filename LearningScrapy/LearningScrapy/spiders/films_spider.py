from urllib import response

import scrapy
import scrapy_selenium4
from scrapy_selenium4 import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

class FilmsSpider(scrapy.Spider):
    name = "films"
    allowed_domains = ["infiniteajaxscroll.com"]
    start_urls = ["https://infiniteajaxscroll.com/examples/json/"]

    # custom settings for this spider
    contentWaitTime = 5  # seconds to wait for new content to load after scrolling (timeout for webdriverwait)

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

    async def start(self):
        for url in self.start_urls:
            yield  SeleniumRequest(url=url, callback=self.parse, wait_time=3)


    def parse(self, response):
        # callback from start()
        self.driver = response.request.meta["driver"]
        yield from self.crawl_films(response)


    def crawl_films(self, response):
        # called by parse() - crawls films and yields results

        parsed_elements = 0 # xpath indexing starts from 1

        while True:
            # get the source for the current page from the driver
            selector = scrapy.Selector(text=self.driver.page_source)

            # get all the films in a list
            films = selector.css("div.container div.item")

            # parse all the films which have been loaded thus far
            for film in films[parsed_elements:]:
                yield from self.parse_film(film)


            # if no new items --> exit loop
            if parsed_elements >= len(films): break

            # scroll down and wait for new items to load
            self.scroll_and_wait() 

            # update the prior element count, becomes the lower bound for the next iteration
            parsed_elements = len(films)

            
        

    def parse_film(self, film):
        # called by crawl_films() - parses each film and yields results
        yield {
            "title": film.css("a.item__link h1.item__title::text").get(),
            "year": film.css("a.item__link div.item__year::text").get(),
            "rating": film.css("a.item__link div.item__rating::text").get(),
            "link": film.css("a.item__link::attr(href)").get(),
            "image_link": film.css("a.item__link div.item__img img.item__img__img::attr(src)").get()
        }
        

    def scroll_and_wait(self, timeout=contentWaitTime):
        # called by crawl_films() - scrolls down the page and waits for new items to load

        # get the current count of loaded items
        prior_element_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div.container div.item"))

        # scroll to the bottom of the page
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # wait for new items to load OR until timeout is reached

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "div.container div.item")) > prior_element_count
            )
        except:
            pass # no new elements (or the page just took too long to load :/ )