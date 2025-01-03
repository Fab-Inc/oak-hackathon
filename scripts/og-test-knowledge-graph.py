# %%
import numpy as np
from tqdm import tqdm
import json
import gzip

from oakhack.utils import load_oak_lessons, extract_klp
from oakhack.embeddings import BM25, get_embeddings
from oakhack import DATA_DIR

scores_dir = DATA_DIR / "bm25_scores"
scores_dir.mkdir(exist_ok=True, parents=True)

# %%
lessons = load_oak_lessons()

flat_klp = extract_klp(lessons)

# %%
klp_bm25 = BM25([klp["keyLearningPoint"] for klp in flat_klp.values()])

top_tokens = klp_bm25._encoding.decode_batch(
    [
        [tok]
        for tok, _ in sorted(
            klp_bm25.doc_freqs.items(), key=lambda x: x[1], reverse=True
        )
    ]
)

print(top_tokens[:10])

# %%
allscores = []
batchscores = []
batchscores_full = []
batchsize = 500
loaded = False
for i in range(len(klp_bm25.documents)):
    ### check at the start of each batch if the file exists
    if i % batchsize == 0:
        print(i)
        batchi = i // batchsize
        outfile = (
            scores_dir / f"bm25_scores_batchsize_{batchsize}_batch{batchi :06d}.npz"
        )
        ### load if it does and skip batch
        if outfile.exists():
            batchscores = np.load(outfile)["a"]
            print(batchscores.shape[0])
            loaded = True
    if not loaded:
        doc = klp_bm25.documents[i]
        docindex = [
            idx
            for idx, klp in enumerate(flat_klp)
            if (
                klp["subjectSlug"] == flat_klp[i]["subjectSlug"]
                and klp["examBoardSlug"] == flat_klp[i]["examBoardSlug"]
            )
        ]
        scores = klp_bm25.get_scores(doc, docindex=docindex)
        scores_full = np.zeros(len(flat_klp))
        scores_full[docindex] = scores
        batchscores.append(scores_full)
    if (i + 1) % batchsize == 0 or i == len(klp_bm25.documents) - 1:
        if loaded:
            batchscores_arr = batchscores
        else:
            batchscores_arr = np.array(batchscores)
        batchi = i // batchsize
        print(batchi)
        outfile = (
            scores_dir / f"bm25_scores_batchsize_{batchsize}_batch{batchi :06d}.npz"
        )
        if not outfile.exists():
            np.savez_compressed(outfile, a=batchscores_arr.astype(np.float32))
        allscores.append(batchscores_arr)
        batchscores = []
        loaded = False

# %%
embs = get_embeddings(klp_bm25.documents, verbose=1)

# %%
batch_size = 3000
embsarr = np.array(embs, dtype=np.float32)
for i, batch_start in enumerate(range(0, embsarr.shape[0], batch_size)):
    outarr = embsarr[batch_start : batch_start + batch_size]
    np.save(
        DATA_DIR / f"embeddings/klp_embeddings_batch_size{batch_size}_{i :05d}.npy",
        outarr,
    )

# %%


# %%
#! %%timeit

doclen = np.array([len(doc) for doc in klp_bm25.documents])
maxlendoc = doclen.max()

docarray = np.full((klp_bm25.doc_count, maxlendoc), fill_value=np.nan)

for i, doc in enumerate(klp_bm25.documents):
    docarray[i, : len(doc)] = doc

# %%
#! %%timeit

(~np.isnan(docarray)).sum(axis=1)

# %%
#! %%timeit
self = klp_bm25
result = 0
for term in self.documents[0]:

    term_freq = (docarray == term).sum(axis=1)

    idf = np.log(
        (self.doc_count - self.doc_freqs[term] + 0.5) / (self.doc_freqs[term] + 0.5) + 1
    )
    numerator = term_freq * (self.k1 + 1)
    denominator = term_freq + self.k1 * (
        1 - self.b + self.b * (doclen / self.avg_doc_length)
    )
    result += idf * (numerator / denominator)

# %%
#! %%timeit
self = klp_bm25
terms = np.array(self.documents[0])

term_freq = (docarray[None, :, :] == terms[:, None, None]).sum(axis=2)

idf = np.log(
    [
        (self.doc_count - self.doc_freqs[term] + 0.5) / (self.doc_freqs[term] + 0.5) + 1
        for term in terms
    ]
)
numerator = term_freq * (self.k1 + 1)
denominator = term_freq + self.k1 * (
    1 - self.b + self.b * (doclen[None] / self.avg_doc_length)
)

result = (idf[:, None] * (numerator / denominator)).sum(axis=0)
