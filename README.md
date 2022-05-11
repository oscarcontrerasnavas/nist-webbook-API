# Nist Webbook spider and API with scrapyrt

This project allows users to request data from the [webbook.nist.gov](https:://webbook.nist.gov) website managed by the National Institute of Standards and Technology.

The webbook is a compilation of chemical substances and properties available to the general public, although there is no interface for easy programmatic access.

This small repository provides one spider to scrap some of the tabulated data receiving two strings as arguments as follow.

```
scrapy crawl webbok_nist -a search_by=name -a name=water
```

or

```
scrapy crawl webbok_nist -a search_by=cas -a cas=7732185
```

## Storing scraped items

If you are familiar with Scrapy, you know we can store the scraped item using a pipeline. In this case, the MongoPipeline class starts a PyMongo connection by looking for two environment variables.

```
MONGO_URI = <URI>
MONGO_DB = <DATABASE>
```

## API deployed on Heroku

Thanks to [ScrapyRT](https://github.com/scrapinghub/scrapyrt), this spider also has a simple read-only API that the user can use to return a JSON file with the scraped item.

For more information, you can visit the ScrapyRT [documentation](https://scrapyrt.readthedocs.io/en/latest/index.html).

### Endpoint and example

```
https://nist-scrapyrt.herokuapp.com/crawl.json?spider_name=webbook_nist&start_requests=true&crawl_args={"search_by":"name","name":"water"}
```

## Properties returned

The list represents the properties returned once you run the spider. Please noticed that not all the properties were extracted, and not all the substances had them. It is up to the final user to check if the value they are looking for exists.

- name
- cas
- formula
- molecular_weight
- iupac_std_inchi
- iupac_std_inchikey
- image
- enthalpy_formation_gas
- enthalpy_combustion_gas
- entropy_gas
- constant_pressure_heat_capacity_values_gas
- constant_pressure_heat_capacity_units_gas
- heat_capacity_shomate_equation_gas
- enthalpy_formation_liquid
- enthalpy_combustion_liquid
- entropy_liquid
- constant_pressure_heat_capacity_values_liquid
- constant_pressure_heat_capacity_units_liquid
- heat_capacity_shomate_equation_liquid
- temperature_boil
- temperature_fusion
- temperature_triple
- pressure_triple
- temperature_critical
- pressure_critical
- volume_critical
- density_critical
- enthalpy_vaporization_average
- enthalpy_vaporization_values
- enthalpy_vaporization_units
- enthalpy_vaporization_equation
- entropy_vaporization_values
- entropy_vaporization_units
- antoine_equation

## Example of data returned

```json
[
  {
    "name": "Water",
    "cas": "7732185",
    "formula": "H2O",
    "molecular_weight": 18.0153,
    "iupac_std_inchi": "InChI=1S/H2O/h1H2",
    "iupac_std_inchikey": "XLYOFNOQVPJJNP-UHFFFAOYSA-N",
    "image": "https://webbook.nist.gov/cgi/cbook.cgi?Struct=C7732185&Type=Color",
    "enthalpy_formation_gas": { "value": -241.826, "units": "kJ/mol" },
    "heat_capacity_shomate_equation_gas": [
      {
        "temperatures": [500.0, 1700.0],
        "A": 30.092,
        "B": 6.832514,
        "C": 6.793435,
        "D": -2.53448,
        "E": 0.082139,
        "F": -250.881,
        "G": 223.3967,
        "H": -241.8264
      },
      {
        "temperatures": [1700.0, 6000.0],
        "A": 41.96426,
        "B": 8.622053,
        "C": -1.49978,
        "D": 0.098119,
        "E": -11.15764,
        "F": -272.1797,
        "G": 219.7809,
        "H": -241.8264
      }
    ],
    "enthalpy_formation_liquid": { "value": -285.83, "units": "kJ/mol" },
    "entropy_liquid": { "value": 69.95, "units": "J/mol*K" },
    "heat_capacity_shomate_equation_liquid": [
      {
        "temperatures": [298.0, 500.0],
        "A": -203.606,
        "B": 1523.29,
        "C": -3196.413,
        "D": 2474.455,
        "E": 3.855326,
        "F": -256.5478,
        "G": -488.7163,
        "H": -285.8304
      }
    ],
    "temperature_boil": { "value": 373.17, "units": "K" },
    "pressure_triple": { "value": 0.0061, "units": "bar" },
    "temperature_critical": { "value": 647.0, "units": "K" },
    "pressure_critical": { "value": 220.64, "units": "bar" },
    "density_critical": { "value": 17.9, "units": "mol/l" },
    "antoine_equation": [
      {
        "temperatures": [379.0, 573.0],
        "A": 3.55959,
        "B": 643.748,
        "C": -198.043
      },
      {
        "temperatures": [273.0, 303.0],
        "A": 5.40221,
        "B": 1838.675,
        "C": -31.737
      },
      {
        "temperatures": [304.0, 333.0],
        "A": 5.20389,
        "B": 1733.926,
        "C": -39.485
      },
      {
        "temperatures": [334.0, 363.0],
        "A": 5.0768,
        "B": 1659.793,
        "C": -45.854
      },
      {
        "temperatures": [344.0, 373.0],
        "A": 5.08354,
        "B": 1663.125,
        "C": -45.622
      },
      {
        "temperatures": [293.0, 343.0],
        "A": 6.20963,
        "B": 2354.731,
        "C": 7.559
      },
      {
        "temperatures": [255.9, 373.0],
        "A": 4.6543,
        "B": 1435.264,
        "C": -64.848
      }
    ]
  }
]
```
