# %%
from typing import Optional, Literal
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

# %%
with ZipFile(jsonzipfile, "r") as zip:
    namelist = zip.namelist()

    namelist_filtered = fnmatch.filter(namelist, "*/units.json")
    # load all units
    units_json = []
    for name in namelist_filtered:
        with zip.open(name) as f:
            units_json.append(json.load(f)["props"]["pageProps"]["curriculumData"])

# %%
units_json[0]


# %%
class OakLessonJson:
    def __init__(self, jsonlist: Optional[list] = None):
        if jsonlist is None:
            jsonlist = []
        self.jsonlist = jsonlist
        self._gen_query_keys_vals()

    def append(self, val):
        self.jsonlist.append(val)
        self._gen_query_keys_vals()

    def _gen_query_keys_vals(self):
        self.query_keys = set(
            [
                key
                for ujson in self.jsonlist
                for key, val in ujson.items()
                if not isinstance(val, (list, dict))
            ]
        )
        self.query_key_vals = {
            key: set([ujson[key] for ujson in self.jsonlist]) for key in self.query_keys
        }

    def query(self, **query):
        outjslist = []
        for json in self.jsonlist:
            for key, val in query.items():
                if json[key] == val:
                    outjslist.append(json)
                    break
        return outjslist


class OakLevel:
    def __init__(
        self, level: Literal["programme", "unit"], parent: str="", catfile=DATA_DIR / "oak_json.zip"
    ):
        self.catfile = catfile
        if level == "programme":
            jsfile = "units.json"
        elif level == "unit":
            jsfile = "lessons.json"
        with ZipFile(catfile, "r") as zip:
            namelist = zip.namelist()
            namelist_filtered = fnmatch.filter(namelist, f"*{parent}/{jsfile}")
            # load all units
            self.jsonlist = OakLessonJson()
            for name in namelist_filtered:
                with zip.open(name) as f:
                    self.jsonlist.append(json.load(f)["props"]["pageProps"]["curriculumData"])

    def query(self, **query):
        return [
            OakLevel(self.jsonlist.query(**query))
        ]

    @property
    def query_keys(self):
        return self.jsonlist.query_keys

    @property
    def query_key_vals(self):
        return self.jsonlist.query_key_vals


# %%
oaklprog = OakLevel("programme")

print(oaklprog.query_keys)
print(oaklprog.query_key_vals)

query_res = oaklprog.query(subjectTitle="Biology", phase="secondary", keyStageSlug="ks4")
print(len(query_res))
print(query_res[0])
