# %%
import oakhack as oh
import requests
import os

base_url = "https://open-api.thenational.academy/api/v0"
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {os.getenv('OAK_API_KEY')}"})


def get(endpoint, params):
    url = base_url + endpoint
    print(url)
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
keyStage = "ks2"
subject = "english"
lessons = get(f"/key-stages/{keyStage}/subject/{subject}/lessons", params=params)
# get /key-stages/{keyStage}/subject/{subject}/lessons
# ?unit ?offset ?limit
# returns [ "unitSlug" "unitTitle" "lessons":[ "lessonTitle" "lessonSlug"]]

# get /lessons/{lesson}/summary
# { "keyLearningPoints"}

# get /lessons/{lesson}/quiz
# list of questions
# print(lessons[0])
# %%
