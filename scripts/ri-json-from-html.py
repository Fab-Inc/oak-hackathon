# %%
from oakhack import PROJ_ROOT, DATA_DIR
from bs4 import BeautifulSoup
import json
DATA_DIR = DATA_DIR / "sample_lesson"

with open(DATA_DIR / "sample_lesson.html", "r") as file:
    soup = BeautifulSoup(file, "lxml")
# %%
script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
lesson_data = json.loads(script_tag.string)
with open(DATA_DIR / "sample_lesson_next_data.json", "w") as file:
    json.dump(lesson_data, file, indent=2)
# %%

# Download all 
# <a role="link" data-testid="download-all-button" title="Download all resources"
#     href="/teachers/programmes/biology-secondary-ks4-foundation-aqa/units/eukaryotic-and-prokaryotic-cells/lessons/cells/downloads?preselected=all"
#     class="sc-5368bac2-0 gJhAja">

# Share all
# <a role="link" data-testid="share-all-button" title="Share activities with pupils" aria-disabled="false"
#     href="/teachers/programmes/biology-secondary-ks4-foundation-aqa/units/eukaryotic-and-prokaryotic-cells/lessons/cells/share?preselected=all"
#     class="sc-5368bac2-0 gJhAja">


#%%
with open(DATA_DIR / "splitpage.json", "r") as file:
    d = json.load(file)

# %%
# Index Page
#
#
with open(DATA_DIR / "english-index.html", "r") as file:
    soup = BeautifulSoup(file, "lxml")
#
script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
index_data = json.loads(script_tag.string)
units_to_get = [u[0] for u in index_data['props']['pageProps']['curriculumData']['units'] if u[0]['cohort']=='2023-2024']
unit_urls = [f"https://www.thenational.academy/teachers/programmes/{u['programmeSlug']}/units/{u['slug']}/lessons" for u in units_to_get]



# %%
# Unit Page
#
#
with open(DATA_DIR / "unit_page.html", "r") as file:
    soup = BeautifulSoup(file, "lxml")
script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
unit_data = json.loads(script_tag.string)
with open(DATA_DIR / "sample_unit_index.json", "w") as file:
    json.dump(unit_data, file, indent=2)
#%%
unit_url = "https://www.thenational.academy/teachers/programmes/english-primary-ks1/units/spoken-language-sharing-your-opinion/lessons"
lesson_data = unit_data['props']['pageProps']['curriculumData']['lessons']
#https://www.thenational.academy/teachers/programmes/english-primary-ks1/units/spoken-language-sharing-your-opinion/lessons/sharing-an-opinion-by-speaking-loudly-and-clearly#slide-deck
lesson_urls = [unit_url + "/" + l['lessonSlug'] for l in lesson_data]
