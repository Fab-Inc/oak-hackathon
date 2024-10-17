# %%
from oakhack import PROJ_ROOT, DATA_DIR
import zipfile as zf
import gzip
import json

mbsse_lp_file = DATA_DIR / "mbsse_lp/mbsseKP_files_lessonplans_parsed.json.gz"
oak_json_file = DATA_DIR / "oak_json.zip"

# %%
# load oak data

# load programmes
with zf.ZipFile(oak_json_file) as file:
    info = file.infolist()
    programme_filenames = [f.filename for f in info if f.is_dir() and len(f.filename.split("/")) == 3]
    programmes = {}
    for p in programme_filenames:
        pj = json.loads(zf.Path(oak_json_file, p + "units.json").read_text())['props']['pageProps']['curriculumData']
        programmes[pj["programmeSlug"]] = pj

def get_programmes_by_ks(programmes, ks):
    return {k: v for k,v in programmes.items() if v["keyStageSlug"]== f"ks{ks}"}

def get_programmes_by_subject(programmes, subject):
    return {k: v for k,v in programmes.items() if v["subjectSlug"]== subject}


# %%
with gzip.open(mbsse_lp_file) as f:
    mbsse_lp_data = json.load(f)
