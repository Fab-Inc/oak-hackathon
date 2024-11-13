# %%
# Imports and function definitions
import oakhack as oh
from oakhack.embeddings import get_embeddings

from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from time import time
import random

load_dotenv(override=True)


def load_lessons():
    lessons, l_df = oh.utils.load_oak_lessons_with_df()
    flat_klp = oh.utils.extract_klp(lessons)
    return lessons, l_df, flat_klp


def get_klps_and_transcripts(lessons: list) -> dict:
    result = {}
    text_elements = []
    for lesson in lessons:
        transcript = lesson["transcriptSentences"]
        if transcript is None:
            continue

        if lesson["lessonTitle"] in result:
            continue

        klps = [klp["keyLearningPoint"] for klp in lesson["keyLearningPoints"]]
        text_elements.extend(klps)
        text_elements.extend(transcript)
        result[lesson["lessonTitle"]] = {
            "klps": len(klps),
            "transcript": len(transcript),
        }
    return result, text_elements


def get_embeddings_lesson(lesson_klps_transcripts: dict) -> dict:
    for lesson in lesson_klps_transcripts:
        klps = lesson_klps_transcripts[lesson]["klps"]
        transcript = lesson_klps_transcripts[lesson]["transcript"]
        klp_embeddings = get_embeddings(klps)
        transcript_embeddings = get_embeddings(transcript)
        lesson_klps_transcripts[lesson]["klp_embeddings"] = klp_embeddings
        lesson_klps_transcripts[lesson]["transcript_embeddings"] = transcript_embeddings


def get_similarities(lesson_klps_transcripts: dict):
    for lesson in lesson_klps_transcripts:
        similarities = cosine_similarity(
            lesson_klps_transcripts[lesson]["transcript"],
            lesson_klps_transcripts[lesson]["klps"],
        )
        lesson_klps_transcripts[lesson]["similarities"] = similarities


def assign_sentence_indices(similarities, threshold: float = 0.7):
    max_indices = np.argmax(similarities, axis=1)
    scores = similarities[np.arange(similarities.shape[0]), max_indices]
    has_assigned_index = scores > threshold
    final_assignments = np.where(has_assigned_index, max_indices, -1)
    return final_assignments


def assign_embeddings_to_lessons(
    lesson_klps_transcripts: dict, text_embeddings: list[float]
):
    starting_index = 0
    for key, value in lesson_klps_transcripts.items():
        num_klps = value["klps"]
        klp_index = starting_index + num_klps
        num_transcripts = value["transcript"]
        transcript_index = starting_index + num_klps + num_transcripts
        value["klps"] = text_embeddings[starting_index:klp_index]
        starting_index += num_klps
        value["transcript"] = text_embeddings[klp_index:transcript_index]
        lesson_klps_transcripts[key] = value


# %%
# Load in data.
s = time()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
lessons = lessons[0:2]
lesson_klps_transcripts, text_elements = get_klps_and_transcripts(lessons)
l = time()
# %%
# Process data
s = time()
text_emebeddings = get_embeddings(text_elements)
assign_embeddings_to_lessons(lesson_klps_transcripts, text_emebeddings)
m = time()

# %%
# Create a new dictionary from the sampled keys
get_similarities(lesson_klps_transcripts)
e = time()
embedding_time = m - s
load_time = e - s

# %%
# Classify transcripts
s = time()
for lesson in lesson_klps_transcripts:
    similarities = lesson_klps_transcripts[lesson]["similarities"]
    final_assignments = assign_sentence_indices(similarities)
    lesson_klps_transcripts[lesson]["assignments"] = final_assignments

e = time()
process_time = e - s

# %%
