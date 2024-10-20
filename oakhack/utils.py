import zipfile as zf
import json
import itertools as it
from pathlib import Path
import pandas as pd

from .constants import DATA_DIR


def get_programmes_by_ks(programmes, ks):
    return {k: v for k, v in programmes.items() if v["keyStageSlug"] == f"ks{ks}"}


def get_programmes_by_subject(programmes, subject):
    return {k: v for k, v in programmes.items() if v["subjectSlug"] == subject}


def flatten(xss):
    return [x for xs in xss for x in xs]


def load_oak_programmes_units(oak_json_file=DATA_DIR / "oak_json.zip"):
    with zf.ZipFile(oak_json_file) as zip:

        # load programmes
        info = zip.infolist()
        programme_filenames = [
            f.filename for f in info if f.is_dir() and len(f.filename.split("/")) == 3
        ]
        programmes = {}
        for p in programme_filenames:
            with zip.open(p + "units.json") as f:
                pj = json.load(f)["props"]["pageProps"]["curriculumData"]
            programmes[pj["programmeSlug"]] = pj

        # load units
        units_by_programme = {}
        for pslug, p in programmes.items():
            units_by_programme[pslug] = {}
            for unit in p["units"]:
                if unit[0]["cohort"] != "2023-2024":
                    continue

                fname = "oak_scraped_json/" + pslug + "/" + unit[0]["slug"] + "/lessons.json"
                with zip.open(fname) as f:
                    units_by_programme[pslug][unit[0]["slug"]] = json.load(f)["props"][
                        "pageProps"
                    ]["curriculumData"]

    return programmes, units_by_programme


def load_oak_lessons(oak_json_file=DATA_DIR / "oak_json.zip"):

    programmes, units_by_programme = load_oak_programmes_units(oak_json_file)

    with zf.ZipFile(oak_json_file) as zip:

        # load lessons
        programm_inherit_fields = ["examBoardSlug", "subjectParent"]
        unit_inherit_fields = ["unitStudyOrder", "yearOrder", "learningThemes"]
        lessons_by_unit = {}
        for units in units_by_programme.values():
            for unit in units.values():
                pj = programmes[unit["programmeSlug"]]

                unit_path = unit["programmeSlug"] + "/" + unit["unitSlug"]
                base_path = "oak_scraped_json/" + unit_path
                lessons_by_unit[unit_path] = {}

                for lesson in unit["lessons"]:
                    fname = base_path + "/" + lesson["lessonSlug"] + ".json"
                    with zip.open(fname) as f:
                        lbu = json.load(f)["props"]["pageProps"]["curriculumData"]
                        for key in programm_inherit_fields:
                            lbu[key] = pj[key]
                        for key in unit_inherit_fields:
                            lesson_unit = [
                                unt[0] for unt in pj["units"] if unt[0]["slug"] == unit["unitSlug"]
                            ]
                            if len(lesson_unit) != 1:
                                raise ValueError("should be exactly one lesson unit")
                            else:
                                lesson_unit = lesson_unit[0]
                            lbu[key] = lesson_unit[key]
                        lessons_by_unit[unit_path][lesson["lessonSlug"]] = lbu

    return flatten([[l for l in us.values()] for us in lessons_by_unit.values()])


def load_oak_lessons_with_df(oak_json_file=DATA_DIR / "oak_json.zip"):
    """Load all Oak lessons in a flat list, with metadata fields added

    Returns the flat list, and a dataframe indexed matching the list:
    >> lessons, l_df = load_oak_lessons_with_df()
    >> query_res = [
           lessons[i] for i in l_df.query("subjectSlug == 'english' and "
                                          "keyStageSlug == 'ks2'").index
       ]
    """
    lessons_l = load_oak_lessons(oak_json_file=oak_json_file)

    # build df of metadata
    column_keys = [
        "lessonSlug",
        "lessonTitle",
        "programmeSlug",
        "unitSlug",
        "keyStageSlug",
        "tierSlug",
        "contentGuidance",
        "additionalMaterialUrl",
        "worksheetUrl",
        "presentationUrl",
        # "transcriptSentences",
        "videoTitle",
        "subjectSlug",
        # "subjectTitle",
        # "upplementary-pdf",
        # "supplementary-docx",
        "examBoardSlug",
        "subjectParent",
        "unitStudyOrder",
        "yearOrder",
        "learningThemes",
    ]

    df_data = {}
    for col in column_keys:
        df_data[col] = [l[col] for l in lessons_l]

    df_data["unitKey"] = [l["programmeSlug"] + "/" + l["unitSlug"] for l in lessons_l]
    df_data["lessonKey"] = [
        l["programmeSlug"] + "/" + l["unitSlug"] + "/" + l["lessonSlug"] for l in lessons_l
    ]
    lessons_df = pd.DataFrame(df_data)

    return lessons_l, lessons_df


def extract_questions(lessons):
    """Extract a flat list of all available questions, with metadata fields added

    Returns the flat list, and a dataframe indexed matching the list:
    >> questions, questions_df = extract_questions(lesssons)
    >> query_res = [
            questions[i] for i in questions_df.query("questionType == 'short-answer' and "
                                                      "subjectSlug == 'physics'").index
        ]
    """

    # extract questions and add some metadata from the parent lesson
    questions = []
    for lesson in lessons:
        for quiztype in ["starter", "exit"]:
            quiz_questions = lesson[quiztype + "Quiz"]
            if quiz_questions is None:
                continue
            for question in lesson[quiztype + "Quiz"]:
                question["quizType"] = quiztype
                for k in [
                    "programmeSlug",
                    "lessonSlug",
                    "unitSlug",
                    "tierSlug",
                    "examBoardTitle",
                    "subjectSlug",
                    "keyStageSlug",
                ]:
                    question[k] = lesson[k]
                questions.append(question)

    # build dataframe of question metadata
    column_keys = [
        "lessonSlug",
        "programmeSlug",
        "unitSlug",
        "keyStageSlug",
        "tierSlug",
        "subjectSlug",
        "examBoardTitle",
        "questionId",
        "questionUid",
        "questionType",
        "quizType",
    ]
    df_data = {}
    for col in column_keys:
        df_data[col] = [q[col] for q in questions]

    df_data["unitKey"] = [q["programmeSlug"] + "/" + q["unitSlug"] for q in questions]
    df_data["lessonKey"] = [
        q["programmeSlug"] + "/" + q["unitSlug"] + "/" + q["lessonSlug"] for q in questions
    ]
    questions_df = pd.DataFrame(df_data)

    return questions, questions_df
