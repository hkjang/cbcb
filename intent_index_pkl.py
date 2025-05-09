import pickle
import faiss
from sentence_transformers import SentenceTransformer
from intent_samples import intent_samples
import numpy as np

# SentenceTransformer 모델 로드
model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

sentences = []
labels = []

# intent_samples에서 문장과 라벨 추출
for intent, samples in intent_samples.items():
    for s in samples:
        sentences.append(s)
        labels.append(intent)

# 문장을 임베딩으로 변환
embeddings = model.encode(sentences)

# FAISS 인덱스 생성 및 임베딩 추가
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# 데이터 저장을 위한 딕셔너리 생성
data = {
    "embeddings": embeddings,
    "labels": labels
}

# 피클 파일로 저장
with open("intent_categories.pkl", "wb") as f:
    pickle.dump(data, f)

# FAISS 인덱스 파일로 저장
faiss.write_index(index, "intent_categories.index")
