#%%

# Get filenames
import gmaps.datasets
import gmaps
from gmaps.geotraitlets import Longitude
from progiter import ProgIter as prog
from strava_export_gpx import main
import gpxpy
import pandas as pd

#%%
folder = "/mnt/d/Users/water_000/Downloads/export_25412727/"
files = main(folder, folder + "activities", folder + "activities.csv")

#%%
data = []
for filename, activity_type in prog(files.items()):
    with open(folder + filename, "r") as file:
        gpxdata = gpxpy.parse(file)

    init_time = gpxdata.tracks[0].segments[0].points[0].time
    for track in gpxdata.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.latitude and point.longitude:
                    data.append(dict(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        time=point.time,
                        type=activity_type,
                        file=filename
                    ))

df = pd.DataFrame(data)

#%%
import gmaps

gmaps.configure(api_key='AIzaSyDhig-iOR9eEfYksDbsyrnRpHBda2z-HwA')
locations = df.loc[df["type"] == "Alpine Ski", ['latitude', 'longitude']]
fig = gmaps.figure(
    styles='''[
    {
        "featureType": "all",
        "stylers": [
        { "color": "#C0C0C0" }
        ]
    },{
        "featureType": "road.arterial",
        "elementType": "geometry",
        "stylers": [
        { "color": "#CCFFFF" }
        ]
    },{
        "featureType": "landscape",
        "elementType": "labels",
        "stylers": [
        { "visibility": "off" }
        ]
    }
]''')
fig.add_layer(gmaps.heatmap_layer(locations))
fig

# %%
