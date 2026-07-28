import pandas as pd
import numpy as np
from shapely import wkt
from shapely.geometry import Polygon                                                
import geopandas as gpd   
import h3                                                                                                    

RES = 9

#------------------------------------
# Schools Data
#------------------------------------

schools = pd.read_csv("../Data/nyc_open_data/2019_-_2020_School_Locations_20260727.csv", low_memory=False)
schools = schools[schools["Status_descriptions"].str.contains("Open", case=False, na=False)]
schools_geo = schools.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
schools_geo['h3_cell'] = [
    h3.latlng_to_cell(lat, lon, RES)
    for lat, lon in zip(schools_geo['LATITUDE'], schools_geo['LONGITUDE'])
]
schools_geo = schools_geo[['Location_Category_Description', 'h3_cell']].rename(columns = {'Location_Category_Description':'school_type'})
schools_geo['has_school'] = 1

mapping = {   
    'Early Childhood': 'early_schooling',                                                                                          
    'Elementary': 'elementary_school',
    'High School': 'high_school',   
    'Junior High-Intermediate-Middle':'middle_school',                             
    'K-8': 'k_8_school',                                                                              
    'K-12 all grades': 'k_12_school',   
    'Seconary School': 'secondary_school',                                                                       
    'Ungraded': 'ungraded_school'                                                                        
}                                                                                                                                                                                                                        
schools_geo['school_type'] = schools_geo['school_type'].replace(mapping)

schools_geo = schools_geo.pivot_table(                                                                     
    index='h3_cell',                                                                                         
    columns='school_type',                                                                                   
    values='has_school',                                                                                     
    aggfunc='max',                                                
    fill_value=0                                                                                             
).reset_index()

#------------------------------------
# Bike Lane Data
#------------------------------------

bikes = pd.read_csv('../Data/nyc_open_data/New_York_City_Bike_Routes_20260727.csv', low_memory=False)
bikes = bikes[bikes["status"].str.contains("Current", case=False, na=False)]

def line_to_cells(wkt_str, res=RES):
    geom = wkt.loads(wkt_str)
    lines = geom.geoms if geom.geom_type == 'MultiLineString' else [geom]
    cells = set()
    for line in lines:
        coords = list(line.coords)  # (lon, lat)
        vertex_cells = [h3.latlng_to_cell(lat, lon, res) for lon, lat in coords]
        cells.update(vertex_cells)
        for a, b in zip(vertex_cells[:-1], vertex_cells[1:]):
            if a != b:
                cells.update(h3.grid_path_cells(a, b))
    return cells

bikes['h3_cells'] = bikes['the_geom'].apply(line_to_cells)
bikes['on_street'] = np.where(bikes['onoffst'] == "ON", 1, 0)
bikes['protected_lane'] = np.where((bikes['ft_facilit'] == "Protected") | (bikes['tf_facilit'] == "Protected"), 1, 0)
bikes = bikes[['on_street', 'protected_lane', 'h3_cells']]
bikes = (bikes.explode('h3_cells') 
         .rename(columns={'h3_cells': 'h3_cell'})  
         .drop_duplicates(subset=['h3_cell']))

#------------------------------------
# Parks Data
#------------------------------------

parks = pd.read_csv('../Data/nyc_open_data/Parks_Zones_20260727.csv', low_memory=False)
parks = parks[parks["RETIRED"] == False]

def polygon_to_cells(wkt_str, res=RES):
    if isinstance(wkt_str, str): 
        geom = wkt.loads(wkt_str)
    else:
        geom = wkt_str
    polys = geom.geoms if geom.geom_type == 'MultiPolygon' else [geom]
    cells = set()
    for poly in polys:
        outer = [(lat, lon) for lon, lat in poly.exterior.coords]
        holes = [[(lat, lon) for lon, lat in interior.coords] for interior in poly.interiors]
        cells.update(h3.h3shape_to_cells(h3.LatLngPoly(outer, *holes), res))
    if not cells:
        c = geom.centroid
        cells.add(h3.latlng_to_cell(c.y, c.x, res))
    return cells

