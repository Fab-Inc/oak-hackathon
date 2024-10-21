from collections import Counter

from tqdm import tqdm
import numpy as np
import tiktoken
from openai import OpenAI


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
        strdocsi, strdocs = zip(
            *[[i, doc] for i, doc in enumerate(documents) if isinstance(doc, str)]
        )
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
