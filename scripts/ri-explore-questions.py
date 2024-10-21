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
question_types = q_df.questionType.unique()
# ['multiple-choice', 'order', 'match', 'short-answer', 'explanatory-text']
qs_by_type = {
    k: [questions[i] for i in q_df.query(f"questionType == '{k}'").index] for k in question_types
}
# order_qs = [questions[i] for i in q_df.query("questionType == 'order'").index]

# %%

# question = questions[0]
question = qs_by_type["explanatory-text"][0]

extracted_questions = []
q_strs = []
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
                            print(f"found multiple-choice answer block of type: {block["type"]}")

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
            for blocks in it.chain([answer[k] for k in ["correctChoice", "matchOption"]]):
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
                        print(f"found short-answer answer block of type: {block["type"]}")

    q_text.extend([question[k] for k in ["hint", "feedback"]])

    q = {"text": q_text, "images": q_image}
    extracted_questions.append(q)
    q_strs.append("\n".join(q_text))


# %%
extracted_questions = oh.utils.extract_question_content(questions)
# %%
q_strs = ["\n".join(q["text"]) for q in extracted_questions]
# %%
extracted_questions
#%% 
# template to describe images
for question in extracted_questions:
    question["image-text"] = []
    for url in question["images"]:
        description = "description of image"
        # description = call_llm_to_describe_image(url)
        question["image-text"].append(description)


# %%
