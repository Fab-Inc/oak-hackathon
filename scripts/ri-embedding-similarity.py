# %%
import oakhack as oh
from oakhack.utils import load_embeddings
import numpy as np
from pathlib import Path

#%%
programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
questions, q_df = oh.utils.extract_questions(lessons)
extracted_questions = oh.utils.extract_question_content(questions)

#%%
flat_klp = oh.utils.extract_klp(lessons)
flat_klp_l = []
for k,v in flat_klp.items():
    flat_klp_l.append({"klp_key":k, **v})

#%% 
# build klp_df index 
# %%
klp_embs = load_embeddings("klp_embeddings_batch_size3000_*.npy")
q_embs = load_embeddings("question_embeddings_batch_size3000_*.npy")

# %%
# slow!!
#cos_q_klp = np.dot(q_embs,klp_embs.T)

# %%
q_idx = 0
q_klp_cos = np.dot(q_embs[q_idx,:], klp_embs.T)
# %%
top_klp = [flat_klp_l[i]['keyLearningPoint'] for i in np.argsort(q_klp_cos)[-100:-1]][::-1]

# %%
top_klp = [flat_klp_l[i]['klp_key'] for i in np.argsort(q_klp_cos)[-100:-1]][::-1]
# %%
