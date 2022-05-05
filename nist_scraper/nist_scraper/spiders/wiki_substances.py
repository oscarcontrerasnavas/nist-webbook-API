import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class WikiSubstancesSpider(CrawlSpider):
    name = "wiki_substances"
    allowed_domains = ["en.wikipedia.org"]
    start_urls = [
        "https://en.wikipedia.org/wiki/List_of_inorganic_compounds",
        "https://en.wikipedia.org/wiki/List_of_biomolecules",
    ]
    custom_settings = {"FEEDS": {"links.json": {"format": "json"}}}

    # Rules
    le_inorganic_substance = LinkExtractor(
        restrict_xpaths="//h3[not(contains(string(.), 'See also'))]/following-sibling::ul[position()=1]/li[1]/a[not(contains(@title, 'page does not exist'))]"
    )
    le_organic_substance = LinkExtractor(
        restrict_xpaths="//h2[not(contains(string(.), 'See also'))]/following-sibling::ul[position()=1]/li/a[not(contains(@title, 'page does not exist'))]"
    )

    rule_inorganic_substance = Rule(
        le_inorganic_substance, callback="parse_item", follow=False
    )
    rule_organic_substance = Rule(
        le_organic_substance, callback="parse_item", follow=False
    )

    rules = (rule_inorganic_substance, rule_organic_substance)

    def parse_item(self, response):
        base_url = "https://webbook.nist.gov/cgi/cbook.cgi?ID=C{}&Units=SI"
        cas = response.xpath("//span[@title='commonchemistry.cas.org']/a/text()").get()
        if cas:
            link = base_url.format(cas.replace("-", ""))
            yield {"link": link}
