import pandas as pd
import numpy as np
import json
import geopandas as gpd
import h3

#------------------------------------
# Load Data
#------------------------------------

wac = pd.read_csv("../Data/employment_data/ny_wac_S000_JT00_2023.csv.gz").rename(columns = {'w_geocode':'geocode'})
loc = pd.read_csv("../Data/employment_data/ny_xwalk.csv.gz")

census = pd.read_csv("../Data/nhgis0001_csv/nhgis0001_ds258_2020_block.csv")

with open('../Intermediate/02_citibike_cells.geojson', "r") as f:
    cells = json.load(f)
cells = gpd.GeoDataFrame.from_features(cells["features"], crs="EPSG:4326")

blocks = gpd.read_file("../Data/census_block_geography/tl_2020_36_tabblock20.shp")

#------------------------------------
# Clean and Process Census Data
#------------------------------------

loc_clean = loc[['tabblk2020','blklatdd', 'blklondd']].rename(columns = {'tabblk2020':'geocode', 'blklatdd':'latitude', 'blklondd':'longitude'})

def clean_data(df):
    white_collar_9_5 = ["CNS09", "CNS10", "CNS12", "CNS13", "CNS20"]
    shift_work_24_hrs = ["CNS03", "CNS05", "CNS08", "CNS14", "CNS16"]
    shfit_work_leisure = ["CNS07", "CNS11", "CNS17", "CNS18", "CNS19"]
    consistent_early_hrs = ["CNS15", "CNS04", "CNS06", "CNS01", "CNS02"]

    df_clean = df.copy()
    df_clean['white_collar_jobs'] = df[white_collar_9_5].sum(axis = 1)
    df_clean['all_day_jobs'] = df[shift_work_24_hrs].sum(axis = 1)
    df_clean['entertainment_jobs'] = df[shfit_work_leisure].sum(axis = 1)
    df_clean['early_start_jobs'] = df[consistent_early_hrs].sum(axis = 1)

    df_clean['age_29_or_younger'] = df_clean['CA01']
    df_clean['pay_1250_or_less'] = df_clean['CE01']
    df_clean['pay_1251_to_3333'] = df_clean['CE02']
    df_clean['pay_over_3333'] = df_clean['CE03']
    df_clean['sex_female'] = df_clean['CS02']

    df_clean.rename(columns = {'C000':'job_ct'}, inplace = True)
    df_clean = df_clean[['geocode', 'job_ct', 'white_collar_jobs','all_day_jobs',
                        'entertainment_jobs', 'early_start_jobs',
                        'age_29_or_younger', 'pay_1250_or_less',
                        'pay_1251_to_3333', 'pay_over_3333', 'sex_female']]
    df_clean = df_clean.fillna(0)

    return df_clean

work_demographics = clean_data(wac)

nyc_census = census[census['COUNTY'].isin(['New York County', 'Queens County', 'Kings County', 'Bronx County', 'Richmond County'])]
nyc_census['age_15_to_34'] = (nyc_census['U7S006'] + nyc_census['U7S007'] + nyc_census['U7S008'] +
                                nyc_census['U7S009'] + nyc_census['U7S010'] + nyc_census['U7S011'] +
                                nyc_census['U7S012'] + nyc_census['U7S030'] + nyc_census['U7S031'] +
                                nyc_census['U7S032'] + nyc_census['U7S033'] + nyc_census['U7S034'] +
                                nyc_census['U7S035'] + nyc_census['U7S036'])
nyc_census.rename(columns = {'GEOCODE':'geocode', 'U7S001':'total_pop', 'U7S026':'female_pop', 'U9V001':'housing_units'}, inplace = True)
nyc_census = nyc_census[['geocode', 'total_pop', 'female_pop', 'age_15_to_34', 'housing_units']]
nyc_census = nyc_census.fillna(0)

census_demographics = nyc_census

#------------------------------------
# Merge Census Data to H3 Locations
#------------------------------------

blocks['geocode'] = blocks['GEOID20']
blocks = blocks.to_crs(cells.crs)

block_hex_xwalk = gpd.sjoin(
    blocks[['geocode', 'geometry']],
    cells[['h3_index', 'geometry']],
    how='inner',
    predicate='intersects',
)[['geocode', 'h3_index']]
block_hex_xwalk['geocode'] = block_hex_xwalk['geocode'].astype(int)

def hex_merge(df, xwalk, hex, share_cols, denom_col, other_cols=[]):
    df_clean = df.copy()
    merged = xwalk.merge(df_clean, on='geocode', how='inner')

    all_metric_cols = list(set(share_cols + [denom_col] + other_cols))
    agg_dict = {col: 'mean' for col in all_metric_cols}
    hex_agg = merged.groupby('h3_index').agg(agg_dict).reset_index()

    for col in share_cols:
        hex_agg[col] = np.where(
            hex_agg[denom_col] == 0, 0, hex_agg[col] / hex_agg[denom_col]
        )

    res = hex[['h3_index', 'geometry']].merge(
        hex_agg, on='h3_index', how='inner'
    )
    return gpd.GeoDataFrame(res, geometry='geometry', crs=hex.crs)

wac_share_cols = [
    "white_collar_jobs",
    "all_day_jobs",
    "entertainment_jobs",
    "early_start_jobs",
    "age_29_or_younger",
    "pay_1250_or_less",
    "pay_1251_to_3333",
    "pay_over_3333",
    "sex_female",
]

hex_work = hex_merge(work_demographics, block_hex_xwalk, cells, wac_share_cols, "job_ct", [])
hex_work = hex_work.drop(['geometry'], axis = 1)

census_share_cols = [
        "female_pop",
        "age_15_to_34",]

hex_census = hex_merge(census_demographics, block_hex_xwalk, cells, census_share_cols, "total_pop", ['housing_units'])
hex_census = hex_census.drop(['geometry'], axis = 1)

hex_work.to_csv('../Intermediate/03_employment_data.csv', index=False)
hex_census.to_csv('../Intermediate/04_census_block_data.csv', index=False)