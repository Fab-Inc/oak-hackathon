# %%
import json
import yaml
import requests
from pathlib import Path
from bs4 import BeautifulSoup as BSoup
from oakhack import PROJ_ROOT, DATA_DIR
import json

# OUT_DIR = DATA_DIR / "oak_scraped_json_nov24"
OUT_DIR = DATA_DIR / "oak_scraped_json_curricula_nov24"
OUT_DIR.mkdir(parents=True, exist_ok=True)
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
}
outdir = OUT_DIR

# %%
# get all curricula pages
index_url = "https://www.thenational.academy/teachers/curriculum"
response = requests.get(index_url, headers=headers)
response.raise_for_status()
soup = BSoup(response.text, "lxml")
script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
index_data = json.loads(script_tag.string)
with open(outdir / "index.json", "w") as file:
    json.dump(index_data, file)

subjects = index_data["props"]["pageProps"]["subjectPhaseOptions"]["subjects"]
phases = ["primary", "secondary"]

#%%
def save_json_from_page(url,slug):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BSoup(response.text, "lxml")
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    index_data = json.loads(script_tag.string)
    with open(outdir / f"{slug}.json", "w") as file:
        json.dump(index_data, file)
# %%
phase = "primary"
for subject in subjects:
    page_slug = f"{subject['slug']}-{phase}"
    subject_url = f"{index_url}/{page_slug}/units"
    print(subject_url)
    save_json_from_page(subject_url, page_slug)

# %%
phase = "secondary"
for subject in subjects:
    if subject["ks4_options"]:
        for ks4_option in subject["ks4_options"]:
            page_slug = f"{subject['slug']}-{phase}-{ks4_option['slug']}"
            subject_url = f"{index_url}/{page_slug}/units"
            print(subject_url)
            save_json_from_page(subject_url, page_slug)
    else:
        page_slug = f"{subject['slug']}-{phase}"
        subject_url = f"{index_url}/{page_slug}/units"
        print(subject_url)
        save_json_from_page(subject_url, page_slug) 


# %%
