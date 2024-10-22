# %%
from itertools import product
import json

import numpy as np
import scipy as sp
import networkx as nx
from tqdm import tqdm

import oakhack as oh

# %%
lessons, l_df = oh.utils.load_oak_lessons_with_df()
flat_klp = oh.utils.extract_klp(lessons)

# %%
### load klp BM25 scores and normalise
klpA = oh.embeddings.get_klp_BM25(flat_klp)

klpA = klpA / klpA.max(axis=1)

# %%#
### load klp embeddinds and calculate scores
klp_embs = oh.load_embeddings("klp_embeddings_batch_size3000_*.npy")

klpB = klp_embs @ klp_embs.T

# %%
### filter klp by programme
programme = "biology-secondary-ks4-foundation-aqa"

klp_programme_index = [
    i for (i, key) in enumerate(flat_klp) if key.split("/")[0] == programme
]
klppi_ix = np.ix_(klp_programme_index, klp_programme_index)

klpA_programme = klpA[klppi_ix]
klpB_programme = klpB[klppi_ix]
flat_klp_programme = {
    key: klp for i, (key, klp) in enumerate(flat_klp.items()) if i in klp_programme_index
}

flat_klp_programme_list = list(flat_klp_programme.values())
# %%
### Label each klp pairwise combination (klp1 x klp2) for if klp1 is earlier or not
nklp = len(flat_klp_programme)

year_order = np.array([klp["yearOrder"] for klp in flat_klp_programme.values()])
unit_study_order = np.array([klp["unitStudyOrder"] for klp in flat_klp_programme.values()])

earlier = (year_order[:, None] < year_order[None]) | (
    (year_order[:, None] == year_order[None])
    & (unit_study_order[:, None] < unit_study_order[None])
)

# %%
### mask the adjacency matrices with the 'earlier' array

klpA_masked = klpA_programme * earlier
np.fill_diagonal(klpA_masked, 0)

klpB_masked = klpB_programme * earlier
np.fill_diagonal(klpB_masked, 0)

# %%
# create graph and show shortest paths from all nodes to all other nodes

# simularity score threshold to craete edge on graph
cutoff = 0.4
# weight of embeddings in combined score
embwt = 0.8

# final adjacency matrix
klp_adj = (klpA_masked * (1-embwt) + klpB_masked * embwt)
klp_adj =  np.minimum(klp_adj * (klp_adj > cutoff), 1)

# create graph and set node attributes
G = nx.from_numpy_array(klp_adj.T, create_using=nx.DiGraph)
nx.set_node_attributes(G, {i: klp for i, klp in enumerate(flat_klp_programme.values())})
# create edge length attribute as complement of weight
# this is to make shortest path calculations make sense
for *_, attr_dict in G.edges(data=True):
    attr_dict["length"] = 1 - attr_dict["weight"]

# get shortests paths between all pairs of nodes in the graph
spaths = dict(nx.all_pairs_dijkstra(G, weight="length"))

# print only those paths longer than 3
for nodeidx, (lengths, paths) in spaths.items():
    for targetnode in paths:
        path = paths[targetnode]
        if len(path) > 3:
            # print((nodeidx, targetnode), path)
            print(
                json.dumps(
                    [flat_klp_programme_list[i]for i in path], indent=2
                )
            )
            length = lengths[targetnode]
            # print((nodeidx, targetnode), path)
            print(length)
