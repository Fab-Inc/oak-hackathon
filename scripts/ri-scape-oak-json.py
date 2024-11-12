# %%
import json
import yaml
import requests
from pathlib import Path
from bs4 import BeautifulSoup as BSoup
from oakhack import PROJ_ROOT, DATA_DIR
import json

OUT_DIR = DATA_DIR / "oak_scraped_json_nov24"
OUT_DIR.mkdir(parents=True, exist_ok=True)

base_url = "https://www.thenational.academy/teachers/"
key_stages = "key-stages"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
}
outdir = OUT_DIR

# %%
# key stages 1-4
for i in range(1, 5):
    ks_slug = f"ks{i}"
    stages_url = f"{base_url}key-stages/{ks_slug}/subjects"
    print(stages_url)

    response = requests.get(stages_url, headers=headers)
    if response.status_code == 200:
        print("OK")

        soup = BSoup(response.text, "lxml")

        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        index_data = json.loads(script_tag.string)
        with open(outdir / f"{ks_slug}-subjects.json", "w") as file:
            json.dump(index_data, file, indent=2)

        # subjects
        for subject in index_data["props"]["pageProps"]["subjects"]:
            if ks_slug=="ks4" and subject["data"]["isNew"]:
                # new ks4 are by exam board and use the loop below
                # old ks4 are the same as others
                continue
            programme_slug = subject["data"]["programmeSlug"]
            print(programme_slug)
            subject_url = f"https://www.thenational.academy/teachers/programmes/{programme_slug}/units"
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
                #if u[0]["cohort"] == "2023-2024"
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
                        if lessons_to_get[k]["expired"] == True:
                            # lesson not available
                            continue
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
