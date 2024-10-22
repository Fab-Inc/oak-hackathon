# %%
import oakhack as oh
import numpy as np
from pathlib import Path

# %%
def load_embeddings(filename_pattern):
    load_arrs = []
    for f in sorted(
        (oh.DATA_DIR / "embeddings").glob(filename_pattern)
    ):
        load_arrs.append(np.load(f))
    return np.concatenate(load_arrs,axis=0)

# %%
klp_embs = load_embeddings("klp_embeddings_batch_size3000_*.npy")

#%%
q_embs = load_embeddings("klp_embeddings_batch_size3000_*.npy")
# %%
batch_size = 3000
embsarr = np.array(embs, dtype=np.float32)
for i, batch_start in enumerate(range(0, embsarr.shape[0], batch_size)):
    outarr = embsarr[batch_start : batch_start + batch_size]
    np.save(
        DATA_DIR
        / f"embeddings/question_embeddings_batch_size{batch_size}_{i :05d}.npy",
        outarr,
    )
# %%
