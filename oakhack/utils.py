import zipfile as zf
import json
import itertools as it
from pathlib import Path
import pandas as pd
import numpy as np
import gzip

from collections import defaultdict
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

                fname = (
                    "oak_scraped_json/"
                    + pslug
                    + "/"
                    + unit[0]["slug"]
                    + "/lessons.json"
                )
                with zip.open(fname) as f:
                    units_by_programme[pslug][unit[0]["slug"]] = json.load(f)["props"][
                        "pageProps"
                    ]["curriculumData"]

    return programmes, units_by_programme


def load_oak_lessons(oak_json_file=DATA_DIR / "oak_json.zip"):
    """Load all lessons from Oak from a zip archive of the scraped json

    Returns a flat list of all the lessons"""

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
                                unt[0]
                                for unt in pj["units"]
                                if unt[0]["slug"] == unit["unitSlug"]
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
        l["programmeSlug"] + "/" + l["unitSlug"] + "/" + l["lessonSlug"]
        for l in lessons_l
    ]
    lessons_df = pd.DataFrame(df_data)

    return lessons_l, lessons_df


def extract_klp(lessons=None):
    """Extract all available key learning points

    Returns a dict with keys:
    "<programmeSlug>/<unitSlug>/<lessonSlug>/<key-learning-point-index>"
    and values as a dict with 'keyLearningPoint' and other metadata.

    If key cache file exists, keys are validated against cached keys, otherwise cache file is
    created.
    """

    if lessons is None:
        lessons = load_oak_lessons()

    lesson_keys = [
        "subjectSlug",
        "examBoardSlug",
        "unitStudyOrder",
        "yearOrder",
        "keyStageSlug",
        "tierSlug",
    ]
    flat_klp = {
        f"{lesson['programmeSlug']}/{lesson['unitSlug']}/{lesson['lessonSlug']}/{klpidx}": {
            "l_index": lidx,
            "klp_index": klpidx,
            **{key: lesson[key] for key in lesson_keys},
            "keyLearningPoint": klp["keyLearningPoint"],
        }
        for lidx, lesson in enumerate(lessons)
        for klpidx, klp in enumerate(lesson["keyLearningPoints"])
    }

    flat_klp_index = list(flat_klp)
    index_file = DATA_DIR / "flat_klp_index.json.gz"
    if index_file.exists():
        with gzip.open(index_file, "rt") as f:
            flat_klp_index_cache = json.load(f)
        if flat_klp_index_cache != flat_klp_index:
            raise ValueError("Index doesn't match cache")
    else:
        with gzip.open(index_file, "wt") as f:
            json.dump(flat_klp_index, f)

    return flat_klp


def extract_klp_with_df(flat_klp=None):
    if flat_klp is None:
        flat_klp = extract_klp()
    flat_klp_l = []
    for k,v in flat_klp.items():
        flat_klp_l.append({"klp_key":k, **v})

    # build a klp index dataframe
    data_df = defaultdict(list)
    for klp in flat_klp_l:
        programme, unit, lesson, klp_idx = klp["klp_key"].split("/")
        lesson_key = "/".join([programme, unit, lesson])
        data_df['programme'].append(programme)
        data_df['unit'].append(unit)
        data_df['lesson'].append(lesson)
        data_df['lesson_key'].append(lesson_key)
        data_df['l_klp_idx'].append(klp_idx)
        lesson_keys = {
            "subject":"subjectSlug",
            "examBoard": "examBoardSlug",
            "tier": "tierSlug",
            "ks": "keyStageSlug",
        }
        [data_df[k].append(klp[v]) for k,v in lesson_keys.items()]
        lesson_keys = ["unitStudyOrder","yearOrder"]
        [data_df[k].append(klp[k]) for k in lesson_keys]

    klp_df = pd.DataFrame(data_df)
    return flat_klp_l, klp_df



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
        q["programmeSlug"] + "/" + q["unitSlug"] + "/" + q["lessonSlug"]
        for q in questions
    ]
    questions_df = pd.DataFrame(df_data)

    return questions, questions_df


def extract_question_content(questions):
    """Extract relevant content from questions

    Includes: question, correct answers, hint and feedback
    Ignores: wrong answers
    Returns both text and image lists

    To get a single string representation of each question:
    >> extracted_questions = extract_question_content(questions)
    >> q_strs = ["\n".join([q["text"]) for q in extracted_questions]
    """
    extracted_questions = []
    for question in questions:
        q_text = []
        q_image = []
        for block in question["questionStem"]:
            if block["type"] == "text":
                q_text.append(block["text"])
            if block["type"] == "image":
                q_image.append(block["imageObject"]["url"])

        if question["questionType"] == "multiple-choice":
            if question["answers"] is not None:
                for answer in question["answers"]["multiple-choice"]:
                    # only keep correct answer options
                    if answer["answerIsCorrect"]:
                        for block in answer["answer"]:
                            if block["type"] == "text":
                                q_text.append(block["text"])
                            elif block["type"] == "image":
                                q_image.append(block["imageObject"]["url"])
                            else:
                                print(
                                    f"found multiple-choice answer block of type: {block["type"]}"
                                )

        elif question["questionType"] == "order":
            for answer in question["answers"]["order"]:
                # add all answer options (ignore order)
                for block in answer["answer"]:
                    if block["type"] == "text":
                        q_text.append(block["text"])
                    else:
                        print(f"found order answer block of type: {block["type"]}")

        elif question["questionType"] == "match":
            for answer in question["answers"]["match"]:
                # add all answer stems and match words
                for blocks in it.chain(
                    [answer[k] for k in ["correctChoice", "matchOption"]]
                ):
                    for block in blocks:
                        if block["type"] == "text":
                            q_text.append(block["text"])
                        else:
                            print(f"found match answer block of type: {block["type"]}")

        elif question["questionType"] == "short-answer":
            if question["answers"] is not None:
                for answer in question["answers"]["short-answer"]:
                    for block in answer["answer"]:
                        if block["type"] == "text":
                            q_text.append(block["text"])
                        else:
                            print(
                                f"found short-answer answer block of type: {block["type"]}"
                            )

        q_text.extend([question[k] for k in ["hint", "feedback"]])

        q = {"text": [t for t in q_text if t], "images": q_image}
        extracted_questions.append(q)

    return extracted_questions


def load_embeddings(filename_pattern):
    """Load precalculated embeddings from batched files matching filename_pattern

    >> klp_embs = load_embeddings("klp_embeddings_batch_size3000_*.npy")
    """
    load_arrs = []
    for f in sorted((DATA_DIR / "embeddings").glob(filename_pattern)):
        load_arrs.append(np.load(f))
    return np.concatenate(load_arrs, axis=0)
