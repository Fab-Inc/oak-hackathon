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
Label each klp pairwise combination (klp1 x klp2) for if klp1 is earlier or not
"""
nklp = len(flat_klp)

year_order = np.array([klp["yearOrder"] for klp in flat_klp.values()])
unit_study_order = np.array([klp["unitStudyOrder"] for klp in flat_klp.values()])

earlier = np.packbits(
    (year_order[:, None] < year_order[None])
    | (
        (year_order[:, None] == year_order[None])
        & (unit_study_order[:, None] < unit_study_order[None])
    )
)


# %%
spA = sp.sparse.csr_array(klpA)

# %%
G = nx.from_numpy_array(klpA)

# %%
G = nx.from_scipy_sparse_array(spA)

# %%
# get lesson info from a klp
key = "biology-secondary-ks4-foundation-aqa/eukaryotic-and-prokaryotic-cells/cells/0"
*lesson_key, klp_idx = key.split("/")
lesson_key = "/".join(lesson_key)
lesson = lessons[l_df[l_df.lessonKey == lesson_key].index]

# %%
