# Geo API Vietnam 🇻🇳

Geo API Vietnam is a package that helps you find locations in Vietnam with strongly cleaned data.

Main fuction:
- Clean up and correct spelling for Province and District.
- Search location by keyword or coordinates.

Location object with properties:
- `address`: The address has been formatted correctly.
- `province`: Province is spelled correctly.
- `district`: District is spelled correctly.
- `ward`: Ward is spelled correctly.
- `latitude`: Latitude of the location.
- `longitude`: Longitude of the location.
- `source`: Origin of `original_address`, including Excel, SQLite, GeoPy, and Google Maps API.
- `original_address`: Address from the above sources.
- `json_data`: The location's data is in the form of a dictionary.

## How it works

- Use Vietnam location data to clean up and correct typos.
- Use APIs from [GeoPy](https://pypi.org/project/geopy/) and Google Maps ([Google Geocoding](https://developers.google.com/maps/documentation/geocoding)) to search for locations online.
- Use Excel and SQLite to save data locally.
- Search location in smart order: Excel > SQLite > GeoPy > Google Maps.

## How to install
### Install with Pip

Install new package.

```
pip install geoapivietnam
```

Upgrade to the latest version.

```
pip install geoapivietnam --upgrade
```

### Install with GitHub

Install new package.

```
pip install git+https://github.com/tranngocminhhieu/geo-api-vietnam.git
```

Upgrade to the latest version.

```
pip install git+https://github.com/tranngocminhhieu/geo-api-vietnam.git --upgrade
```

## How to use
Import module and read [Sample usage notebook](https://github.com/tranngocminhhieu/geo-api-vietnam/blob/main/notebook/sample-usage.ipynb) to explore this module.

```
from geoapivietnam import Correct, GetLocation
```