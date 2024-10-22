# %%
import oakhack as oh
from oakhack.utils import load_embeddings
import numpy as np
import pandas as pd

#%%
programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
questions, q_df = oh.utils.extract_questions(lessons)
extracted_questions = oh.utils.extract_question_content(questions)
flat_klp = oh.utils.extract_klp(lessons)
flat_klp_l, klp_df = oh.utils.extract_klp_with_df(flat_klp)

# %%
klp_embs = load_embeddings("klp_embeddings_batch_size3000_*.npy")
q_embs = load_embeddings("question_embeddings_batch_size3000_*.npy")

# %%
# questions to klps within programmes
cos_q_klp = {}
for p in list(programmes):
    klp_idx = klp_df.loc[klp_df.programme == p].index.to_numpy()
    q_idx = q_df.loc[q_df.programmeSlug == p].index.to_numpy()
    cos_q_klp[p] = np.dot(q_embs[q_idx,:], klp_embs[klp_idx,:].T)




#%%
cos_q_klp = np.dot(q_embs,klp_embs.T)

# %%
q_idx = 6
q_klp_cos = np.dot(q_embs[q_idx,:], klp_embs.T)
# %%
idx = klp_df.loc[klp_df.programme == 'biology-secondary-ks4-foundation-aqa'].index.to_numpy()
top_klp = [flat_klp_l[i]['keyLearningPoint'] for i in np.argsort(q_klp_cos[idx])[-100:-1]][::-1]

# %%
# top_klp = [flat_klp_l[i]['lesson'] for i in np.argsort(q_klp_cos[idx])[-100:-1]][::-1]
top_klp = [klp_df.lesson.iloc[i] for i in np.argsort(q_klp_cos[idx])[-100:-1]][::-1]
# %%

