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
    constant_pressure_heat_capacity_values_gas = scrapy.Field()
    constant_pressure_heat_capacity_units_gas = scrapy.Field()
    heat_capacity_shomate_equation_gas = scrapy.Field()
    enthalpy_formation_liquid = scrapy.Field()
    enthalpy_combustion_liquid = scrapy.Field()
    entropy_liquid = scrapy.Field()
    constant_pressure_heat_capacity_values_liquid = scrapy.Field()
    constant_pressure_heat_capacity_units_liquid = scrapy.Field()
    heat_capacity_shomate_equation_liquid = scrapy.Field()
    temperature_boil = scrapy.Field()
    temperature_fusion = scrapy.Field()
    temperature_triple = scrapy.Field()
    pressure_triple = scrapy.Field()
    temperature_critical = scrapy.Field()
    pressure_critical = scrapy.Field()
    volume_critical = scrapy.Field()
    density_critical = scrapy.Field()
    enthalpy_vaporization_average = scrapy.Field()
    enthalpy_vaporization_values = scrapy.Field()
    enthalpy_vaporization_units = scrapy.Field()
    enthalpy_vaporization_equation = scrapy.Field()
