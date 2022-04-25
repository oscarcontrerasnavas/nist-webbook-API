import scrapy
import re
from nist_scraper.items import SubstanceItem


class WebbookNistGovSpider(scrapy.Spider):
    name = "webbook.nist.gov"
    allowed_domains = ["webbook.nist.gov"]
    start_urls = ["https://webbook.nist.gov/cgi/cbook.cgi?Name=methane&Units=SI"]
    substance = SubstanceItem()
    custom_settings = {"FEEDS": {"items.json": {"format": "json"}}}

    def parse(self, response):
        name = response.xpath("//h1[@id='Top']/text()").get()
        cas = int(
            response.xpath("//main/ul/li[strong[contains(string(.), 'CAS')]]/text()")
            .get()
            .strip()
            .replace("-", "")
        )
        formula = (
            response.xpath(
                "string(//main/ul/li[strong[contains(string(.), 'Formula')]])"
            )
            .get()
            .replace("Formula: ", "")
        )
        molecular_weight = float(
            response.xpath(
                "string(//main/ul/li[strong[contains(string(.), 'Molecular')]])"
            )
            .get()
            .replace("Molecular weight: ", "")
        )
        iupac_std_inchi = response.xpath(
            "//main//span[@clss='inchi-text']/text()"
        ).get()
        iupac_std_inchikey = response.xpath(
            "//main//span[@class='inchi-text']/text()"
        ).get()
        image = "https://webbook.nist.gov{}".format(
            response.xpath(
                "//main//li[strong[contains(text(), 'Chemical structure')]]/img/@src"
            ).get()
        )
        gas_phase_thermo = "https://webbook.nist.gov{}".format(
            response.xpath(
                "//main//li[a[contains(string(.), 'Gas phase thermo')]]/a/@href"
            ).get()
        )

        self.substance["name"] = name
        self.substance["cas"] = cas
        self.substance["formula"] = formula
        self.substance["molecular_weight"] = molecular_weight
        self.substance["iupac_std_inchi"] = iupac_std_inchi
        self.substance["iupac_std_inchikey"] = iupac_std_inchikey
        self.substance["image"] = image

        yield scrapy.Request(gas_phase_thermo, self.parse_gas_phase_thermo)

    def parse_gas_phase_thermo(self, response):
        rows = response.xpath(
            "//main/table[@aria-label='One dimensional data']//tr[th]/following-sibling::tr[position()=1]"
        )
        for row in rows:
            property = row.xpath("string(td[position()=1])").get()
            value = {
                "value": float(
                    re.sub("\s.*", "", row.xpath("string(td[position()=2])").get())
                ),
                "units": row.xpath("td[position()=3]/text()").get(),
            }

            if property == "fH°gas":
                self.substance["enthalpy_formation_gas"] = value
            if property == "cH°gas":
                self.substance["enthalpy_combustion_gas"] = value
            if property == "S°gas":
                self.substance["entropy_gas"] = value

        yield self.substance
