import scrapy
import re
from nist_scraper.items import SubstanceItem


class WebbookNistGovSpider(scrapy.Spider):
    name = "webbook_nist"
    allowed_domains = ["webbook.nist.gov"]
    start_urls = [
        "https://webbook.nist.gov/cgi/cbook.cgi?Name=methane&Units=SI",
        "https://webbook.nist.gov/cgi/cbook.cgi?Name=water&Units=SI",
    ]
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

        yield response.follow(
            url=gas_phase_thermo,
            callback=self.parse_gas_phase_thermo,
            meta={
                "name": name,
                "cas": cas,
                "formula": formula,
                "molecular_weight": molecular_weight,
                "iupac_std_inchi": iupac_std_inchi,
                "iupac_std_inchikey": iupac_std_inchikey,
                "image": image,
            },
        )

    def parse_gas_phase_thermo(self, response):
        substance = SubstanceItem()
        substance["name"] = response.request.meta["name"]
        substance["cas"] = response.request.meta["cas"]
        substance["formula"] = response.request.meta["formula"]
        substance["molecular_weight"] = response.request.meta["molecular_weight"]
        substance["iupac_std_inchi"] = response.request.meta["iupac_std_inchi"]
        substance["iupac_std_inchikey"] = response.request.meta["iupac_std_inchikey"]
        substance["image"] = response.request.meta["image"]
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
                substance["enthalpy_formation_gas"] = value
            if property == "cH°gas":
                substance["enthalpy_combustion_gas"] = value
            if property == "S°gas":
                substance["entropy_gas"] = value

        heat_capacity_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Constant pressure heat capacity')]//tr[position()>1]"
        )
        if heat_capacity_rows:
            values = []
            for row in heat_capacity_rows:
                value = float(
                    re.sub("\s.*", "", row.xpath("td[position()=1]/text()").get())
                )
                temperature = float(row.xpath("td[position()=2]/text()").get())
                values.append([value, temperature])

            values_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Constant pressure heat capacity')]//tr[position()=1]/th[position()=1])"
            )[0].get()
            temperature_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Constant pressure heat capacity')]//tr[position()=1]/th[position()=2])"
            )[0].get()
            values_units = re.search("\((.*)\)", values_units).group(1)
            temperature_units = re.search("\((.*)\)", temperature_units).group(1)
            substance["constant_pressure_heat_capacity_values"] = sorted(
                values, key=lambda value: value[1]
            )
            substance["constant_pressure_heat_capacity_units"] = [
                values_units,
                temperature_units,
            ]

        shomate_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Shomate')]//tr[position()<10]"
        )
        if shomate_rows:
            heat_capacity_shomate_equation = []
            cols = response.xpath(
                "//main/table[contains(@aria-label, 'Shomate')]//tr[position()=1]/td"
            )
            for col in range(len(cols)):
                temperatures = (
                    shomate_rows[0].xpath("td")[col].xpath("text()").get().split("-")
                )
                temperatures = [float(x) for x in temperatures]
                a = float(shomate_rows[1].xpath("td")[col].xpath("text()").get())
                b = float(shomate_rows[2].xpath("td")[col].xpath("text()").get())
                c = float(shomate_rows[3].xpath("td")[col].xpath("text()").get())
                d = float(shomate_rows[4].xpath("td")[col].xpath("text()").get())
                e = float(shomate_rows[5].xpath("td")[col].xpath("text()").get())
                f = float(shomate_rows[6].xpath("td")[col].xpath("text()").get())
                g = float(shomate_rows[7].xpath("td")[col].xpath("text()").get())
                h = float(shomate_rows[8].xpath("td")[col].xpath("text()").get())

                heat_capacity_shomate_equation.append(
                    {
                        "temperatures": temperatures,
                        "A": a,
                        "B": b,
                        "C": c,
                        "D": d,
                        "E": e,
                        "F": f,
                        "G": g,
                    }
                )

            substance["heat_capacity_shomate_equation"] = heat_capacity_shomate_equation

        yield substance
