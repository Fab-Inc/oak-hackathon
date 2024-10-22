# %%
import oakhack as oh
from oakhack.utils import load_embeddings
import numpy as np
from pathlib import Path

# %%


# %%
klp_embs = load_embeddings("klp_embeddings_batch_size3000_*.npy")

#%%
q_embs = load_embeddings("question_embeddings_batch_size3000_*.npy")
# %%
