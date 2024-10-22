import oakhack as oh
import tiktoken
from oakhack.utils import load_oak_lessons, extract_klp
from oakhack.embeddings import BM25
from time import time
import json

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

s = time()
lessons = load_oak_lessons()
flat_klp = extract_klp(lessons)
klps = [klp["keyLearningPoint"] for klp in flat_klp.values()]

programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
questions, q_df = oh.utils.extract_questions(lessons)
extracted_questions = oh.utils.extract_question_content(questions)
q_strs = ['\n'.join(q['text']) for q in extracted_questions] 

encoding = tiktoken.encoding_for_model("text-embedding-3-large")
encoded_questions = encoding.encode_batch(q_strs)
encoded_klps = encoding.encode_batch(klps)
all_encodings = []
all_encodings.extend(encoded_questions)
all_encodings.extend(encoded_klps)
bm25 = BM25(all_encodings)
print("Beginning scoring")
separated_lessons = separate_lessons()
for subject, lessons in separated_lessons.items():
    subject_klps = []
    for lesson in lessons.values():
        subject_klps.extend(lesson.get("klps", []))
        questions = lesson.get("questions", [])
        
        if len(questions) > 0:
            encoded_questions = encoding.encode_batch(questions)
            print(lesson.get("klps", []))
            for question in questions:
                scores = bm25.get_scores_index_slice(question, index_lower=len(encoded_questions))
                break
        break
    break

print("---"*12)
e = time()
print(e - s)