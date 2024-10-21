# %%
import oakhack as oh
import zipfile as zf
import itertools as it

from oakhack import DATA_DIR

mbsse_lp_file = DATA_DIR / "mbsse_lp/mbsseKP_files_lessonplans_parsed.json.gz"
oak_json_file = DATA_DIR / "oak_json.zip"

programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
questions, q_df = oh.utils.extract_questions(lessons)

# %%

question = questions[0]
q_text = []
q_image = []
for block in question["questionStem"]:
    if block["type"] == "text":
        q_text.append(block["text"])
    if block["type"] == "image":
        q_image.append(block["imageObject"]["url"])
if question["questionType"] == "multiple-choice":
    for answer in question["answers"]["multiple-choice"]:
        # only keep correct answer options
        if answer["answerIsCorrect"]:
            for block in answer["answer"]:
                if block["type"] == "text":
                    q_text.append(block["text"])
                else:
                    print(f"found multiple-choice answer block of type: {block["type"]}")
q_text.extend([question[k] for k in ["hint", "feedback"]])

# %%
