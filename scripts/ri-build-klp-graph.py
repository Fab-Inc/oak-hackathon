# %%
from itertools import product

import numpy as np
import scipy as sp
import networkx as nx
from tqdm import tqdm

import oakhack as oh

# %%
lessons, l_df = oh.utils.load_oak_lessons_with_df()
flat_klp = oh.utils.extract_klp(lessons)
# %%
klpA = oh.embeddings.get_klp_BM25(flat_klp)

# %%
"""
Label each klp pairwise combination (klp1 x klp2) as one of:
    -1: klp1 is earlier than klp2
    0: klp1 is equal to klp2
    1: klp1 is later than klp2
"""
nklp = len(flat_klp)
later_earlier = np.zeros((nklp, nklp), np.int8)

for (i, klp1), (j, klp2) in tqdm(
    product(enumerate(flat_klp.values()), repeat=2), total=nklp**2
):
    if klp1["yearOrder"] < klp2["yearOrder"]:
        later_earlier[i, j] = -1
    elif klp1["yearOrder"] == klp2["yearOrder"]:
        if klp1["unitStudyOrder"] < klp2["unitStudyOrder"]:
            later_earlier[i, j] = -1
        elif klp1["unitStudyOrder"] > klp2["unitStudyOrder"]:
            later_earlier[i, j] = 1
    else:
        later_earlier[i, j] = 1


# %%
spA = sp.sparse.csr_array(klpA)
# %%
G = nx.from_numpy_array(klpA)
# %%
G = nx.from_scipy_sparse_array(spA)

# %%
