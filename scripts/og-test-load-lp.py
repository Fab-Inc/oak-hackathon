# %%
import gzip
import json

from oakhack import DATA_DIR

# %%
with gzip.open(DATA_DIR / "mbsse_lp/mbsseKP_files_lessonplans_parsed_cleaned.json.gz") as f:
    lpdata = json.load(f)