# %%
import oakhack as oh
from oakhack.utils import load_embeddings
import numpy as np
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import seaborn as sns

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
beta = 0.75 # embeddign weighting
mix_q_klp = {}
for p in cos_q_klp.keys():
    mix_q_klp[p] = bm25_q_klp[p] + beta*cos_q_klp[p]

# %%
# based on a targe question, select KLPs related to the question in different ways
p = "biology-secondary-ks4-higher-ocr"
programme_questions = q_df.loc[q_df.programmeSlug == p]
q_select = 0  # index in programme questions

data_df = defaultdict(list)
for q_select in tqdm(range(len(programme_questions))):
    q = questions[programme_questions.iloc[q_select].name]
    q_lessonkey = f"{q['programmeSlug']}/{q['unitSlug']}/{q['lessonSlug']}"
    q_unit = q["unitSlug"]

    p_klp_df = klp_df.loc[(klp_df.programme == p)].copy().reset_index()
    # same lesson
    klp_samelesson_idx = p_klp_df.loc[
        (p_klp_df.lesson_key == q_lessonkey) # same lesson
    ].index.to_numpy()

    # same-unit but different lesson
    klp_sameunit_idx = p_klp_df.loc[
        (p_klp_df.lesson_key != q_lessonkey) # not same lesseon
        & (p_klp_df.unit == q_unit) # same unit
    ].index.to_numpy()

    # different unit
    klp_diffint_idx = p_klp_df.loc[
        (p_klp_df.unit != q_unit) # different unit
    ].index.to_numpy()

    sims = [bm25_q_klp[p], cos_q_klp[p], mix_q_klp[p]]
    data_df["questionId"].extend(9*[q["questionId"]])
        
    data_df["avg_sim"].extend([np.mean(x[:,klp_samelesson_idx]) for x in sims])
    data_df["measure"].extend(["bm25", "emb", "weighted"])
    data_df["klps"].extend(3*["same-lesson"])

    data_df["avg_sim"].extend([np.mean(x[:,klp_sameunit_idx]) for x in sims])
    data_df["measure"].extend(["bm25", "emb", "weighted"])
    data_df["klps"].extend(3*["same-unit"])

    data_df["avg_sim"].extend([np.mean(x[:,klp_diffint_idx]) for x in sims])
    data_df["measure"].extend(["bm25", "emb", "weighted"])
    data_df["klps"].extend(3*["different-unit"])


q_klp_mean_df = pd.DataFrame(data_df)

# %%
# visualise



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
