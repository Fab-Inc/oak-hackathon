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
