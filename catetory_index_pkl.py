import pickle
import faiss
import numpy as np
import argparse
from sentence_transformers import SentenceTransformer
from category_samples import category_samples

def main(device_choice):
    model_name = "intfloat/multilingual-e5-large-instruct"
    model = SentenceTransformer(model_name, device=device_choice)

    sentences = []
    labels = []

    for category, samples in category_samples.items():
        for s in samples:
            sentences.append(s)
            labels.append(category)

    embeddings = model.encode(sentences)

    if device_choice == "cuda":
        # GPU용 FAISS 설정
        res = faiss.StandardGpuResources()
        index_flat = faiss.IndexFlatL2(embeddings.shape[1])
        index = faiss.index_cpu_to_gpu(res, 0, index_flat)
    else:
        # CPU용 FAISS 설정
        index = faiss.IndexFlatL2(embeddings.shape[1])

    index.add(embeddings)

    data = {
        "embeddings": embeddings,
        "labels": labels
    }

    with open("question_categories.pkl", "wb") as f:
        pickle.dump(data, f)

    faiss.write_index(faiss.index_gpu_to_cpu(index) if device_choice == "cuda" else index,
                      "question_categories.index")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=str, choices=["cpu", "cuda"], default="cpu", help="사용할 디바이스 선택")
    args = parser.parse_args()
    main(args.device)
