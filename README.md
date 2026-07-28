# HYS NYC CitiBike Bike Transit Analysis

Data Sources:

-   NYC Citibike ride data from July 2025-June 2026 was downloaded at https://s3.amazonaws.com/tripdata/index.html.

-   Census employment data (ny_wac_S000_JT00_2023.csv.gz, ny_xwalk.csv.gz) was downloaded at <https://lehd.ces.census.gov/data/lodes/LODES8/ny/>.

-   Census block demographics data (nhgis0001_ds258_2020_block.csv) was downloaded from <https://data2.nhgis.org/main>.

    -   I selected the "P1. Total Population", "P12. Sex by Age for Selected Age Categories", and "H1. Housing Units" tables from the\
        2020_DHCa dataset at the block level for New York state only.

-   Census block geography files were downloaded from <https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2020&layergroup=Blocks+%282020%29>.

-   Bike Lane, Park, School, and Zoning data was downloaded from the NYC Open Data website (file names may differ slightly based on download date).
    -   New_York_City_Bike_Routes_20260727.csv was downloaded at https://data.cityofnewyork.us/dataset/New-York-City-Bike-Routes-Map-/9e2b-mctv.
    -   Parks_Zones_20260727.csv was downloaded at https://data.cityofnewyork.us/City-Government/Parks-Zones/4j29-i5ry/about_data.
    -   2019_-_2020_School_Locations_20260727.csv was downloaded at https://data.cityofnewyork.us/Education/2019-2020-School-Locations/wg9x-4ke6/about_data.
    -   NYC_Zoning_Tax_Lot_Database_20260727.csv was downloaded at https://data.cityofnewyork.us/City-Government/NYC-Zoning-Tax-Lot-Database/fdkv-4t4z/about_data.
        - Borough Block Lot geographic data was downloaded at https://www.nyc.gov/content/planning/pages/resources/datasets/mappluto-pluto-change, selecting "MapPLUTO - Shoreline Clipped (shp)".
