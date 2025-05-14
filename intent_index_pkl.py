import pickle
import faiss
import numpy as np
import argparse
from sentence_transformers import SentenceTransformer
from intent_samples import intent_samples

def main(device_choice):
    model_name = "intfloat/multilingual-e5-large-instruct"
    model = SentenceTransformer(model_name, device=device_choice)

    sentences = []
    labels = []

    for intent, samples in intent_samples.items():
        for s in samples:
            sentences.append(s)
            labels.append(intent)

    embeddings = model.encode(sentences)

    if device_choice == "cuda":
        res = faiss.StandardGpuResources()
        index_flat = faiss.IndexFlatL2(embeddings.shape[1])
        index = faiss.index_cpu_to_gpu(res, 0, index_flat)
    else:
        index = faiss.IndexFlatL2(embeddings.shape[1])

    index.add(embeddings)

    data = {
        "embeddings": embeddings,
        "labels": labels
    }

    with open("intent_categories.pkl", "wb") as f:
        pickle.dump(data, f)

    faiss.write_index(faiss.index_gpu_to_cpu(index) if device_choice == "cuda" else index,
                      "intent_categories.index")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=str, choices=["cpu", "cuda"], default="cpu", help="사용할 디바이스 선택")
    args = parser.parse_args()
    main(args.device)
