import scrapy
import re
from nist_scraper.items import SubstanceItem

# from os import path
# import json


class WebbookNistSpider(scrapy.Spider):
    name = "webbook_nist"
    allowed_domains = ["webbook.nist.gov"]
    start_urls = ["https://webbook.nist.gov/cgi/cbook.cgi?Name=methane&Units=SI"]
    # custom_settings = {"FEEDS": {"items.json": {"format": "json"}}}

    custom_settings = {
        "ITEM_PIPELINES": {
            "nist_scraper.pipelines.MongoPipeline": 300,
        }
    }

    # def __init__(self):
    #     basepath = path.dirname(__file__)
    #     filepath = path.abspath(path.join(basepath, "..", "..", "links.json"))

    #     with open(filepath) as data_file:
    #         self.links = json.load(data_file)

    # def start_requests(self):
    #     for item in self.links:
    #         request = scrapy.Request(item["link"], callback=self.parse)
    #         yield request

    def parse(self, response):
        name = response.xpath("//h1[@id='Top']/text()").get()

        # If name does not exist then there is no additional info from this substance
        if name:
            properties = {}
            properties["name"] = name

            cas = response.xpath(
                "//main/ul/li[strong[contains(string(.), 'CAS')]]/text()"
            ).get()
            if cas:
                properties["cas"] = cas.strip().replace("-", "")

            formula = response.xpath(
                "string(//main/ul/li[strong[contains(string(.), 'Formula')]])"
            ).get()
            if formula:
                properties["formula"] = formula.replace("Formula: ", "")

            molecular_weight = response.xpath(
                "string(//main/ul/li[strong[contains(string(.), 'Molecular')]])"
            ).get()
            if molecular_weight:
                properties["molecular_weight"] = float(
                    molecular_weight.replace("Molecular weight: ", "")
                )

            iupac_std_inchi = response.xpath(
                "//main//span[@clss='inchi-text']/text()"
            ).get()
            if iupac_std_inchi:
                properties["iupac_std_inchi"] = iupac_std_inchi

            iupac_std_inchikey = response.xpath(
                "//main//span[@class='inchi-text']/text()"
            ).get()
            if iupac_std_inchikey:
                properties["iupac_std_inchikey"] = iupac_std_inchikey

            image = response.xpath(
                "//main//li[strong[contains(text(), 'Chemical structure')]]/img/@src"
            ).get()
            if image:
                properties["image"] = "https://webbook.nist.gov{}".format(image)

            # Look for link to pass as url for next response
            gas_phase_thermo = response.xpath(
                "//main//li[a[contains(string(.), 'Gas phase thermo')]]/a/@href"
            ).get()
            condensed_phase_thermo = response.xpath(
                "//main//li[a[contains(string(.), 'Condensed phase thermo')]]/a/@href"
            ).get()
            phase_change_data = response.xpath(
                "//main//li[a[contains(string(.), 'Phase change data')]]/a/@href"
            ).get()

            if gas_phase_thermo:
                gas_phase_thermo = "https://webbook.nist.gov{}".format(gas_phase_thermo)
                yield response.follow(
                    url=gas_phase_thermo,
                    callback=self.parse_gas_phase_thermo,
                    meta={**properties},
                )
            elif condensed_phase_thermo:
                condensed_phase_thermo = "https://webbook.nist.gov{}".format(
                    condensed_phase_thermo
                )
                yield response.follow(
                    url=condensed_phase_thermo,
                    callback=self.parse_condensed_phase_thermo,
                    meta={**properties},
                )
            elif phase_change_data:
                phase_change_data = "https://webbook.nist.gov{}".format(
                    phase_change_data
                )
                yield response.follow(
                    url=phase_change_data,
                    callback=self.parse_phase_change_data,
                    meta={**properties},
                )
            else:
                substance = SubstanceItem()
                for key, value in properties.items():
                    substance[key] = value

                yield substance

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

    def to_float(self, text: str) -> float:
        if "×10" in text:
            value = float(text.split("×")[0])
            power = text.split("×")[1]
            power = float(re.search("10(.*)", power).group(1))
            return value * 1 * 10 ** (power)
        return float(text)

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
        if one_dimentional_data:
            for row in one_dimentional_data:
                property = row.xpath("string(td[position()=1])").get()
                value_str = re.sub(
                    "\s.*", "", row.xpath("string(td[position()=2])").get()
                )
                if value_str:
                    value = {
                        "value": self.to_float(value_str),
                        "units": row.xpath("td[position()=3]/text()").get(),
                    }

                    # Gas or liquid
                    if property == "fH°{}".format(phase):
                        properties["enthalpy_formation_{}".format(phase)] = value
                    if property == "cH°{}".format(phase):
                        properties["enthalpy_combustion_{}".format(phase)] = value
                    if property == "S°{}".format(phase):
                        properties["entropy_{}".format(phase)] = value

                    # Phase change
                    if property == "Tboil":
                        properties["temperature_boil"] = value
                    if property == "Tfus":
                        properties["temperature_fusion"] = value
                    if property == "Ttriple":
                        properties["temperature_triple"] = value
                    if property == "Ptriple":
                        properties["pressure_triple"] = value
                    if property == "Tc":
                        properties["temperature_critical"] = value
                    if property == "Pc":
                        properties["pressure_critical"] = value
                    if property == "Vc":
                        properties["volume_critical"] = value
                    if property == "c":
                        properties["density_critical"] = value
                    if property == "vapH°":
                        properties["enthalpy_vaporization_average"] = value

        # Some substances have one or more tables with pair or values for Cp(T)
        heat_capacity_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Constant pressure heat capacity of {}')]//tr[position()>1]".format(
                phase
            )
        )
        if heat_capacity_rows:  # Checking if these tables exist
            values = []
            for row in heat_capacity_rows:
                temperature = row.xpath("td[position()=2]/text()").get()
                if temperature:
                    if "-" not in temperature:
                        temperature = float(temperature)
                        value = float(
                            re.sub(
                                "\s.*", "", row.xpath("td[position()=1]/text()").get()
                            )
                        )
                        values.append([value, temperature])

            values_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Constant pressure heat capacity of {}')]//tr[position()=1]/th[position()=1])".format(
                    phase
                )
            )[0].get()
            temperature_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Constant pressure heat capacity of {}')]//tr[position()=1]/th[position()=2])".format(
                    phase
                )
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
            "//main/table[contains(@aria-label, '{} Phase Heat Capacity (Shomate Equation)')]//tr[position()<10]".format(
                phase.capitalize()
            )
        )
        if shomate_rows:
            heat_capacity_shomate_equation = []
            cols = response.xpath(
                "//main/table[contains(@aria-label, '{} Phase Heat Capacity (Shomate Equation)')]//tr[position()=1]/td".format(
                    phase.capitalize()
                )
            )
            for col in range(1, len(cols) + 1):
                temperatures = (
                    shomate_rows[0].xpath("string(td[{}])".format(col)).get().split("-")
                )
                temperatures = [float(x) for x in temperatures]
                a = self.to_float(
                    shomate_rows[1].xpath("string(td[{}])".format(col)).get()
                )
                b = self.to_float(
                    shomate_rows[2].xpath("string(td[{}])".format(col)).get()
                )
                c = self.to_float(
                    shomate_rows[3].xpath("string(td[{}])".format(col)).get()
                )
                d = self.to_float(
                    shomate_rows[4].xpath("string(td[{}])".format(col)).get()
                )
                e = self.to_float(
                    shomate_rows[5].xpath("string(td[{}])".format(col)).get()
                )
                f = self.to_float(
                    shomate_rows[6].xpath("string(td[{}])".format(col)).get()
                )
                g = self.to_float(
                    shomate_rows[7].xpath("string(td[{}])".format(col)).get()
                )
                h = self.to_float(
                    shomate_rows[8].xpath("string(td[{}])".format(col)).get()
                )

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

        # Change phase data enthalpy_vaporization
        enthalpy_vaporization_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Enthalpy of vaporization')][1]//tr[position()>1]"
        )

        if enthalpy_vaporization_rows:
            values = []
            for row in enthalpy_vaporization_rows:
                temperature = row.xpath("td[position()=2]/text()").get()
                if temperature and "-" not in temperature:
                    temperature = float(temperature)
                    value = float(
                        re.sub("\s.*", "", row.xpath("td[position()=1]/text()").get())
                    )
                    values.append([value, temperature])

            values_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Enthalpy of vaporization')]//tr[position()=1]/th[position()=1])"
            )[0].get()
            temperature_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Enthalpy of vaporization')]//tr[position()=1]/th[position()=2])"
            )[0].get()
            values_units = re.search("\((.*)\)", values_units).group(1)
            temperature_units = re.search("\((.*)\)", temperature_units).group(1)
            properties["enthalpy_vaporization_values"] = sorted(
                values, key=lambda value: value[1]
            )
            properties["enthalpy_vaporization_units"] = [
                values_units,
                temperature_units,
            ]

        enthalpy_vaporization_equation_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Enthalpy of vaporization')][2]//tr[position()<6]"
        )
        if enthalpy_vaporization_equation_rows:
            enthalpy_vaporization_equation = []
            cols = response.xpath(
                "//main/table[contains(@aria-label, 'Enthalpy of vaporization')][2]//tr[position()=1]/td"
            )
            for col in range(len(cols)):
                temperatures = (
                    enthalpy_vaporization_equation_rows[0]
                    .xpath("td")[col]
                    .xpath("text()")
                    .get()
                    .split("-")
                )
                temperatures = [float(x) for x in temperatures]
                a = float(
                    enthalpy_vaporization_equation_rows[1]
                    .xpath("td")[col]
                    .xpath("text()")
                    .get()
                )
                alpha = float(
                    enthalpy_vaporization_equation_rows[2]
                    .xpath("td")[col]
                    .xpath("text()")
                    .get()
                )
                beta = float(
                    enthalpy_vaporization_equation_rows[3]
                    .xpath("td")[col]
                    .xpath("text()")
                    .get()
                )
                temperature_critical = float(
                    enthalpy_vaporization_equation_rows[4]
                    .xpath("td")[col]
                    .xpath("text()")
                    .get()
                )

                enthalpy_vaporization_equation.append(
                    {
                        "temperatures": temperatures,
                        "A": a,
                        "alpha": alpha,
                        "beta": beta,
                        "Tc": temperature_critical,
                    }
                )
            properties[
                "enthalpy_vaporization_equation"
            ] = enthalpy_vaporization_equation

        # Change phase data entropy_vaporization
        entropy_vaporization_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Entropy of vaporization')][1]//tr[position()>1]"
        )

        if entropy_vaporization_rows:
            values = []
            for row in entropy_vaporization_rows:
                temperature = row.xpath("td[position()=2]/text()").get()
                if temperature:
                    temperature = float(temperature)
                    value = float(
                        re.sub("\s.*", "", row.xpath("td[position()=1]/text()").get())
                    )
                    values.append([value, temperature])

            values_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Entropy of vaporization')]//tr[position()=1]/th[position()=1])"
            )[0].get()
            temperature_units = response.xpath(
                "string(//main/table[contains(@aria-label, 'Entropy of vaporization')]//tr[position()=1]/th[position()=2])"
            )[0].get()
            values_units = re.search("\((.*)\)", values_units).group(1)
            temperature_units = re.search("\((.*)\)", temperature_units).group(1)
            properties["entropy_vaporization_values"] = sorted(
                values, key=lambda value: value[1]
            )
            properties["entropy_vaporization_units"] = [
                values_units,
                temperature_units,
            ]

        # Antoine equation
        antoine_rows = response.xpath(
            "//main/table[contains(@aria-label, 'Antoine')]//tr[position()>1]"
        )
        if antoine_rows:
            values = []
            for row in antoine_rows:
                temperature = row.xpath("td[position()=1]/text()").get().split("-")
                tmin = float(temperature[0])
                tmax = float(temperature[1])
                a = float(row.xpath("td[position()=2]/text()").get())
                b = float(row.xpath("td[position()=3]/text()").get())
                c = float(row.xpath("td[position()=4]/text()").get())
                values.append(
                    {
                        "temperatures": [tmin, tmax],
                        "A": a,
                        "B": b,
                        "C": c,
                    }
                )
            properties["antoine_equation"] = values

        return properties

    def parse_gas_phase_thermo(self, response):
        properties = self.extract_data_tables(response, "gas")

        # Look for link to pass as url for next response
        condensed_phase_thermo = response.xpath(
            "//main//li[a[contains(string(.), 'Condensed phase thermo')]]/a/@href"
        ).get()
        phase_change_data = response.xpath(
            "//main//li[a[contains(string(.), 'Phase change data')]]/a/@href"
        ).get()

        if condensed_phase_thermo:
            condensed_phase_thermo = "https://webbook.nist.gov{}".format(
                condensed_phase_thermo
            )
            yield response.follow(
                url=condensed_phase_thermo,
                callback=self.parse_condensed_phase_thermo,
                meta={**properties},
            )
        elif phase_change_data:
            phase_change_data = "https://webbook.nist.gov{}".format(phase_change_data)
            yield response.follow(
                url=phase_change_data,
                callback=self.parse_phase_change_data,
                meta={**properties},
            )
        else:
            substance = SubstanceItem()
            for key, value in properties.items():
                substance[key] = value

            yield substance

    def parse_condensed_phase_thermo(self, response):
        properties = self.extract_data_tables(response, "liquid")

        # Look for link to pass as url for next response
        phase_change_data = response.xpath(
            "//main//li[a[contains(string(.), 'Phase change data')]]/a/@href"
        ).get()

        if phase_change_data:
            phase_change_data = "https://webbook.nist.gov{}".format(phase_change_data)
            yield response.follow(
                url=phase_change_data,
                callback=self.parse_phase_change_data,
                meta={**properties},
            )
        else:
            substance = SubstanceItem()
            for key, value in properties.items():
                substance[key] = value

            yield substance

    def parse_phase_change_data(self, response):
        properties = self.extract_data_tables(response, "")

        substance = SubstanceItem()
        for key, value in properties.items():
            substance[key] = value

        yield substance
