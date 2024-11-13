# %%
# Imports and function definitions
import oakhack as oh
from scipy.stats import mode
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


def get_klps_and_transcripts(lessons: list, window_size: int = 1) -> dict:
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
        if window_size > 1:
            original_num_transcript_sentences = len(transcript)
            transcript = sliding_window(transcript, window_size)
            text_elements.extend(transcript)
        else:
            text_elements.extend(transcript)

        num_transcript_sentences = len(transcript)

        if window_size > 1:
            result[lesson["lessonTitle"]] = {
                "klps": len(klps),
                "transcript": num_transcript_sentences,
                "original_num_transcript_sentences": original_num_transcript_sentences,
            }
        else:
            result[lesson["lessonTitle"]] = {
                "klps": len(klps),
                "transcript": num_transcript_sentences,
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


def sliding_window(lst: list, window_size: int = 1):
    result = []
    for i in range(len(lst)):
        result.append(" ".join(lst[i : i + window_size]))
    return result


def count_votes(lesson: dict, final_assignments: np.ndarray, window_size: int):
    original_num_sentences = lesson["original_num_transcript_sentences"]
    votes = [[] for _ in range(original_num_sentences)]

    for idx in range(original_num_sentences):
        if idx == len(final_assignments):
            break
        for i in range(window_size):
            if (idx + i) <= len(final_assignments) - 1:
                votes[idx + i].append(final_assignments[idx + i])
        votes[idx] = mode(votes[idx]).mode

    votes = np.array(votes)
    return votes


# %%
# Load in data.
window_size = 3
s = time()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
lessons = lessons[0:10]
l = time()

# %%
# Process data
s = time()
lesson_klps_transcripts, text_elements = get_klps_and_transcripts(
    lessons, window_size=window_size
)
p = time()

# %%
# Get embeddings
s = time()
text_embeddings = get_embeddings(text_elements)
assign_embeddings_to_lessons(lesson_klps_transcripts, text_embeddings)
e = time()

# %%
# Create a new dictionary from the sampled keys
get_similarities(lesson_klps_transcripts)

# %%
# Classify transcripts
s = time()
for lesson in lesson_klps_transcripts:
    similarities = lesson_klps_transcripts[lesson]["similarities"]
    final_assignments = assign_sentence_indices(similarities)
    if window_size > 1:
        final_assignments = count_votes(
            lesson_klps_transcripts[lesson], final_assignments, window_size
        )
    lesson_klps_transcripts[lesson]["assignments"] = final_assignments
    break

e = time()
process_time = e - s

# %%
# Apply window
