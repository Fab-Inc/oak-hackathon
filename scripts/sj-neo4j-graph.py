# %%
import os
import numpy as np
import json
import itertools as it
from neo4j import GraphDatabase
import neo4j
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(override=True)
URI = os.getenv("URI")
USER = os.getenv("USER")
PASS = os.getenv("PASS")

import oakhack as oh


def get_data_for_adjacency_matrix():
    lessons, _ = oh.utils.load_oak_lessons_with_df()
    flat_klp = oh.utils.extract_klp(lessons)
    klp_bm25 = oh.embeddings.get_klp_BM25(flat_klp)
    klp_bm25 = klp_bm25 / klp_bm25.max(axis=1)
    klp_embs = oh.load_embeddings("klp_embeddings_batch_size3000_*.npy").astype(float)
    return flat_klp, klp_bm25, klp_embs


def filter_klps_by_programme(programme: str, flat_klp, klp_bm25, klp_embs):
    klp_programme_index = [
        i for (i, key) in enumerate(flat_klp) if key.split("/")[0] == programme
    ]
    klppi_ix = np.ix_(klp_programme_index, klp_programme_index)

    klp_bm25_programme = klp_bm25[klppi_ix]

    klp_embs_programme = klp_embs[klp_programme_index]
    klp_embs_programme = klp_embs_programme @ klp_embs_programme.T

    flat_klp_programme = {
        key: klp
        for i, (key, klp) in enumerate(flat_klp.items())
        if i in klp_programme_index
    }

    flat_klp_programme_list = list(flat_klp_programme.values())

    return (
        klp_bm25_programme,
        klp_embs_programme,
        flat_klp_programme,
        flat_klp_programme_list,
    )


def pairwise_label_klp_combinations(flat_klp_programme: dict):
    year_order = np.array([klp["yearOrder"] for klp in flat_klp_programme.values()])
    unit_study_order = np.array(
        [klp["unitStudyOrder"] for klp in flat_klp_programme.values()]
    )
    order_in_unit = np.array(
        [klp["orderInUnit"] for klp in flat_klp_programme.values()]
    )

    earlier = (
        (year_order[:, None] < year_order[None])
        | (
            (year_order[:, None] == year_order[None])
            & (unit_study_order[:, None] < unit_study_order[None])
        )
        | (
            (year_order[:, None] == year_order[None])
            & (unit_study_order[:, None] == unit_study_order[None])
            & (order_in_unit[:, None] < order_in_unit[None])
        )
    )
    return earlier


def mask_adjacency_matrix(klp_bm25_programme, klp_embs_programme, earlier):

    klp_bm25_masked = klp_bm25_programme * earlier
    np.fill_diagonal(klp_bm25_masked, 0)

    klp_embs_masked = klp_embs_programme * earlier
    np.fill_diagonal(klp_embs_masked, 0)
    return klp_bm25_masked, klp_embs_masked


def get_similarity_adjacency_matrix_for_programme(
    programme: str, flat_klp, klp_bm25, klp_embs
):
    # Matrix, klp x klp
    (
        klp_bm25_programme,
        klp_embs_programme,
        flat_klp_programme,
        flat_klp_programme_list,
    ) = filter_klps_by_programme(programme, flat_klp, klp_bm25, klp_embs)
    earlier = pairwise_label_klp_combinations(flat_klp_programme)
    klp_bm25_masked, klp_embs_masked = mask_adjacency_matrix(
        klp_bm25_programme, klp_embs_programme, earlier
    )
    cutoff = 0.4
    embwt = 0.8
    klp_adj = klp_bm25_masked * (1 - embwt) + klp_embs_masked * embwt
    klp_adj = np.minimum(klp_adj * (klp_adj > cutoff), 1)

    return klp_adj, flat_klp_programme_list


def remove_excess_data(json_data: dict) -> dict:
    """Removes the excess json elements from the oak scrape.

    Args:
        json_data (dict): Raw json data pulled from the oak scrape.

    Returns:
        dict: Processed json data containing only sections with data we are going to pull from.
    """
    return json_data["props"]["pageProps"]["curriculumData"]


