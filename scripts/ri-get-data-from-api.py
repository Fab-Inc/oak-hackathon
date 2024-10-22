# %%
import oakhack as oh
import requests
import os
from tqdm import tqdm
import json
import gzip

base_url = "https://open-api.thenational.academy/api/v0"
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {os.getenv('OAK_API_KEY')}"})

def get(endpoint, params):
    url = base_url + endpoint
    # print(url)
    return session.get(url, params=params).json()

# def get_items_pages(endpoint):
#     # Fetch the first page and return it
#     response = session.get(base_url+endpoint).json()
#     yield response['data']

#     # Loop over the remaining pages and return one at a time
#     # dont know if we have numPages or num items from oak api?
#     num_pages = response['page_info']['numPages']
#     for page in range(2, num_pages+1):
#         response = session.get(url, params={'page': page}).json()
#         yield response['data']
# %%
# get /key-stages
# returns: ["slug" "title"]
keystages = get("/key-stages", params={})

# get /key-stages/{keyStage}/subjects
# returns: ["subjectSlug" "subjectTitle"]

# get /key-stages/{keyStage}/subject/{subject}/units
# returns ["unitSlug" "unitTitle"]
# %%
#params = {"unit": "word-class"}
params = {
    "limit": "10", 
    # "offset": "10",
    }
keyStage = "ks4"
subject = "biology"
lessons = get(f"/key-stages/{keyStage}/subject/{subject}/lessons", params=params)
# get /key-stages/{keyStage}/subject/{subject}/lessons
# ?unit ?offset ?limit
# returns [ "unitSlug" "unitTitle" "lessons":[ "lessonTitle" "lessonSlug"]]

# get /lessons/{lesson}/summary
# { "keyLearningPoints"}

#%%
unit = 'eukaryotic-and-prokaryotic-cells'
unit_resp = get(f"/units/{unit}/summary", params={})
# get /lessons/{lesson}/quiz
# list of questions
# print(lessons[0])
# %%

lesson = 'cells'
lessonr = get(f"/lessons/{lesson}/summary", params={})
# %%
# %%
programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
unit = 'eukaryotic-and-prokaryotic-cells'
unit_resp = get(f"/units/{unit}/summary", params={})

unit_keys = ['priorKnowledgeRequirements',
'nationalCurriculumContent',
'priorUnit',
'futureUnit']

for programme in tqdm(units.values()):
    for unit,unit_data in programme.items():
        unit_resp = get(f"/units/{unit}/summary", params={}) 
        api_data = unit_resp
        unit_data.update(**{k:api_data.get(k,None) for k in unit_keys})

#%%
none_units = []
for programme in units.values():
    for unit in programme.values():
        if unit["priorKnowledgeRequirements"] is None:
            print(unit['unitSlug'])
            none_units.append(unit)

for unit in none_units:
    unit_resp = get(f"/units/{unit['unitSlug']}/summary", params={}) 
    print(unit_resp)
    
        
#%%

# lessons:
#'pupilLessonOutcome'
#'teacherTips'
lesson_keys = ['pupilLessonOutcome', 'teacherTips']

from concurrent.futures import ThreadPoolExecutor

# for lesson in tqdm(lessons):
#     lesson_resp = get(f"/lessons/{lesson['lessonSlug']}/summary", params={})
#     lesson.update(**{k:lesson_resp.get(k,None) for k in lesson_keys})

def update_lesson_from_api(lesson):
    lesson_resp = get(f"/lessons/{lesson['lessonSlug']}/summary", params={})
    lesson.update(**{k:lesson_resp.get(k,None) for k in lesson_keys})
    return lesson

with ThreadPoolExecutor(max_workers=16) as executor:
    results = list(executor.map(update_lesson_from_api, lessons))
lessons = results
# %%
#save updates
with gzip.open(oh.DATA_DIR / "lessons_with_api_updates.json.gz", "wt") as f:
    json.dump(results,f)
# %%
with gzip.open(oh.DATA_DIR / "units_with_api_updates.json.gz", "wt") as f:
    json.dump(units,f)
# %%