parks['h3_cells'] = parks['multipolygon'].apply(polygon_to_cells)
parks['has_park'] = 1
parks = parks.rename(columns = {'PROPNAME':'park_name'})
parks = parks[['has_park', 'park_name', 'h3_cells']]
parks = (parks.explode('h3_cells')  
            .rename(columns={'h3_cells': 'h3_cell'})  
            .drop_duplicates(subset=['h3_cell'])[['h3_cell', 'has_park', 'park_name']])

#------------------------------------
# Zoning Data
#------------------------------------

pluto = gpd.read_file("../Data/nyc_open_data/nyc_mappluto_26v1_shp.zip")[['BBL', 'geometry']]                
pluto['BBL'] = pluto['BBL'].astype(int)                                                                                                                                                                           
pluto = pluto.to_crs(epsg=4326)                                                                              
                                                                                                                
zoning = pd.read_csv('../Data/nyc_open_data/NYC_Zoning_Tax_Lot_Database_20260727.csv', dtype=str)            
zoning['BBL'] = zoning['BBL'].astype(int)                                                                    
zoning = zoning.drop_duplicates()                                                                            
                                                                                                                
zone_cols = ['Zoning District 1', 'Zoning District 2', 'Zoning District 3', 'Zoning District 4']             
zoning['res_zoning_ct'] = 0                                                                                  
zoning['com_zoning_ct'] = 0                                                                                  
zoning['manf_zoning_ct'] = 0                                                                                 
                                                                                                                
for col in zone_cols:                                                                                        
    if col in zoning.columns:                                                                                
        first_char = zoning[col].fillna('').astype(str).str.strip().str.upper().str[0]                       
        zoning['res_zoning_ct'] += (first_char == 'R').astype(int)                                           
        zoning['com_zoning_ct'] += (first_char == 'C').astype(int)                                           
        zoning['manf_zoning_ct'] += (first_char == 'M').astype(int)                                          
                                                                                                                
zoning = zoning[['BBL', 'res_zoning_ct', 'com_zoning_ct', 'manf_zoning_ct']].drop_duplicates()                                                                                                                     
zoning_gdf = pluto.merge(zoning, on="BBL", how="inner")                                                      
                                                                                                                
xmin, ymin, xmax, ymax = zoning_gdf.total_bounds                                                             
nyc_bbox = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])                                                                                                                                           
nyc_outer = [(lat, lon) for lon, lat in nyc_bbox.exterior.coords]                                            
nyc_h3_cells = h3.h3shape_to_cells(h3.LatLngPoly(nyc_outer), RES)                                            
                                                                                                                
h3_polys = []                                                                                                
for cell in nyc_h3_cells:                                                                                    
    boundary = h3.cell_to_boundary(cell)  # [(lat, lon), ...]                                                
    poly_geom = Polygon([(lon, lat) for lat, lon in boundary])                                               
    h3_polys.append({'h3_cell': cell, 'geometry': poly_geom})                                                                                                                                                             
h3_gdf = gpd.GeoDataFrame(h3_polys, crs="EPSG:4326")                                                                                                          
joined = gpd.sjoin(zoning_gdf, h3_gdf, how="inner", predicate="intersects")                                  
                                                           
zoning_h3 = joined.groupby('h3_cell').agg(                                                           
    res_lots=('res_zoning_ct', 'sum'),                                                                       
    com_lots=('com_zoning_ct', 'sum'),                                                                       
    manf_lots=('manf_zoning_ct', 'sum')                                                                      
).reset_index()                                                                                               

#------------------------------------
# Save Cleaned Datasets
#------------------------------------

schools_geo.to_csv('../Intermediate/05_school_data.csv', index=False)
bikes.to_csv('../Intermediate/06_bike_lane_data.csv', index=False)
parks.to_csv('../Intermediate/07_parks_data.csv', index=False)
zoning_h3.to_csv('../Intermediate/08_zoning_data.csv', index=False)