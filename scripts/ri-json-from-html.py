# %%
from oakhack.config import PROJ_ROOT, DATA_DIR
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