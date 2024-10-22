#%%
import oakhack as oh
import numpy as np
import scipy as sp
import networkx as nx

#%%
lessons, l_df = oh.utils.load_oak_lessons_with_df()
flat_klp = oh.utils.extract_klp(lessons)
#%%
klpA = oh.embeddings.get_klp_BM25(flat_klp)
#%%
spA = sp.sparse.csr_array(klpA)
# %%
G = nx.from_numpy_array(klpA)
# %%
G = nx.from_scipy_sparse_array(spA)

# %%
# get lesson info from a klp
key = 'biology-secondary-ks4-foundation-aqa/eukaryotic-and-prokaryotic-cells/cells/0'
*lesson_key, klp_idx = key.split('/')
lesson_key = "/".join(lesson_key)
lesson = lessons[l_df[l_df.lessonKey == lesson_key].index]
# %%
