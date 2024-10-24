# %%
import json
import yaml
import requests
from pathlib import Path
from bs4 import BeautifulSoup as BSoup
from oakhack import PROJ_ROOT, DATA_DIR
import json

OUT_DIR = DATA_DIR / "oak_scraped_json"


def pageWebContainers(page_data, element):
    element = "li.sc-fb6fa463-0 > div"
    subjects = page_data.select(element)
    subjects_url = []
    for subject in subjects:
        label = subject.find("span", {"class": "hHBExW"})
        if label:
            url = subject.find("a", class_="hXdIPD")["href"]
            subject_name = subject.find("h2", {"class": "fBzdXp"}).text
            subjects_url.append({subject_name: url})
    return subjects_url


base_url = "https://www.thenational.academy/teachers/"
key_stages = "key-stages"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
}
outdir = OUT_DIR

# %%
# key stages 1-3
for i in range(1, 4):
    stages_url = f"{base_url}key-stages/ks{i}/subjects"
    print(stages_url)

    response = requests.get(stages_url, headers=headers)
    if response.status_code == 200:
        print("OK")

        soup = BSoup(response.text, "lxml")

        # subjects
        access_urls = pageWebContainers(soup, "ABC")

        for subject_dict in access_urls:
            subject = list(subject_dict.keys())[0]
            url = subject_dict[subject]
            subject_url = "https://www.thenational.academy" + url
            response = requests.get(subject_url, headers=headers)
            soup = BSoup(response.text, "lxml")

            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

            index_data = json.loads(script_tag.string)

            subject_folder = index_data["props"]["pageProps"]["curriculumData"]["programmeSlug"]
            programme_folder = outdir / subject_folder
            programme_folder.mkdir(exist_ok=True, parents=True)

            with open(programme_folder / "units.json", "w") as file:
                json.dump(index_data, file, indent=2)

            units_to_get = [
                u[0]
                for u in index_data["props"]["pageProps"]["curriculumData"]["units"]
                if u[0]["cohort"] == "2023-2024"
            ]  # cohort

            programmes_url = (
                "https://www.thenational.academy/teachers/programmes/" + subject_folder
            )
            unit_urls = [f"{programmes_url}/units/{un['slug']}/lessons" for un in units_to_get]

            ## going through each unit url generated above
            for url in unit_urls:
                response = requests.get(url, headers=headers)

                soup = BSoup(response.text, "lxml")

                if response.status_code == 200:
                    soup = BSoup(response.text, "lxml")

                    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

                    index_data = json.loads(script_tag.string)

                    ## create sub folder and save the second iteration
                    unit_folder_str = index_data["props"]["pageProps"]["curriculumData"][
                        "unitSlug"
                    ]
                    unit_folder = programme_folder / unit_folder_str
                    unit_folder.mkdir(exist_ok=True)

                    with open(unit_folder / "lessons.json", "w") as file:
                        json.dump(index_data, file, indent=2)

                    lessons_to_get = [
                        u for u in index_data["props"]["pageProps"]["curriculumData"]["lessons"]
                    ]

                    prefix_url = programmes_url + "/" + "units/" + unit_folder_str
                    lesson_urls = [
                        f"{prefix_url}/lessons/{u['lessonSlug']}" for u in lessons_to_get
                    ]

                    for k, url in enumerate(lesson_urls):
                        response = requests.get(url, headers=headers)

                        soup = BSoup(response.text, "lxml")

                        if response.status_code == 200:
                            soup = BSoup(response.text, "lxml")

                            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

                            index_data = json.loads(script_tag.string)

                            lesson_slug = index_data["props"]["pageProps"]["curriculumData"][
                                "lessonSlug"
                            ]

                            with open(unit_folder / f"{lesson_slug}.json", "w") as file:
                                json.dump(index_data, file, indent=2)

#%% 
# ks4 
i = 4
stages_url = f"{base_url}key-stages/ks{i}/subjects"
print(stages_url)

response = requests.get(stages_url, headers=headers)
if response.status_code == 200:
    print("OK")

    soup = BSoup(response.text, "lxml")

    # subjects
    access_urls = pageWebContainers(soup, "ABC")

    for subject_dict in access_urls:
        subject = list(subject_dict.keys())[0]
        url = subject_dict[subject]
        subject_url = "https://www.thenational.academy" + url
        response = requests.get(subject_url, headers=headers)
        soup = BSoup(response.text, "lxml")

        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

        index_data = json.loads(script_tag.string)

        for programme in index_data["props"]["pageProps"]["programmes"]:
            programme_slug = programme["programmeSlug"]
            programme_folder = outdir / programme_slug
            programme_folder.mkdir(exist_ok=True, parents=True)

            programme_url = f"https://www.thenational.academy/teachers/programmes/{programme_slug}"
            response = requests.get(programme_url + "/units", headers=headers)
            soup = BSoup(response.text, "lxml")
            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
            index_data = json.loads(script_tag.string)
            with open(programme_folder / "units.json", "w") as file:
                json.dump(index_data, file, indent=2)

            units_to_get = [
                u[0]
                for u in index_data["props"]["pageProps"]["curriculumData"]["units"]
                if u[0]["cohort"] == "2023-2024"
            ]  # cohort

            unit_urls = [f"{programme_url}/units/{un['slug']}/lessons" for un in units_to_get]

            ## going through each unit url generated above
            for url in unit_urls:
                response = requests.get(url, headers=headers)

                soup = BSoup(response.text, "lxml")

                if response.status_code == 200:
                    soup = BSoup(response.text, "lxml")

                    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

                    index_data = json.loads(script_tag.string)

                    ## create sub folder and save the second iteration
                    unit_folder_str = index_data["props"]["pageProps"]["curriculumData"][
                        "unitSlug"
                    ]
                    unit_folder = programme_folder / unit_folder_str
                    unit_folder.mkdir(exist_ok=True)

                    with open(unit_folder / "lessons.json", "w") as file:
                        json.dump(index_data, file, indent=2)

                    lessons_to_get = [
                        u for u in index_data["props"]["pageProps"]["curriculumData"]["lessons"]
                    ]

                    prefix_url = programme_url + "/" + "units/" + unit_folder_str
                    lesson_urls = [
                        f"{prefix_url}/lessons/{u['lessonSlug']}" for u in lessons_to_get
                    ]

                    for k, url in enumerate(lesson_urls):
                        response = requests.get(url, headers=headers)

                        soup = BSoup(response.text, "lxml")

                        if response.status_code == 200:
                            soup = BSoup(response.text, "lxml")

                            script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

                            index_data = json.loads(script_tag.string)

                            lesson_slug = index_data["props"]["pageProps"]["curriculumData"][
                                "lessonSlug"
                            ]

                            with open(unit_folder / f"{lesson_slug}.json", "w") as file:
                                json.dump(index_data, file, indent=2)

# %%
with open(DATA_DIR / "ks4_desbug.json", "w") as file:
    json.dump(index_data["props"]["pageProps"], file, indent=2)
# %%
