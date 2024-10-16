# %%
import gzip
import json

from dotenv import load_dotenv

load_dotenv(override=True)

from fdllm import get_caller
from fdllm.extensions import general_query
import numpy as np

from oakhack import DATA_DIR


def lp_sampler(lpdata, size=None, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    elif isinstance(rng, int):
        rng = np.random.default_rng(rng)

    nfiles = len(lpdata)
    filesampi = rng.choice(nfiles, size)
    lpsamps = []
    for filei in filesampi:
        filedata = lpdata[filei]
        lpsamp = rng.choice(filedata["plans"])
        lpsamps.append(lpsamp)

    return lpsamps


# %%
lpfile = DATA_DIR / "mbsse_lp/mbsseKP_files_lessonplans_parsed_cleaned.json.gz"
with gzip.open(lpfile) as f:
    lpdata = json.load(f)

oaklessonfile = DATA_DIR / "sample_lesson/sample_lesson_next_data.json"
with open(oaklessonfile) as f:
    oaklessondata = json.load(f)

# %%
nexamples = 20
seed = 83252023554

sample_plans = lp_sampler(lpdata, size=nexamples, rng=seed)

print(sample_plans)

jsonin = {
    "source_lesson": oaklessondata,
    "target_format:: Examples of target format": sample_plans,
}

jsonout = {
    "generated_lessons"
    ":: Generate one new lesson based the content of source_lesson, but matching it to"
    " the style, length, language, naming conventions, and level of resources displayed in target_format": [
        {
            "Lesson Title": None,
            "Theme": None,
            "Lesson Number": None,
            "Class/Level": "Class 10",
            "Time": "45 minutes",
            "Body": {
                "Learning Outcomes": {
                    "markdown": None,
                    "duration": None,
                },
                "Teaching Aids": {
                    "markdown": None,
                    "duration": None,
                },
                "Preparation": {
                    "markdown": None,
                    "duration": None,
                },
                "Opening": {
                    "markdown": None,
                    "duration": None,
                },
                "Introduction to the New Material": {
                    "markdown": None,
                    "duration": None,
                },
                "Guided Practice": {
                    "markdown": None,
                    "duration": None,
                },
                "Independent Practice": {
                    "markdown": None,
                    "duration": None,
                },
                "Closing": {
                    "markdown": None,
                    "duration": None,
                },
            },
            "meta_format": None,
            "body_format": None,
            "extra": [
                {
                    "heading": None,
                    "markdown": None,
                }
            ],
        }
    ]
}

caller = get_caller("gpt-4o-2024-08-06")

out = general_query(jsonin, jsonout, caller=caller, temperature=0)

print(json.dumps(out, indent=4))