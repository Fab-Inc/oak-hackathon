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
    mix_q_klp[p] = (1-beta)*bm25_q_klp[p] + beta*cos_q_klp[p]

# %%
# based on a targe question, select KLPs related to the question in different ways
p = "biology-secondary-ks4-higher-ocr"
# p = "biology-secondary-ks4-foundation-aqa"
p = "english-secondary-ks3"

q_klp_sim = {}
for p in tqdm(programmes.keys()):
# def calc_programme(p):
    programme_questions = q_df.loc[q_df.programmeSlug == p]
    q_select = 0  # index in programme questions

    # make it average of top-k?

    k = 5
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
        data_df["quizType"].extend(9*[q["quizType"]])
        data_df["keyStage"].extend(9*[q["keyStageSlug"]])
        data_df["subject"].extend(9*[q["subjectSlug"]])
        data_df["programme"].extend(9*[p])
        data_df["unit"].extend(9*[q["unitSlug"]])
            
        data_df["avg_sim"].extend([np.mean(x[q_select,klp_samelesson_idx]) for x in sims])
        # data_df["avg_sim"].extend([np.mean(np.sort(x[q_select, klp_samelesson_idx])[-k:]) for x in sims])
        data_df["measure"].extend(["bm25", "emb", "weighted"])
        data_df["klps"].extend(3*["same-lesson"])

        data_df["avg_sim"].extend([np.mean(x[q_select,klp_sameunit_idx]) for x in sims])
        # data_df["avg_sim"].extend([np.mean(np.sort(x[q_select,klp_sameunit_idx])[-k:]) for x in sims])
        data_df["measure"].extend(["bm25", "emb", "weighted"])
        data_df["klps"].extend(3*["same-unit"])

        data_df["avg_sim"].extend([np.mean(x[q_select,klp_diffint_idx]) for x in sims])
        # data_df["avg_sim"].extend([np.mean(np.sort(x[q_select,klp_diffint_idx])[-k:]) for x in sims])
        data_df["measure"].extend(["bm25", "emb", "weighted"])
        data_df["klps"].extend(3*["different-unit"])

    q_klp_mean_df = pd.DataFrame(data_df)
    q_klp_sim[p] = q_klp_mean_df 
    # return q_klp_mean_df

# from concurrent.futures import ProcessPoolExecutor
# with ProcessPoolExecutor(max_workers=5) as executor:
#     # Map the function to all items and process them in parallel
#     results = list(executor.map(calc_programme, programmes.keys()))

# q_klp_sim = {k: v for k,v in zip(programmes.keys(),results)}
all_res_df = pd.concat(q_klp_sim.values(),axis=0).reset_index()

#%%
# all_res_df = pd.read_csv(oh.DATA_DIR / 'q_to_klp_sim_stats.csv.gz')


#%%
plot_df = all_res_df.loc[all_res_df.measure=="weighted"]
g = sns.catplot(plot_df, x="klps", y="avg_sim",
            # col="measure",
            #col="keyStage",
            kind="boxen",
            dodge=True,
            hue="quizType",
            height=3,
            aspect=2
            )

g.figure.suptitle("Question-KLP similarity", fontsize=16, y=1.02)
g.ax.set_xlabel("KLP Relationship to Question", fontsize=12)
g.ax.set_ylabel("Avg Similarity", fontsize=12)
#%%
g = sns.catplot(plot_df, x="klps", y="avg_sim",
            # col="measure",
            col="keyStage", col_order=["ks1", "ks2", "ks3", "ks4"],col_wrap=2,
            # kind="bar",
            dodge=True,
            hue="quizType"
            )

g.figure.suptitle("Question-KLP similarity", fontsize=16, y=1.02)
xl = "KLP Relationship to Question"
g.axes[2].set_xlabel(xl, fontsize=12)  # Bottom left
g.axes[3].set_xlabel(xl, fontsize=12)  # Bottom right
#%%
g = sns.catplot(plot_df, x="klps", y="avg_sim",
            # col="measure",
            col="subject",col_wrap=2,
            kind="bar",
            hue="quizType"
            )

g.figure.suptitle("Question-KLP similarity", fontsize=16, y=1.02)
xl = "KLP Relationship to Question"
g.axes[-2].set_xlabel(xl, fontsize=12)  # Bottom left
g.axes[-1].set_xlabel(xl, fontsize=12)  # Bottom right
g.set_titles(template='{col_name}')


#%%
all_res_df.to_csv(oh.DATA_DIR / 'q_to_klp_sim_stats.csv.gz', index=False, compression='gzip')
# %%
# visualise

sns.catplot(data_df, x="klps", y="avg_sim", col="measure",
            # kind="bar",
            hue="quizType", dodge=True,
            )

sns.catplot(data_df, x="klps", y="avg_sim", col="measure",
            kind="bar",
            hue="quizType"
            )


# %%
q_idx = q_df.loc[q_df.programmeSlug == p].index.to_numpy()
q_same_lesson = q_df.loc[q_df.programmeSlug == p].index.to_numpy()
cos = cos_q_klp[p]

# %%
cos_q_klp = np.dot(q_embs, klp_embs.T)

# %%
q_idx = 0
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
# sample question
p = "biology-secondary-ks4-foundation-aqa"
q_idx = 0
k = 3
top_klp = [
    flat_klp_l[i]["keyLearningPoint"] for i in np.argsort(mix_q_klp[p][q_idx,:])[-(k+1):-1]
][::-1]
# %%
top_lesson = [klp_df.lesson.iloc[i] for i in np.argsort(mix_q_klp[p][q_idx,:])[-(k+1):-1]][::-1]

# %%
q_df.query()
# %%
