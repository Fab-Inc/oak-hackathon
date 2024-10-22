#%%
from oakhack.utils import load_oak_lessons, extract_klp
from oakhack.embeddings import BM25, get_embeddings
from oakhack import DATA_DIR
import oakhack as oh
#%%

programmes, units = oh.utils.load_oak_programmes_units()
lessons, l_df = oh.utils.load_oak_lessons_with_df()
questions, q_df = oh.utils.extract_questions(lessons)
extracted_questions = oh.utils.extract_question_content(questions)
q_strs = ["\n".join(q["text"]) for q in extracted_questions]

# %%
embs = get_embeddings(q_strs, verbose=1)
# %%
batch_size = 3000
embsarr = np.array(embs, dtype=np.float32)
for i, batch_start in enumerate(range(0, embsarr.shape[0], batch_size)):
    outarr = embsarr[batch_start : batch_start + batch_size]
    np.save(
        DATA_DIR / f"embeddings/question_embeddings_batch_size{batch_size}_{i :05d}.npy",
        outarr,
    )