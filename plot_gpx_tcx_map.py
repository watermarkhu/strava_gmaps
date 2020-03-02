import ggps
import os
import time
from xml.sax._exceptions import SAXParseException
from progiter import ProgIter as prog
import pandas as pd
import plotly.express as px
import plotly
from geopy.geocoders import Nominatim as nom
import numpy as np
import scipy.cluster.hierarchy as hcluster
from collections import defaultdict

onlyfiles = [f for f in os.listdir("./") if os.path.isfile(os.path.join("./", f))]

points = ["latitudedegrees", "longitudedegrees"]

data = dict()
errors = 0
for filename in prog(onlyfiles[:]):

    if filename[-3:] == "gpx":
        handler = ggps.GpxHandler()
    elif filename[-3:] == "tcx":
        handler = ggps.TcxHandler()
        with open(filename, "r+") as reader:
            old = reader.read()
            start = old.find("<")
            if start != 0:
                new = old[start:]
                reader.seek(0)
                reader.write(new)
    else:
        continue

    try:
        handler.parse(filename)
        if len(handler.trackpoints) > 100:
            exersize = []
            for i in range(1, len(handler.trackpoints)):
                trackpoint = handler.trackpoints[i].values
                exersize.append({key: float(trackpoint[key]) for key in points})
            data[handler.first_time] = exersize
    except ValueError:
        errors += 1
    except KeyError:
        errors += 1
    except SAXParseException:
        errors += 1

print(f"processed {len(data)} with {errors} errors")


class loca(object):
    def __init__(self, name):
        self.keys = ["city", "town", "village", "city_district", "county", "nature_reserve"]
        self.locator = nom(user_agent=name)

    def get(self, lat, lon):
        location = self.locator.reverse("{}, {}".format(lat, lon)).raw['address']
        time.sleep(1)
        for key in self.keys:
            if key in location:
                print(f"got loc: {location[key]}")
                return location[key]
        else:
            return None

locator = loca("strava_output_mapper3")

locs = []
for i, (key, value) in enumerate(data.items()):
    try:
        lat, lon = float(value[0]['latitudedegrees']), float(value[0]['longitudedegrees'])
        locs.append([lat, lon])
    except IndexError:
        print(i, key, value)



ids = hcluster.fclusterdata(np.array(locs), 0.3, criterion="distance")
id_locs = defaultdict(list)
print(f"got {len(set(ids))} clusters")

for loc, id in zip(locs, ids):
    id_locs[id].append(loc)

id_cluster, cluster_locs = dict(), dict()
for id, id_loc in id_locs.items():
    num = len(id_loc)
    lats, lons = list(map(list, zip(*id_loc)))
    lat, lon = sum(lats)/num, sum(lons)/num
    cluster = locator.get(lat, lon)
    id_cluster[id] = cluster
    cluster_locs[cluster] = dict(lat=lat, lon=lon)


print("saving database")
df = pd.DataFrame(columns=points)
for value, id in zip(data.values(), ids):
    ex = pd.DataFrame(value, columns=points)
    ex["location"] = id_cluster[id]
    ex["z"] = 1
    df = df.append(ex, ignore_index=True)


points = 100000
for cluster in id_cluster.values():
    subdf = df[df['location'] == cluster]
    slice = int(-((-len(subdf)/points)//1))

    fig = px.density_mapbox(subdf.iloc[::slice], lat='latitudedegrees', lon='longitudedegrees', z = "z", radius=1,
                            center=cluster_locs[cluster], zoom=10,
                            mapbox_style="carto-darkmatter", color_continuous_scale=px.colors.sequential.Viridis)

    print(f"saving {cluster}")

    if not os.path.exists("html"):
        os.mkdir("html")
    plotly.offline.plot(fig, filename=f'html/{cluster}.html', auto_open=False)

    time.sleep(1)
#
# subdf = df[df['location'] == "Eindhoven"]
# fig = px.density_mapbox(subdf[::2], lat='latitudedegrees', lon='longitudedegrees', z = "z", radius=1,
#                         center=cluster_locs["Eindhoven"], zoom=12,
#                         mapbox_style="carto-darkmatter", color_continuous_scale=px.colors.sequential.Viridis)
#
# if not os.path.exists("html"):
#     os.mkdir("html")
# plotly.offline.plot(fig, filename='Eindhoven2.html', auto_open=False)