def process_lesson(page_data: dict) -> dict:
    """Filters data from lesson json to contain only 'useful' keys.

    Args:
        page_data (dict): Json data pulled from Oak scrape

    Returns:
        dict: Filtered json data containing only the main keys for inclusion in the lesson graph.
    """

    lesson_title = page_data["lessonTitle"]
    tier_title = page_data["tierTitle"]
    content_guidance = (
        page_data["contentGuidance"] if page_data["contentGuidance"] is not None else []
    )
    if len(content_guidance) > 0:
        content_guidance = [cg["contentGuidanceLabel"] for cg in content_guidance]
    misconceptions_responses = [
        (m["misconception"], m["response"])
        for m in page_data["misconceptionsAndCommonMistakes"]
    ]
    misconceptions, responses = zip(*misconceptions_responses)
    tips = [t["teacherTip"] for t in page_data.get("teacherTips", []) or []]
    lesson_outcome = page_data["pupilLessonOutcome"]
    key_words = [k["keyword"] for k in page_data["lessonKeywords"]]
    key_stage = int(page_data["keyStageTitle"].split(" ")[-1])
    subject = page_data["subjectTitle"]
    year = int(page_data["yearTitle"].split(" ")[-1])
    exam_board = page_data["examBoardTitle"]
    unit = page_data["unitTitle"]

    lesson = {
        "lesson_title": lesson_title,
        "lesson_outcome": lesson_outcome,
        "key_words": key_words,
        "content_guidance": content_guidance,
        "tips": tips,
        "misconceptions": misconceptions,
        "responses": responses,
        "exam_board": exam_board,
        "key_stage": key_stage,
        "tier": tier_title,
        "year": year,
        "subject": subject,
        "unit": unit,
    }

    return lesson


def process_klps(page_data: dict) -> list[str]:
    """Isolates only the klps from a lessons page data.

    Returns:
        list[str]: list of key learning points.
    """
    klps = [klp["keyLearningPoint"] for klp in page_data["keyLearningPoints"]]
    return klps


def process_transcript(page_data: dict) -> list[str]:
    """Isolates only the transcripts from a lessons page data.

    Returns:
        list[str]: list of sentences from the lesson's transcript.
    """
    transcript_lines = page_data["transcriptSentences"]
    return transcript_lines


def process_question(question: dict) -> str:
    """Isolates and processes the a question from a given quiz from a lesson.

    Args:
        question (dict): A single question from the lesson's quizzes.

    Returns:
        str: The key points of interest from the question stored as a string separated by \n
    """
    q_text = []
    for block in question["questionStem"]:
        if block["type"] == "text":
            q_text.append(block["text"])

    if question["questionType"] == "multiple-choice":
        if question["answers"] is not None:
            for answer in question["answers"]["multiple-choice"]:
                # only keep correct answer options
                if answer["answerIsCorrect"]:
                    for block in answer["answer"]:
                        if block["type"] == "text":
                            q_text.append(block["text"])

    elif question["questionType"] == "order":
        for answer in question["answers"]["order"]:
            # add all answer options (ignore order)
            for block in answer["answer"]:
                if block["type"] == "text":
                    q_text.append(block["text"])

    elif question["questionType"] == "match":
        for answer in question["answers"]["match"]:
            # add all answer stems and match words
            for blocks in it.chain(
                [answer[k] for k in ["correctChoice", "matchOption"]]
            ):
                for block in blocks:
                    if block["type"] == "text":
                        q_text.append(block["text"])

    elif question["questionType"] == "short-answer":
        if question["answers"] is not None:
            for answer in question["answers"]["short-answer"]:
                for block in answer["answer"]:
                    if block["type"] == "text":
                        q_text.append(block["text"])

    q_text.extend([question[k] for k in ["hint", "feedback"]])

    q = "\n".join([t for t in q_text if t])

    return q


