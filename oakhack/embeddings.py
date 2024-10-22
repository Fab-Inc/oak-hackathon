from collections import Counter

from tqdm import tqdm
import numpy as np
import tiktoken
from openai import OpenAI

from .constants import DATA_DIR

class BM25:
    def __init__(
        self,
        documents: list[list[int] | str],
        k1=1.5,
        b=0.75,
        encoding_model="text-embedding-3-large",
    ):
        self._encoding = tiktoken.encoding_for_model(encoding_model)
        self.documents = documents.copy()
        self.doc_count = len(self.documents)
        strdocsi_strdocs = [[i, doc] for i, doc in enumerate(documents) if isinstance(doc, str)]
        if len(strdocsi_strdocs) > 0:
            strdocsi, strdocs = zip(*strdocsi_strdocs)
        else:
            strdocsi, strdocs = [], []

        strdocs_encoded = self._encoding.encode_batch(strdocs)
        for i, strdoc_encoded in zip(strdocsi, strdocs_encoded):
            self.documents[i] = strdoc_encoded

        # vector stuff
        self.doclen = np.array([len(doc) for doc in self.documents])
        maxlendoc = self.doclen.max()
        self.docarray = np.full((self.doc_count, maxlendoc), fill_value=np.nan)
        for i, doc in enumerate(self.documents):
            self.docarray[i, : len(doc)] = doc
        ####

        self.k1 = k1  # Term frequency scaling factor
        self.b = b  # Length normalization factor
        self.avg_doc_length = self._average_document_length()
        self.doc_freqs = self._calculate_doc_frequencies()

    def _average_document_length(self):
        total_length = sum(len(doc) for doc in self.documents)
        return total_length / self.doc_count

    def _calculate_doc_frequencies(self):
        doc_freqs = Counter()
        for doc in self.documents:
            unique_terms = set(doc)
            for term in unique_terms:
                doc_freqs[term] += 1
        return doc_freqs

    def _bm25_score_vectorized(self, term, docarray, doclen):
        term_freq = (docarray == term).sum(axis=1)

        idf = np.log(
            (self.doc_count - self.doc_freqs[term] + 0.5) / (self.doc_freqs[term] + 0.5) + 1
        )
        numerator = term_freq * (self.k1 + 1)
        denominator = term_freq + self.k1 * (1 - self.b + self.b * (doclen / self.avg_doc_length))

        return idf * (numerator / denominator)

    def _bm25_score(self, term, doc):
        term_freq = doc.count(term)
        if term_freq == 0:
            return 0.0

        idf = np.log(
            (self.doc_count - self.doc_freqs[term] + 0.5) / (self.doc_freqs[term] + 0.5) + 1
        )

        numerator = term_freq * (self.k1 + 1)
        denominator = term_freq + self.k1 * (
            1 - self.b + self.b * (len(doc) / self.avg_doc_length)
        )

        return idf * (numerator / denominator)

    def get_scores_doc(self, query: list[int] | str, doc: list[int] | str):
        score = 0
        if isinstance(query, str):
            query = self._encoding.encode(query)
        if isinstance(doc, str):
            doc = self._encoding.encode(doc)
        for term in query:
            score += self._bm25_score(term, doc)
        return score
    
    def get_scores_index_slice(self, query: list[int] | str, index_lower: int = 0, index_upper: int = -1):
        scores = []
        if isinstance(query, str):
            query = self._encoding.encode(query)
        docs_of_interest = self.documents[index_lower:index_upper]
        for idx, doc in enumerate(docs_of_interest):
            scores.append([idx, 0])
            for term in query:
                scores[idx][1] += self._bm25_score(term, doc)
        scores.sort(key=lambda x: x[1],reverse=True)
        return scores

    def get_scores(self, query: list[int] | str, vectorized=True, docindex=None):
        if docindex is None:
            docindex = np.arange(self.doc_count)
        scores = np.zeros(len(docindex))
        if vectorized:
            docarray = self.docarray[docindex]
            doclen = self.doclen[docindex]
            for term in query:
                scores += self._bm25_score_vectorized(term, docarray, doclen)
        else:
            for i in docindex:
                doc = self.documents[i]
                scores[i] += self.get_scores_doc(query, doc)
        return scores


def get_embeddings(
    documents: list[list[int] | str],
    encoding_model="text-embedding-3-large",
    batch_size=2048,
    verbose=0,
):
    client = OpenAI()
    embeddings = []
    batchiter = range(0, len(documents), batch_size)
    if verbose > 0:
        batchiter = tqdm(batchiter)
    for batch_start in batchiter:
        batch_docs = documents[batch_start : batch_start + batch_size]
        create_out = client.embeddings.create(input=batch_docs, model=encoding_model)
        embeddings.extend([emb.embedding for emb in create_out.data])
    return embeddings


def get_klp_BM25(flat_klp, scores_dir=DATA_DIR / "bm25_scores"):
    klp_bm25 = BM25([klp["keyLearningPoint"] for klp in flat_klp.values()])

    top_tokens = klp_bm25._encoding.decode_batch(
        [[tok] for tok, _ in sorted(klp_bm25.doc_freqs.items(), key=lambda x: x[1], reverse=True)]
    )

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
            outfile = scores_dir / f"bm25_scores_batchsize_{batchsize}_batch{batchi :06d}.npz"
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
            outfile = scores_dir / f"bm25_scores_batchsize_{batchsize}_batch{batchi :06d}.npz"
            if not outfile.exists():
                np.savez_compressed(outfile, a=batchscores_arr.astype(np.float32))
            allscores.append(batchscores_arr)
            batchscores = []
            loaded = False

    A = np.concatenate(allscores, axis=0)
    return A
