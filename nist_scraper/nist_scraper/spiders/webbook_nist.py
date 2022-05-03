import scrapy
import re
from nist_scraper.items import SubstanceItem


class WebbookNistSpider(scrapy.Spider):
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
        gas_phase_thermo = response.xpath(
            "//main//li[a[contains(string(.), 'Gas phase thermo')]]/a/@href"
        ).get()

        gas_phase_thermo_link = "https://webbook.nist.gov{}".format(gas_phase_thermo)

        yield response.follow(
            url=gas_phase_thermo_link,
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

    def extract_properties(self, properties: dict) -> dict:
        parsed_properties = {}
        for key, value in properties.items():
            if key not in [
                "depth",
                "download_timeout",
                "download_slot",
                "download_latency",
            ]:
                parsed_properties[key] = value

        return parsed_properties

    def extract_data_tables(self, response: scrapy.Request, phase: str) -> dict:
        """_summary_

        Args:
            response (scrapy.Request): _description_
            phase (str): _description_

        Returns:
            dict: _description_
        """

        # Spreding the information alrady scraped from the previous parse
        # In order to not create a SubstanceItem() instance rigt away due to unconsistence behaviours
        # when passing more than one start_urls it was found better to pass these properties
        # as dict
        properties = self.extract_properties(response.request.meta)

        # One dimentional data is the first table for each phase (gas, condensed or change)
        # This table contains the enthalpy and entalpy for each phase.
        one_dimentional_data = response.xpath(
            "//main/table[@aria-label='One dimensional data']//tr[th]/following-sibling::tr[position()=1]"
        )
        for row in one_dimentional_data:
            property = row.xpath("string(td[position()=1])").get()
            value = {
                "value": float(
                    re.sub("\s.*", "", row.xpath("string(td[position()=2])").get())
                ),
                "units": row.xpath("td[position()=3]/text()").get(),
            }

            if property == "fH°{}".format(phase):
                properties["enthalpy_formation_{}".format(phase)] = value
            if property == "cH°{}".format(phase):
                properties["enthalpy_combustion_{}".format(phase)] = value
            if property == "S°{}".format(phase):
                properties["entropy_{}".format(phase)] = value

        # Some substances have one or more tables with pair or values for Cp(T)
        heat_capacity_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Constant pressure heat capacity')]//tr[position()>1]"
        )
        if heat_capacity_rows:  # Checking if those tables exist
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
            properties[
                "constant_pressure_heat_capacity_values_{}".format(phase)
            ] = sorted(values, key=lambda value: value[1])
            properties["constant_pressure_heat_capacity_units_{}".format(phase)] = [
                values_units,
                temperature_units,
            ]

        # Other substances instead of pair of values for Cp(T) they have shomate equation
        # The shomate equation have [a-h] constants
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
                        "H": h,
                    }
                )
            properties[
                "heat_capacity_shomate_equation_{}".format(phase)
            ] = heat_capacity_shomate_equation

        return properties

    def parse_gas_phase_thermo(self, response):
        properties = self.extract_data_tables(response, "gas")

        condensed_phase_thermo = response.xpath(
            "//main//li[a[contains(string(.), 'Condensed phase thermo')]]/a/@href"
        ).get()

        condensed_phase_thermo_link = "https://webbook.nist.gov{}".format(
            condensed_phase_thermo
        )

        if condensed_phase_thermo:
            yield response.follow(
                url=condensed_phase_thermo_link,
                callback=self.parse_condensed_phase_thermo,
                meta={**properties},
            )
        else:
            substance = SubstanceItem()
            for key, value in properties.items():
                substance[key] = value

            yield substance

    def parse_condensed_phase_thermo(self, response):
        properties = self.extract_data_tables(response, "liquid")
        substance = SubstanceItem()
        for key, value in properties.items():
            substance[key] = value

        yield substance