def get_basic_merge_query(labels: str, properties: dict) -> str:
    properties = {k: v for k, v in properties.items() if v is not None}
    properties_string = "{" + ", ".join(f"{key}:${key}" for key in properties) + "}"
    return f"MERGE ({labels} {properties_string})"


def get_unit_information(programme: str):
    with open(f"../data/oak_scraped_json/{programme}/units.json", "rb") as f:
        unit_meta_data = json.load(f)
        unit_meta_data = unit_meta_data["props"]["pageProps"]["curriculumData"]

    units = [(u[0]["title"], u[0]["slug"]) for u in unit_meta_data["units"]]
    return units


def get_lesson_names(programme: str, units):
    lesson_file_names = {}

    for title, slug in units:
        try:
            with open(
                f"../data/oak_scraped_json/{programme}/{slug}/lessons.json",
                "rb",
            ) as f:
                lesson_meta_data = json.load(f)
                lesson_meta_data = lesson_meta_data["props"]["pageProps"][
                    "curriculumData"
                ]
            file_names = [
                f'{l["lessonSlug"]}.json' for l in lesson_meta_data["lessons"]
            ]
            lesson_file_names[title] = {"lessons": file_names, "slug": slug}
        except:
            pass
    return lesson_file_names


def get_lesson_data_for_unit(programme: str, lesson_file_names: dict):

    lessons_by_unit = []
    lesson_queries_by_unit = []
    klps_by_unit = []
    starter_quizzes_by_unit = []
    exit_quizzes_by_unit = []
    transcripts_by_unit = []

    for unit_info in lesson_file_names.values():
        lesson_queries = []
        lessons = []
        klpses = []
        starter_quizzes = []
        exit_quizzes = []
        transcripts = []
        lesson_names = unit_info["lessons"]
        slug = unit_info["slug"]
        for file in lesson_names:
            with open(
                f"../data/oak_scraped_json/{programme}/{slug}/{file}",
                "rb",
            ) as f:
                data = json.load(f)
                lesson_data = remove_excess_data(data)
                lesson = process_lesson(lesson_data)
                klps = process_klps(lesson_data)
                transcript_sentences = process_transcript(lesson_data)

                starter_quiz_section = lesson_data.get("starterQuiz", []) or []
                exit_quiz_section = lesson_data.get("exitQuiz", []) or []
                starter_quiz = [process_question(q) for q in starter_quiz_section]
                exit_quiz = [process_question(q) for q in exit_quiz_section]
                lesson_query = get_basic_merge_query(":Lesson", lesson)
                lesson_queries.append(lesson_query)
                lessons.append(lesson)
                klpses.append(klps)
                starter_quizzes.append(starter_quiz)
                exit_quizzes.append(exit_quiz)
                transcripts.append(transcript_sentences)
        lesson_queries_by_unit.append(lesson_queries)
        lessons_by_unit.append(lessons)
        klps_by_unit.append(klpses)
        starter_quizzes_by_unit.append(starter_quizzes)
        exit_quizzes_by_unit.append(exit_quizzes)
        transcripts_by_unit.append(transcripts)
    return (
        lesson_queries_by_unit,
        lessons_by_unit,
        klps_by_unit,
        starter_quizzes_by_unit,
        exit_quizzes_by_unit,
        transcripts_by_unit,
    )


def clear_graph_db():
    with GraphDatabase.driver(URI, auth=(USER, PASS)) as driver:
        driver.verify_connectivity()
        driver.execute_query("MATCH (n) DETACH DELETE n")


