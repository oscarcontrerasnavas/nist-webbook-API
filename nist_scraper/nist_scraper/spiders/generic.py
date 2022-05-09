import scrapy


class GenericSpider(scrapy.Spider):
    name = "generic_spider"
    allowed_domains = ["entri.app"]
    start_urls = [
        "https://entri.app/blog/list-of-chemical-compounds-and-their-common-names-and-formulas/",
    ]
    custom_settings = {"FEEDS": {"links.json": {"format": "json"}}}

    def parse(self, response):
        base_url = "https://webbook.nist.gov/cgi/cbook.cgi?Name={}&Units=SI"
        names = response.xpath(
            "//table/tbody/tr[position()>1]/td[position()=2]/h5/text()"
        ).getall()
        for name in names:
            link = base_url.format(name.strip().replace(" ", "+"))
            yield {"link": link}
