import pandas as pd
import polars as pl
import h3

#----------------------------------
# Import Cleaned Data
#----------------------------------

station_cells = pd.read_csv('../Intermediate/01_citibike_rides.csv').rename(
    columns = {'start_cell':'cell_start', 'end_cell':'cell_end'})
emp = pd.read_csv('../Intermediate/03_employment_data.csv').rename(columns = {'h3_index':'cell'})
census = pd.read_csv('../Intermediate/04_census_block_data.csv').rename(columns = {'h3_index':'cell'})
schools = pd.read_csv('../Intermediate/05_school_data.csv').rename(columns = {'h3_cell':'cell'})
bike_lanes = pd.read_csv('../Intermediate/06_bike_lane_data.csv').rename(columns = {'h3_cell':'cell'})
parks = pd.read_csv('../Intermediate/07_parks_data.csv').rename(columns = {'h3_cell':'cell'})
zoning = pd.read_csv('../Intermediate/08_zoning_data.csv').rename(columns = {'h3_cell':'cell'})

#----------------------------------
# Merge Data Together
#----------------------------------

combined = station_cells.copy()

def merge_tgt(df):
    tmp = combined.merge(df.add_suffix('_start'), how = "left", on= "cell_start")
    return tmp.merge(df.add_suffix('_end'), how = "left", on= "cell_end")

combined = merge_tgt(emp)
print("merged emp")
combined = merge_tgt(census)
print("merged census")
combined = merge_tgt(schools)
print("merged school")
combined = merge_tgt(bike_lanes)
print("merged bikes")
combined = merge_tgt(parks)
print("merged parks")
combined = merge_tgt(zoning)
print("merged zoning")

#combined["grid_distance"] = combined.apply(
#    lambda row: h3.grid_distance(row["cell_start"], row["cell_end"]),
#    axis=1,
#)
#print("added dists")

combined_pl = pl.from_pandas(combined)
combined_pl.write_csv('../Intermediate/09_combined_dataset.csv')