def insert_oak_data_into_db(
    lesson_queries_by_unit,
    lessons_by_unit,
    klps_by_unit,
    starter_quizzes_by_unit,
    exit_quizzes_by_unit,
    transcripts_by_unit,
):
    with GraphDatabase.driver(URI, auth=(USER, PASS)) as driver:
        driver.verify_connectivity()
        for unit_idx, unit in enumerate(lesson_queries_by_unit):
            with driver.session() as session:
                for lesson_idx, lesson_query in enumerate(unit):
                    current_lesson_title = lessons_by_unit[unit_idx][lesson_idx][
                        "lesson_title"
                    ]

                    # Start a new transaction for each lesson
                    with session.begin_transaction() as tx:
                        # Execute the lesson query
                        tx.run(lesson_query, **lessons_by_unit[unit_idx][lesson_idx])

                        # Insert Key Learning Points
                        for klp in klps_by_unit[unit_idx][lesson_idx]:
                            tx.run(
                                "MERGE (n:KeyLearningPoint {key_learning_point: $key_learning_point})",
                                key_learning_point=klp,
                            )

                        # Add klp and lesson relationships
                        for klp in klps_by_unit[unit_idx][lesson_idx]:
                            tx.run(
                                "MATCH (l:Lesson {lesson_title:$lesson_title}), (klp:KeyLearningPoint {key_learning_point: $key_learning_point}) "
                                "MERGE (klp)-[r:BELONGS_TO]->(l)",
                                key_learning_point=klp,
                                lesson_title=current_lesson_title,
                            )

                        # Insert Starter Questions
                        for question in starter_quizzes_by_unit[unit_idx][lesson_idx]:
                            tx.run(
                                "MERGE (q:Question {question:$question})",
                                question=question,
                            )
                            tx.run(
                                "MATCH (l:Lesson {lesson_title:$lesson_title}), (q:Question {question: $question}) "
                                "MERGE (q)-[r:STARTER_QUESTION]->(l)",
                                lesson_title=current_lesson_title,
                                question=question,
                            )

                        # Insert Exit Questions
                        for question in exit_quizzes_by_unit[unit_idx][lesson_idx]:
                            tx.run(
                                "MERGE (q:Question {question:$question})",
                                question=question,
                            )
                            tx.run(
                                "MATCH (l:Lesson {lesson_title:$lesson_title}), (q:Question {question: $question}) "
                                "MERGE (q)-[r:EXIT_QUESTION]->(l)",
                                lesson_title=current_lesson_title,
                                question=question,
                            )

                        # Insert transcript
                        if transcripts_by_unit[unit_idx][lesson_idx] is not None:
                            tx.run(
                                "MERGE (t:Transcript {transcript:$transcript})",
                                transcript=transcripts_by_unit[unit_idx][lesson_idx],
                            )
                            tx.run(
                                "MATCH (l:Lesson {lesson_title:$lesson_title}), (t:Transcript {transcript:$transcript}) "
                                "MERGE (t)-[:BELONGS_TO]->(l)",
                                lesson_title=current_lesson_title,
                                transcript=transcripts_by_unit[unit_idx][lesson_idx],
                            )

                        # Handle previous lesson relationships
                        if lesson_idx != 0:
                            previous_lesson_title = lessons_by_unit[unit_idx][
                                lesson_idx - 1
                            ]["lesson_title"]
                            tx.run(
                                "MATCH (l1:Lesson {lesson_title:$current_lesson_title}), (l2:Lesson {lesson_title: $previous_lesson_title}) "
                                "MERGE (l2)-[r:PRECEDED_BY]->(l1)",
                                current_lesson_title=current_lesson_title,
                                previous_lesson_title=previous_lesson_title,
                            )
                    with session.begin_transaction() as tx:
                        # After processing the lesson, you can add the Unit relationships
                        tx.run(
                            "MERGE (:Unit {unit:$unit})",
                            unit=lessons_by_unit[unit_idx][lesson_idx]["unit"],
                        )
                        tx.run(
                            "MATCH (l:Lesson {lesson_title:$lesson_title}), (u:Unit {unit:$unit}) "
                            "MERGE (l)-[:BELONGS_TO]->(u)",
                            lesson_title=current_lesson_title,
                            unit=lessons_by_unit[unit_idx][lesson_idx]["unit"],
                        )


