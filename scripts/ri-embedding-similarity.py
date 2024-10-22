# %%
import oakhack as oh
from oakhack.utils import load_embeddings
import numpy as np
import pandas as pd

# %%
programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
#%%
questions, q_df = oh.utils.extract_questions(lessons)
extracted_questions = oh.utils.extract_question_content(questions)
flat_klp = oh.utils.extract_klp(lessons)
flat_klp_l, klp_df = oh.utils.extract_klp_with_df(flat_klp)

# %%
klp_embs = load_embeddings("klp_embeddings_batch_size3000_*.npy")
q_embs = load_embeddings("question_embeddings_batch_size3000_*.npy")

# questions to klps within programmes
cos_q_klp = {}
for p in list(programmes):
    klp_idx = klp_df.loc[klp_df.programme == p].index.to_numpy()
    q_idx = q_df.loc[q_df.programmeSlug == p].index.to_numpy()
    cos_q_klp[p] = np.dot(q_embs[q_idx, :], klp_embs[klp_idx, :].T)

# %%
with open(oh.DATA_DIR / "similarity/bm25-q-klp-by-programme.npz", "rb")  as f:
    d = np.load(f,allow_pickle=True)
    bm25_q_klp = d['arr_0'].item()

# %%
# based on a targe question, select KLPs related to the question in different ways
p = "biology-secondary-ks4-foundation-aqa"
programme_questions = q_df.loc[q_df.programmeSlug == p]
q_select = 0  # index in programme questions

for q in range(len(programme_questions)):
    q = questions[programme_questions.iloc[q_select].name]
    q_lessonkey = f"{q['programmeSlug']}/{q['unitSlug']}/{q['lessonSlug']}"
    q_unit = q["unitSlug"]

    # same lesson
    klp_samelesson_idx = klp_df.loc[
        (klp_df.programme == p) # same programmes
        & (klp_df.lesson_key == q_lessonkey) # same lesson
    ].index.to_numpy()

    # same-unit but different lesson
    klp_sameunit_idx = klp_df.loc[
        (klp_df.programme == p) # within program
        & (klp_df.lesson_key != q_lessonkey) # not same lesseon
        & (klp_df.unit == q_unit) # same unit
    ].index.to_numpy()

    # different unit
    klp_diffint_idx = klp_df.loc[
        (klp_df.programme == p) # same programme
        & (klp_df.unit != q_unit) # different unit
    ].index.to_numpy()

    # mean cos 
    # mean bm
    # mean bm + 0.8 * cos 

# %%
q_idx = q_df.loc[q_df.programmeSlug == p].index.to_numpy()
q_same_lesson = q_df.loc[q_df.programmeSlug == p].index.to_numpy()
cos = cos_q_klp[p]


# %%
cos_q_klp = np.dot(q_embs, klp_embs.T)

# %%
q_idx = 6
q_klp_cos = np.dot(q_embs[q_idx, :], klp_embs.T)
# %%
idx = klp_df.loc[
    klp_df.programme == "biology-secondary-ks4-foundation-aqa"
].index.to_numpy()
top_klp = [
    flat_klp_l[i]["keyLearningPoint"] for i in np.argsort(q_klp_cos[idx])[-100:-1]
][::-1]

# %%
# top_klp = [flat_klp_l[i]['lesson'] for i in np.argsort(q_klp_cos[idx])[-100:-1]][::-1]
top_klp = [klp_df.lesson.iloc[i] for i in np.argsort(q_klp_cos[idx])[-100:-1]][::-1]
# %%
