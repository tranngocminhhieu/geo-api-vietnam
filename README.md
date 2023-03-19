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
- Use APIs from GeoPy and Google Maps to search for locations online.
- Use Excel and SQLite to save data locally.

## How to install
Run this command in Terminal (CMD).
```
pip install git+https://github.com/tranngocminhhieu/geo-api-vietnam.git
```

Use this command to update geoapivietnam.

```
pip install git+https://github.com/tranngocminhhieu/geo-api-vietnam.git --upgrade
```

## How to use
Import module and read [Sample usage notebook](https://github.com/tranngocminhhieu/geo-api-vietnam/blob/main/notebook/sample-usage.ipynb) to explore this module.

```
from geoapivietnam import Correct, GetLocation
```