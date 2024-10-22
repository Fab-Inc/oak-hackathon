import oakhack as oh
import tiktoken
from oakhack.utils import load_oak_lessons, extract_klp
from oakhack.embeddings import BM25
from time import time
import json
from tqdm import tqdm
import numpy as np

keys = [
    'isLegacy', 'lessonSlug', 'lessonTitle', 
    'tierTitle', 'tierSlug', 'contentGuidance', 
    'misconceptionsAndCommonMistakes', 'teacherTips', 'lessonEquipmentAndResources', 
    'additionalMaterialUrl', 'keyLearningPoints', 'pupilLessonOutcome', 
    'lessonKeywords', 'copyrightContent', 'supervisionLevel', 
    'worksheetUrl', 'presentationUrl', 'videoMuxPlaybackId', 
    'videoWithSignLanguageMuxPlaybackId', 'transcriptSentences', 
    'isWorksheetLandscape', 'expired', 'starterQuiz', 
    'exitQuiz', 'videoTitle', 'lessonCohort', 
    'updatedAt', 'programmeSlug', 'unitSlug', 
    'unitTitle', 'keyStageSlug', 'keyStageTitle', 
    'subjectSlug', 'subjectTitle', 'yearTitle', 
    'examBoardTitle', 'downloads', 'pathways', 
    'examBoardSlug', 'subjectParent', 'unitStudyOrder', 
    'yearOrder', 'learningThemes'
]

# Re-associate scores to the original query strings
# then use printing/percentages to see whether the values are dragging all or just the important ones. 
# test within subject/within year/within unit/within lesson
# Try that non-linearity if things are a bit shitty. 
# maybe just use set operations, use indexes to retrieve the original strings. 
# form into a set.
# form KLPs into set. 
# subtract from each other, see how many leftovers there are.
# if it only removes a few then we are probably pretty good.

# Got to score fetching, just need to figure out the mapping it back and then set maths to see if everything makes sense.
# will require messing with the clamping, shame BM25 isn't bounded. 

def process_lesson_data(lesson_data):
    starter_questions = lesson_data["starterQuiz"]
    exit_questions = lesson_data["exitQuiz"]
    if starter_questions is not None:
        starter_questions = oh.utils.extract_question_content(starter_questions)
    else:
        starter_questions = []
    if exit_questions is not None:
        exit_questions = oh.utils.extract_question_content(exit_questions)
    else:
        exit_questions = []
    starter_questions = ['\n'.join(q['text']) for q in starter_questions] 
    exit_questions = ['\n'.join(q['text']) for q in exit_questions] 
    klps = [klp["keyLearningPoint"] for klp in lesson_data["keyLearningPoints"]]
    return {
        "klps" : klps,
        "questions": starter_questions + exit_questions
    }    

def construct_name(year, unit, unit_order):
    return f"{year}_{unit}_{unit_order}"

def process_sciences(result, lesson_data, exam_board, subject, year, unit, unit_order):
    core_sciences = ["Physics", "Biology", "Chemistry", "Combined science"]
    exam_boards = ["None", "Edexcel", "Eduqas", "AQA", "OCR"]
    if subject == "Science":
        for science in core_sciences:
            for exam_board in exam_boards:
                if exam_board not in result[science]:
                    result[science][exam_board] = {}
                result[science][exam_board][construct_name(year, unit, unit_order)] = process_lesson_data(lesson_data)
    else:
        if exam_board not in result[subject]:
            result[subject][exam_board] = {}
        result[subject][exam_board][construct_name(year, unit, unit_order)] = process_lesson_data(lesson_data)

def process_other(result, lesson_data, exam_board, subject, year, unit, unit_order):
    if exam_board not in result[subject]:
        result[subject][exam_board] = {}
    result[subject][construct_name(year, unit, unit_order)] = process_lesson_data(lesson_data)

def separate_lessons():
    result = {}
    lessons = load_oak_lessons()
    subjects = set(l["subjectTitle"] for l in lessons)
    for subject in subjects:
        result[subject] = {}

    for lesson in lessons:
        exam_board = lesson["examBoardTitle"]
        subject = lesson["subjectTitle"]
        subject_parent = lesson["subjectParent"]
        year = lesson["yearOrder"]
        unit = lesson["unitTitle"]
        unit_order = lesson["unitStudyOrder"]

        if subject_parent == "Science" or subject == "Science":
            process_sciences(result, lesson, exam_board, subject, year, unit, unit_order)

        else:
            process_other(result, lesson, exam_board, subject, year, unit, unit_order)

    return result

programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
questions, q_df = oh.utils.extract_questions(lessons)
extracted_questions = oh.utils.extract_question_content(questions)
flat_klp = oh.utils.extract_klp(lessons)
flat_klp_l, klp_df = oh.utils.extract_klp_with_df(flat_klp)
flat_klp_l = [f_klp_l["keyLearningPoint"] for f_klp_l in flat_klp_l]
flat_klp_l = np.array(flat_klp_l)

q_strs = np.array(['\n'.join(q['text']) for q in extracted_questions] )

bm25_q_klp = {}
encoding = tiktoken.encoding_for_model("text-embedding-3-large")
training_set_unencoded = np.concatenate((flat_klp_l, q_strs)).tolist()
training_set = encoding.encode_batch(training_set_unencoded)
bm25 = BM25(training_set)

for p in tqdm(list(programmes)):
    klp_idx = klp_df.loc[klp_df.programme == p].index.to_numpy()
    q_idx = q_df.loc[q_df.programmeSlug == p].index.to_numpy()
    question_strings_unencoded = q_strs[q_idx]
    question_strings = encoding.encode_batch(question_strings_unencoded)
    score_array = []
    for question_string in question_strings:
        scores = bm25.get_scores(question_string, docindex=klp_idx)
        ss_max = scores.max()
        ss_min = scores.min()
        normed_scores = (scores - ss_min) / (ss_max - ss_min)
        score_array.append(normed_scores)
    bm25_q_klp[p] = np.array(score_array)

np.savez("./data/similarity/bm25-q-klp-by-programme", bm25_q_klp, allow_pickle=True)
