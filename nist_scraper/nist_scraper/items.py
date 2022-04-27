# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SubstanceItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    cas = scrapy.Field()
    formula = scrapy.Field()
    molecular_weight = scrapy.Field()
    iupac_std_inchi = scrapy.Field()
    iupac_std_inchikey = scrapy.Field()
    image = scrapy.Field()
    enthalpy_formation_gas = scrapy.Field()
    enthalpy_combustion_gas = scrapy.Field()
    entropy_gas = scrapy.Field()
    constant_pressure_heat_capacity_values = scrapy.Field()
    heat_capacity_shomate_equation = scrapy.Field()
    constant_pressure_heat_capacity_units = scrapy.Field()
