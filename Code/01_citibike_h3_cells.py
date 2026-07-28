from pathlib import Path
import pandas as pd
import h3
import json

#----------------------------------
# Clean Data and Get Ride Counts
#----------------------------------

def clean_rides(rides, df):
    df['started_at'] = pd.to_datetime(df['started_at'])
    df['ended_at'] = pd.to_datetime(df['ended_at'])
    df = df.dropna(subset=['start_lat', 'start_lng', 'end_lat', 'end_lng'])
    df = df[df['ended_at'] > df['started_at']]
    duration = (df['ended_at'] - df['started_at']).dt.total_seconds()
    df = df[(duration >= 60) & (duration <= 60*120)]

    df['minutes'] = df['started_at'].dt.hour * 60 + df['started_at'].dt.minute
    breaks = [-1, 360, 600, 960, 1200, 1439]
    labels = ['early_morning', 'morning', 'midday', 'evening', 'night']
    df['time'] = pd.cut(df['minutes'], bins=breaks, labels=labels, right=False)
    df['month'] = df['started_at'].dt.month
    df['weekend'] = df['started_at'].dt.dayofweek >= 5

    df['start_cell'] = [h3.latlng_to_cell(lat, lng, 9) for lat, lng in zip(df['start_lat'], df['start_lng'])]
    df['end_cell'] = [h3.latlng_to_cell(lat, lng, 9) for lat, lng in zip(df['end_lat'], df['end_lng'])]

    new_rides = df.groupby(['time', 'month', 'weekend', 'start_cell', 'end_cell']).size().reset_index(name='ride_count')
    
    return pd.concat([rides, new_rides], ignore_index=True)

citibike_data = Path("../Data/citibike")

rides = pd.DataFrame()

for file in citibike_data.rglob('*.csv'):
    df = pd.read_csv(file)
    rides = clean_rides(rides, df)

#----------------------------------
# Map Stations to H3 Cells
#----------------------------------

cells = pd.DataFrame(pd.concat([rides['start_cell'], rides['end_cell']]).drop_duplicates(), columns = ["station_cells"])
cells = cells['station_cells']

features = []
for hex in cells:
    vertices = h3.cell_to_boundary(hex)
    border = [[lng, lat] for lat, lng in vertices]
    border.append(border[0])
    lat, lng = h3.cell_to_latlng(hex)

    features.append({
        "type": "Feature",
        "properties": {
            "h3_index": hex,
            "center_lat": lat,
            "center_lng": lng,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [border],
        },
    })

cells = {
    "type": "FeatureCollection",
    "features": features,
}

#----------------------------------
# Save Output
#----------------------------------

rides.to_csv('../Intermediate/01_citibike_rides.csv', index=False)
with open("../Intermediate/02_citibike_cells.geojson", "w") as f:
    json.dump(cells, f)