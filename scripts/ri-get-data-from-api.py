#%%
import oakhack as oh
import requests

base_url = "unknown"
session = requests.Session()
access_token = "ABCD"
session.headers.update({'Authorization': 'Bearer {access_token}'})
def get(endpoint, params):
    return session.get(base_url+endpoint).json()

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
#%%
# get /key-stages
# returns: ["slug" "title"]
keystages = get("/key-stages")

# get /key-stages/{keyStage}/subjects
# returns: ["subjectSlug" "subjectTitle"]

# get /key-stages/{keyStage}/subject/{subject}/units
# returns ["unitSlug" "unitTitle"]

params = {"unit": "xxx"}
lessons = get(f"/key-stages/{keyStage}/subject/{subject}/lessons", params=params)
# get /key-stages/{keyStage}/subject/{subject}/lessons
# ?unit ?offset ?limit
# returns [ "unitSlug" "unitTitle" "lessons":[ "lessonTitle" "lessonSlug"]]

# get /lessons/{lesson}/summary
# { "keyLearningPoints"}

#get /lessons/{lesson}/quiz
# list of questions