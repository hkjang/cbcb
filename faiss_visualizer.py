import pickle
import faiss
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from matplotlib import rc

# 한글 폰트 설정
rc('font', family='Malgun Gothic')  # Windows의 경우
# rc('font', family='AppleGothic')  # macOS의 경우
# rc('font', family='NanumGothic')  # Linux에서 사용할 수 있는 한글 폰트

# 한글 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False

# 1. FAISS 인덱스 로드
index = faiss.read_index("question_categories.index")

# 2. pickle로 저장된 벡터 및 레이블 로드
with open("question_categories.pkl", "rb") as f:
    data = pickle.load(f)

embeddings = data["embeddings"]
labels = data["labels"]

# 3. 차원 축소 (t-SNE)
tsne = TSNE(n_components=2, random_state=42, perplexity=30)
reduced_embeddings = tsne.fit_transform(embeddings)

# 4. 시각화
plt.figure(figsize=(12, 10))

# 범주별로 다른 색상으로 표시
unique_labels = list(set(labels))
colors = plt.cm.get_cmap("tab20", len(unique_labels))

# 스타일링
for i, label in enumerate(unique_labels):
    indices = [idx for idx, lbl in enumerate(labels) if lbl == label]

    # 각 범주별로 다른 마커와 색상을 적용
    plt.scatter(reduced_embeddings[indices, 0], reduced_embeddings[indices, 1],
                label=label, s=100, edgecolors='black', alpha=0.7,
                color=colors(i), marker='o', linewidth=1.5)

# 제목 및 라벨 스타일 추가
plt.title("FAISS question_categories 벡터 시각화 (t-SNE)", fontsize=18, weight='bold', color='#2E3B4E')
plt.xlabel("차원 1", fontsize=14, weight='bold', color='#2E3B4E')
plt.ylabel("차원 2", fontsize=14, weight='bold', color='#2E3B4E')

# 그리드 스타일 조정
plt.grid(True, linestyle='--', alpha=0.7)

# 범례 스타일 조정
plt.legend(loc="best", fontsize=12, title="범주", title_fontsize=14, frameon=False, fancybox=True, facecolor='whitesmoke')

# 배경 스타일
plt.gcf().set_facecolor('whitesmoke')

# x, y 축 눈금 스타일
plt.xticks(fontsize=12, rotation=45, color='#5A5A5A')
plt.yticks(fontsize=12, color='#5A5A5A')

# 시각화
plt.tight_layout()
plt.show()
