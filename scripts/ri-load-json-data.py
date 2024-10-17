# %%
from oakhack import PROJ_ROOT, DATA_DIR
import zipfile as zf
import itertools as it
import gzip
import json

mbsse_lp_file = DATA_DIR / "mbsse_lp/mbsseKP_files_lessonplans_parsed.json.gz"
oak_json_file = DATA_DIR / "oak_json.zip"

# %%
# load oak data

# load programmes
with zf.ZipFile(oak_json_file) as zip:
    info = zip.infolist()
    programme_filenames = [
        f.filename for f in info if f.is_dir() and len(f.filename.split("/")) == 3
    ]
    programmes = {}
    for p in programme_filenames:
        with zip.open(p + "units.json") as f:
            pj = json.load(f)["props"]["pageProps"]["curriculumData"]
        programmes[pj["programmeSlug"]] = pj


def get_programmes_by_ks(programmes, ks):
    return {k: v for k, v in programmes.items() if v["keyStageSlug"] == f"ks{ks}"}


def get_programmes_by_subject(programmes, subject):
    return {k: v for k, v in programmes.items() if v["subjectSlug"] == subject}


# load units
with zf.ZipFile(oak_json_file) as zip:
    units_by_programme = {}
    for pslug, p in programmes.items():
        units_by_programme[pslug] = {}
        for unit in p["units"]:
            if unit[0]["cohort"] != "2023-2024":
                continue

            fname = "oak_scraped_json/" + pslug + "/" + unit[0]["slug"] + "/lessons.json"
            with zip.open(fname) as f:
                units_by_programme[pslug][unit[0]["slug"]] = json.load(f)["props"]["pageProps"][
                    "curriculumData"
                ]

# %%
# load lessons
lessons_by_unit = {}
with zf.ZipFile(oak_json_file) as zip:
    all_units = it.chain.from_iterable([list(v.values()) for v in units_by_programme.values()])
    for units in units_by_programme.values():
        for unit in units.values():
            unit_path = unit["programmeSlug"] + "/" + unit["unitSlug"]
            base_path = "oak_scraped_json/" + unit_path
            lessons_by_unit[unit_path] = {}

            for lesson in unit["lessons"]:
                fname = base_path + "/" + lesson["lessonSlug"] + ".json"
                with zip.open(fname) as f:
                    lessons_by_unit[unit_path][lesson["lessonSlug"]] = json.load(f)["props"][
                        "pageProps"
                    ]["curriculumData"]

# %%
with gzip.open(mbsse_lp_file) as f:
    mbsse_lp_data = json.load(f)
