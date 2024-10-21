# %%
import oakhack as oh
import zipfile as zf
import itertools as it

from oakhack import DATA_DIR

mbsse_lp_file = DATA_DIR / "mbsse_lp" / "mbsseKP_files_lessonplans_parsed.json.gz"
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
import os
api_key = os.getenv("OPENAI_API_KEY")

def prompt_from_question(question):
    prompt = ""
    prompt += "The image is a visual aid for the following question:\n\n"
    question_text = "\n".join(question["text"])
    task_text = """Please describe these images for an alt-text to enable a LLM model to
        understand what is shown in the image. The description should be less than 20
        words per image."""
    prompt += f"{question_text}\n\n{task_text}"
    return prompt
    


import requests

def describe_image(image_url, prompt, api_key=api_key, model='gpt-4o-2024-08-06'):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],
        "max_tokens": 16384
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    else:
        print(f"Error processing {image_url}: {response.status_code} {response.text}")
        return ""

import json
outpath = DATA_DIR / "question_json"
outpath.mkdir(exist_ok=True)
# template to describe images
qid = 0
for question in extracted_questions:
    question["image-text"] = []
    prompt = prompt_from_question(question)
    for url in question["images"]:
        
        description = describe_image(url,prompt)
        # description = call_llm_to_describe_image(url)
        question["image-text"].append(description)
    with open(outpath / f"question_{qid}.json", "w") as f:
        json.dump(question, f)
    qid += 1

# %%

