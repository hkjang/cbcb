import pickle
import faiss
from sentence_transformers import SentenceTransformer
from category_samples import category_samples
import numpy as np

model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

sentences = []
labels = []

for category, samples in category_samples.items():
    for s in samples:
        sentences.append(s)
        labels.append(category)

embeddings = model.encode(sentences)
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

data = {
    "embeddings": embeddings,
    "labels": labels
}

with open("question_categories.pkl", "wb") as f:
    pickle.dump(data, f)

faiss.write_index(index, "question_categories.index")