def insert_unit_relationships(lesson_queries_by_unit, lessons_by_unit):
    with GraphDatabase.driver(URI, auth=(USER, PASS)) as driver:
        driver.verify_connectivity()
        for unit_idx, unit in enumerate(lesson_queries_by_unit):
            if unit_idx == 0:
                continue
            for lesson_idx, _ in enumerate(unit):
                current_unit = lessons_by_unit[unit_idx][lesson_idx]["unit"]
                previous_unit = lessons_by_unit[unit_idx - 1][lesson_idx]["unit"]
                driver.execute_query(
                    "MATCH (u1:Unit {unit:$unit1}), (u2:Unit {unit:$unit2}) MERGE (u2)-[:PRECEDED_BY]->(u1)",
                    unit1=previous_unit,
                    unit2=current_unit,
                )
                break


def insert_adjacency_relationships(klp_adj, flat_klp_programme_list):
    existing_relationships = set()
    batch_size = 1000

    with GraphDatabase.driver(URI, auth=(USER, PASS)) as driver:
        with driver.session() as session:
            for x_idx in range(len(klp_adj)):
                with (
                    session.begin_transaction() as tx
                ):  # Start a new transaction for each outer loop
                    for y_idx in range(len(klp_adj)):
                        if y_idx == x_idx:
                            continue
                        if klp_adj[x_idx][y_idx] == 0:
                            continue
                        if (
                            flat_klp_programme_list[x_idx]["keyLearningPoint"]
                            == flat_klp_programme_list[y_idx]["keyLearningPoint"]
                        ):
                            continue

                        relationship_key = f"{flat_klp_programme_list[x_idx]['keyLearningPoint']}_{flat_klp_programme_list[y_idx]['keyLearningPoint']}"
                        if relationship_key not in existing_relationships:
                            existing_relationships.add(relationship_key)
                            tx.run(
                                """
                                MATCH (klp:KeyLearningPoint {key_learning_point:$klp1}), (klp2:KeyLearningPoint {key_learning_point:$klp2})
                                MERGE (klp)-[:RELATED_TO {similarity:$similarity}]->(klp2)
                                """,
                                klp1=flat_klp_programme_list[x_idx]["keyLearningPoint"],
                                klp2=flat_klp_programme_list[y_idx]["keyLearningPoint"],
                                similarity=klp_adj[x_idx][y_idx],
                            )

                        # Commit the transaction if batch size is reached
                        if (y_idx + 1) % batch_size == 0:
                            tx.commit()  # Commit current transaction
                            tx = session.begin_transaction()  # Start a new transaction

                    # Commit any remaining operations after inner loop completes
                    tx.commit()


# %%
# Get klp data
flat_klp, klp_bm25, klp_embs = get_data_for_adjacency_matrix()

# %%
# Load programme names
programmes = os.listdir(f"../data/oak_scraped_json/")


# %%
# Clear db contents
clear_graph_db()

# %%
# Process data by programme
for programme in tqdm(programmes, "Inserting data into neo4j"):
    klp_adjacency, flat_klp_programme_list = (
        get_similarity_adjacency_matrix_for_programme(
            programme, flat_klp, klp_bm25, klp_embs
        )
    )
    units = get_unit_information(programme)
    lesson_file_names = get_lesson_names(programme, units)
    (
        lesson_queries_by_unit,
        lessons_by_unit,
        klps_by_unit,
        starter_quizzes_by_unit,
        exit_quizzes_by_unit,
        transcripts_by_unit,
    ) = get_lesson_data_for_unit(programme, lesson_file_names)
    insert_oak_data_into_db(
        lesson_queries_by_unit,
        lessons_by_unit,
        klps_by_unit,
        starter_quizzes_by_unit,
        exit_quizzes_by_unit,
        transcripts_by_unit,
    )
    insert_unit_relationships(lesson_queries_by_unit, lessons_by_unit)
    insert_adjacency_relationships(klp_adjacency, flat_klp_programme_list)
