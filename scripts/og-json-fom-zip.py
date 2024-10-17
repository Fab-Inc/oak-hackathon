# %%
import json
import fnmatch
from zipfile import ZipFile

from oakhack import DATA_DIR

# %%
jsonzipfile = DATA_DIR / "oak_json.zip"

# open zip file
zip = ZipFile(jsonzipfile, "r")

# list files in archive
namelist = zip.namelist()

# get all json files for english, ks2, using glob pattern
namelist_filtered = fnmatch.filter(namelist, "*/english*-ks2*.json")

# iterate over and load the json
jsonlist_filtered = []
for name in namelist_filtered:
    with zip.open(name) as f:
        jsonlist_filtered.append(json.load(f))

# close the zip
zip.close()

# %%
### Same thing in a context manager

with ZipFile(jsonzipfile, "r") as zip:
    namelist = zip.namelist()
    namelist_filtered = fnmatch.filter(namelist, "*/english*-ks2*.json")
    jsonlist_filtered = []
    for name in namelist_filtered:
        with zip.open(name) as f:
            jsonlist_filtered.append(json.load(f))