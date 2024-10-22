# %%
from itertools import product

import numpy as np
import scipy as sp
import networkx as nx
from tqdm import tqdm
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import regex as re
import string

import oakhack as oh

from dotenv import load_dotenv

load_dotenv(override=True)
import openai
from openai import OpenAI

from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional

from oakhack.embeddings import get_embeddings

# %%
lessons, l_df = oh.utils.load_oak_lessons_with_df()
flat_klp = oh.utils.extract_klp(lessons)

# %%
print(type(lessons))
print(type(l_df))
print(l_df.shape)
print(l_df.columns)
l_df.head()

# %%
len_klps = []
for i, lesson in enumerate(lessons):
    klps = lesson['keyLearningPoints']
    transcript_sentences = lesson['transcriptSentences']

    klps_list = []
    for klp in klps:
        klps_list.append(klp['keyLearningPoint'])
    len_klps.append(len(klps_list))
    break
    #print(len(klps_list))
    #print(transcript_sentences)

#print(pd.Series(len_klps).value_counts())

# %%
class Dict_clf(BaseModel):
    sentence: Optional[str] = None
    index: Optional[int] = None

class transcript_classified(BaseModel):
    sentences_classified_dict: List[Dict_clf] = Field(default_factory=list)


def classify_transcript_sentences_with_LLM(klps_formatted, transcript_formatted):

    prompt = f"""
    You are given a list of key learning points from a lesson taught by a teacher and a transcript of sentences from the lesson. Your task is to classify each sentence from the transcript based on which key learning point it aligns with the most. Please return the results as a dictionary where each sentence is a key, and the value is the index of the most relevant learning point (e.g., 1, 2, 3, etc.).

    Key Learning Points:
{klps_formatted}

    Video Transcript sentences:
{transcript_formatted}

    Desired Output:
    Return the results as a dictionary in the following format:
    {{
        "[Sentence 1]": Learning_Point_Index,
        "[Sentence 2]": Learning_Point_Index,
        "[Sentence 3]": Learning_Point_Index,
        ...
    }}

    Make sure the values in the dictionary correspond to the index of the most relevant key learning point. Only output the dictionary.
    """
    print(prompt)


    client = OpenAI()
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        #tools=[
        #    openai.pydantic_function_tool(MCQ_both_languages),
        #],
        #response_format=transcript_classified,
    )

    #output = completion.choices[0].message.tool_calls[0].function.parsed_arguments
    return completion

def format_klps(key_learning_points):
    formatted_output = ""
    for idx, klp in enumerate(key_learning_points, 1):
        formatted_output += f"{idx}. {klp}\n"
    return formatted_output.strip()

def format_sentences(transcript_sentences):
    formatted_output = ""
    for idx, sent in enumerate(transcript_sentences, 1):
        formatted_output += f"{sent}\n"
    return formatted_output.strip()

# %%
klps_formatted = format_klps(klps_list)
print(klps_formatted)

transcript_sentences_formatted = format_sentences(transcript_sentences)
print(transcript_sentences_formatted)
# %%
completion = classify_transcript_sentences_with_LLM(klps_formatted, transcript_sentences_formatted)
output = completion.choices[0].message.content#.parsed
print(output)

# %%
pattern = r'\{[^{}]*\}'
output_dict = re.findall(pattern, output)[0] # [0] to have the dict only
# %%
output_df = pd.DataFrame(columns = ['raw data', 'sentence', 'index'])
def save_llm_output_in_df(output):
    pattern = r'\{[^{}]*\}'
    output_dict = re.findall(pattern, output)[0]
    lines = output_dict.split("\n")
    for i, line in enumerate(lines):
        output_df.loc[i, "raw data"] = line
    return output_df

output_df = save_llm_output_in_df(output)
# remove all rows that do not have dict format
print(output_df.shape)
output_df_filtered = output_df[output_df['raw data'].str.contains(":", na = False)].reset_index(drop=True)
print(f"Number of rows before filtering ':': {output_df.shape}\nNumber of rows after filtering ':': {output_df_filtered.shape}")

output_df_filtered['sentence'] = output_df_filtered['raw data'].apply(lambda x: x.split(":")[0])
#output_df_filtered['index'] = output_df_filtered['raw data'].apply(lambda x: x.split(":")[1])
output_df_filtered['index'] = output_df_filtered['raw data'].apply(lambda x: re.findall(r':\s*(\d+)', x)[0])
output_df_filtered.drop(columns = ['raw data'], inplace=True)
print(output_df_filtered.shape)
output_df_filtered.head()

