# %%
import json
import pickle
import numpy as np
from tqdm import tqdm

from oakhack.utils import load_oak_lessons
from oakhack.embeddings import BM25
from oakhack import DATA_DIR

scores_dir = DATA_DIR / "bm25_scores"
scores_dir.mkdir(exist_ok=True, parents=True)

# %%
lessons = load_oak_lessons()

# %%
lesson_keys = ["subjectSlug", "examBoardSlug", "unitStudyOrder", "yearOrder"]
flat_klp = [
    {
        "l_index": lidx,
        "klp_index": klpidx,
        **{key: lesson[key] for key in lesson_keys},
        "keyLearningPoint": klp["keyLearningPoint"],
    }
    for lidx, lesson in enumerate(lessons)
    for klpidx, klp in enumerate(lesson["keyLearningPoints"])
]

klp_bm25 = BM25([klp["keyLearningPoint"] for klp in flat_klp])

top_tokens = klp_bm25._encoding.decode_batch(
    [[tok] for tok, _ in sorted(klp_bm25.doc_freqs.items(), key=lambda x: x[1], reverse=True)]
)

print(top_tokens[:10])

# %%
allscores = []
batchscores = []
batchscores_full = []
batchsize = 500
i = -1
while i < len(klp_bm25.documents):
    i += 1
    doc = klp_bm25.documents[i]
    docindex = [
        idx for idx, klp in enumerate(flat_klp) if (
            klp["subjectSlug"] == flat_klp[i]["subjectSlug"]
            and 
            klp["examBoardSlug"] == flat_klp[i]["examBoardSlug"]
        )
    ]
    ### check at the start of each batch if the file exists
    if i % batchsize == 0:
        print(i)
        batchi = i // batchsize
        outfile = scores_dir / f"bm25_scores_batchsize_{batchsize}_batch{batchi :06d}.npz"
        ### load if it does and skip batch
        if outfile.exists():
            batchscores = np.load(outfile)["a"].tolist()
            i += batchsize - 1
    else:
        scores = klp_bm25.get_scores(doc, docindex=docindex)
        scores_full = np.zeros(len(flat_klp))
        scores_full[docindex] = scores
        batchscores.append(scores_full)
    if (i + 1) % batchsize == 0 or i == len(klp_bm25.documents) - 1:
        batchscores_arr = np.array(batchscores)
        if i == len(klp_bm25.documents) - 1:
            batchi = (i + 1) // batchsize
        else:
            batchi = i // batchsize
        outfile = scores_dir / f"bm25_scores_batchsize_{batchsize}_batch{batchi :06d}.npz"
        if not outfile.exists():
            np.savez_compressed(outfile, a=batchscores_arr)
        allscores.append(batchscores_arr)
        batchscores = []

# %%
import numpy as np

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

    idf = np.log((self.doc_count - self.doc_freqs[term] + 0.5) / (self.doc_freqs[term] + 0.5) + 1)
    numerator = term_freq * (self.k1 + 1)
    denominator = term_freq + self.k1 * (1 - self.b + self.b * (doclen / self.avg_doc_length))
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
denominator = term_freq + self.k1 * (1 - self.b + self.b * (doclen[None] / self.avg_doc_length))

result = (idf[:, None] * (numerator / denominator)).sum(axis=0)