# %%
def clean_sentence(sentence):
    # Remove punctuation
    #sentence = sentence.translate(str.maketrans('', '', string.punctuation))
    # Remove leading and trailing whitespace and replace multiple spaces with a single space
    #cleaned_sentence = ' '.join(sentence.split())
    cleaned_sentence = sentence.lstrip().replace('"', '')
    return cleaned_sentence

output_df_filtered['sentence'] = output_df_filtered['sentence'].apply(lambda x: clean_sentence(x))

# compare to list of sentences in transcript with original list
transcript_sent_llm = output_df_filtered[output_df_filtered['sentence'].isin(transcript_sentences)].reset_index(drop=True)
print(transcript_sent_llm.shape)
transcript_sent_llm.head()


# %%
## with embeddings
print(len(klps_list))
print(len(transcript_sentences))
# %%
# Encode the key learning points and transcript sentences into embeddings
klp_embeddings = get_embeddings(klps_list)
transcript_embeddings = get_embeddings(transcript_sentences)

# %% 
# Compute cosine similarity for each sentence with all key learning points
similarities = cosine_similarity(transcript_embeddings, klp_embeddings)
#print(similarities.shape)

#plt.figure(figsize=(10, 8))
#sns.heatmap(similarities, cmap='coolwarm', annot=False, fmt=".2f", cbar=True, vmin=-1, vmax=1)
#plt.title('Similarity Matrix Heatmap', fontsize=16)
#plt.xlabel('Features', fontsize=12)
#plt.ylabel('Samples', fontsize=12)
#plt.show()

# Assign each sentence to the key learning point with the highest cosine similarity
assigned_indices = np.argmax(similarities, axis=1) + 1  # +1 to match 1-based indexing of learning points
transcript_sent_embed = pd.DataFrame({
    'sentence': transcript_sentences,
    'index': assigned_indices
})

print(transcript_sent_embed.shape)
transcript_sent_embed.head()


# %%
# merge the two approaches
transcript_sent_embed['index llm'] = None
for i, row in transcript_sent_embed.iterrows():
    if len(transcript_sent_llm[transcript_sent_llm['sentence'] == row['sentence']]) != 0:
        transcript_sent_embed.loc[i, "index llm"] = transcript_sent_llm[transcript_sent_llm['sentence'] == row['sentence']]["index"].values[0]

# same type
transcript_sent_embed['index'] = transcript_sent_embed['index'].astype(str)
transcript_sent_embed['index llm'] = transcript_sent_embed['index llm'].astype(str)
print(transcript_sent_embed.shape)
print(transcript_sent_embed['index'].value_counts())
print(transcript_sent_embed['index llm'].value_counts())
transcript_sent_embed.head()

# %%
acc = (transcript_sent_embed['index'] == transcript_sent_embed['index llm']).mean()
print(f"Accuracy: {acc:.2f}")

# %%

# with similarity threshold
def assign_sentence_indices(similarity_matrix, threshold):
    assigned_indices = []

    for row in similarity_matrix:
        max_score = np.max(row)
        max_index = np.argmax(row)
        
        if max_score > threshold:
            assigned_indices.append(int(max_index) + 1) # + 1 to match the real klp indices
        else:
            assigned_indices.append(None)  # No valid index if the max score is below the threshold

    return assigned_indices

sentence_assignments = assign_sentence_indices(similarities, threshold=0.75)
print(pd.Series(sentence_assignments).value_counts())

# %%
klp_transcript = pd.DataFrame({
    "abstract sentence": transcript_sentences,
    "klp assigned idx": sentence_assignments,
    #"klp assigned": None,
})
#klp_transcript['klp assigned'] = klp_transcript['klp assigned idx'].apply(lambda x: klps_list[int(x)] if x != np.nan else x)
print(klp_transcript.shape)
print(klp_transcript['klp assigned idx'].value_counts())
klp_transcript.head()
# %%
for idx in klp_transcript['klp assigned idx'].value_counts():
    print(f"KLP {idx}:\n{klps_list[idx-1]}\nSentences in transcript linked to this KLP:\n-----")
    for sent in klp_transcript[klp_transcript['klp assigned idx'] == idx]['abstract sentence']:
        print(sent)
    print("-----\n\n")

# %%
