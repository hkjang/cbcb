from fastapi import FastAPI, Form, Query, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
import httpx
import uuid
import json
from pathlib import Path
import os
import time
import threading
import pickle
import faiss
import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
import torch

# 글로벌 변수
embedding_model = None
category_index = None
intent_index = None
category_labels = []
intent_labels = []
models_ready = False
loading_thread = None
model_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_cache")

# GPU 사용 가능 여부 확인
use_gpu = torch.cuda.is_available()
device = torch.device("cuda" if use_gpu else "cpu")

app = FastAPI()

# 모델 캐시 디렉토리 확인 및 생성
os.makedirs(model_cache_dir, exist_ok=True)

def load_models_async():
    """
    백그라운드에서 모델 및 인덱스 로드 - 최적화된 버전
    """
    global embedding_model, category_index, intent_index, category_labels, intent_labels, models_ready

    start_time = time.time()
    print(f"모델 로딩 시작... (장치: {device})")

    try:
        # 1. 경량 임베딩 모델 로드 (대형 모델 대신 효율적인 모델 사용)
        model_name = "intfloat/multilingual-e5-large-instruct"  # 더 빠른 로드를 위한 경량 모델

        # 모델 캐시 경로 설정 - 다운로드 속도 향상
        os.environ['TRANSFORMERS_CACHE'] = model_cache_dir

        # 모델 로드 시 최적화 옵션
        embedding_model = SentenceTransformer(model_name, device=device)

        # 메모리 사용량 최적화 (CPU에서 실행 시)
        if not use_gpu:
            # 모델 양자화 (메모리 사용량 감소)
            try:
                from torch.quantization import quantize_dynamic
                embedding_model.model = quantize_dynamic(
                    embedding_model.model, {torch.nn.Linear}, dtype=torch.qint8
                )
                print("모델 양자화 적용됨 (메모리 최적화)")
            except Exception as e:
                print(f"모델 양자화 실패 (무시됨): {e}")

        # 2. 카테고리 인덱스 로드 (예외 처리 및 로깅 강화)
        try:
            if os.path.exists("question_categories.pkl") and os.path.exists("question_categories.index"):
                print("카테고리 인덱스 로딩 중...")
                with open("question_categories.pkl", "rb") as f:
                    data = pickle.load(f)
                    category_labels = data["labels"]

                # 인덱스 파일 로드를 위한 예외 처리 강화
                try:
                    category_index = faiss.read_index("question_categories.index")
                    print(f"카테고리 인덱스 로드 성공 (개수: {len(category_labels)})")
                except Exception as e:
                    print(f"카테고리 인덱스 파일 로드 실패: {e}")
            else:
                print("카테고리 인덱스 파일이 존재하지 않음")
        except Exception as e:
            print(f"카테고리 인덱스 로드 과정 실패: {e}")

        # 3. 의도 인덱스 로드
        try:
            if os.path.exists("intent_categories.pkl") and os.path.exists("intent_categories.index"):
                print("의도 인덱스 로딩 중...")
                with open("intent_categories.pkl", "rb") as f:
                    intent_data = pickle.load(f)
                    intent_labels = intent_data["labels"]

                try:
                    intent_index = faiss.read_index("intent_categories.index")
                    print(f"의도 인덱스 로드 성공 (개수: {len(intent_labels)})")
                except Exception as e:
                    print(f"의도 인덱스 파일 로드 실패: {e}")
            else:
                print("의도 인덱스 파일이 존재하지 않음")
        except Exception as e:
            print(f"의도 인덱스 로드 과정 실패: {e}")

        # 모델 로딩 완료 및 통계 출력
        models_ready = embedding_model is not None
        elapsed = time.time() - start_time

        # 로딩 결과 요약
        ready_status = []
        if embedding_model is not None:
            ready_status.append("임베딩 모델")
        if category_index is not None:
            ready_status.append("카테고리 인덱스")
        if intent_index is not None:
            ready_status.append("의도 인덱스")

        if ready_status:
            print(f"모델 로딩 완료! 준비된 컴포넌트: {', '.join(ready_status)} (소요 시간: {elapsed:.2f}초)")
            # 메모리 최적화를 위한 가비지 컬렉션 실행
            import gc
            gc.collect()
            if use_gpu:
                torch.cuda.empty_cache()
        else:
            print(f"모든 모델 로딩 실패 (소요 시간: {elapsed:.2f}초)")

    except Exception as e:
        print(f"모델 로딩 중 예상치 못한 오류 발생: {e}")

    finally:
        # 로딩 스레드 참조 제거
        global loading_thread
        loading_thread = None


# 서버 시작 시 백그라운드에서 모델 로딩
@app.on_event("startup")
async def startup_event():
    global loading_thread
    if loading_thread is None or not loading_thread.is_alive():
        loading_thread = threading.Thread(target=load_models_async, daemon=True)
        loading_thread.start()

# 예측 함수 (지연 로딩 포함)
def predict_category(question: str) -> str:
    """
    카테고리 예측 함수 - 모델 준비 상태 확인 및 예외 처리
    """
    global models_ready, loading_thread

    # 모델이 준비되지 않았고, 로딩 중이 아니면 로딩 시작
    if not models_ready and (loading_thread is None or not loading_thread.is_alive()):
        loading_thread = threading.Thread(target=load_models_async, daemon=True)
        loading_thread.start()
        return "모델 로딩 중..."

    # 모델이 아직 준비되지 않았으면 대기 메시지 반환
    if not models_ready or embedding_model is None or category_index is None or not category_labels:
        return "모델 준비 중..."

    # 예측 시도
    try:
        # CPU/GPU 메모리 최적화를 위한 with 컨텍스트
        with torch.no_grad():
            # 임베딩 생성
            embedding = embedding_model.encode([question], show_progress_bar=False)
            # 벡터 검색
            D, I = category_index.search(np.array(embedding, dtype=np.float32), k=1)
            # 결과 반환
            return category_labels[I[0][0]]
    except Exception as e:
        print(f"카테고리 예측 오류: {e}")
        return "알 수 없음"

# 의도 예측 함수도 동일한 방식으로 구현
def predict_intent(question: str) -> str:
    """
    의도 예측 함수 - 모델 준비 상태 확인 및 예외 처리
    """
    if not models_ready or embedding_model is None or intent_index is None or not intent_labels:
        return "모델 준비 중..."

    try:
        with torch.no_grad():
            embedding = embedding_model.encode([question], show_progress_bar=False)
            D, I = intent_index.search(np.array(embedding, dtype=np.float32), k=1)
            return intent_labels[I[0][0]]
    except Exception as e:
        print(f"의도 예측 오류: {e}")
        return "알 수 없음"

# 글로벌 변수로 모델, 인덱스 준비 상태 추적
model_ready = False
embedding_model = None
category_index = None
intent_index = None

# 비동기 로딩 시작
threading.Thread(target=load_models_async, daemon=True).start()

# 공통 모델 변수 초기화
category_labels = []
intent_labels = []

# 임베딩 캐시
embedding_cache = {}

def get_embedding(text: str):
    if text in embedding_cache:
        return embedding_cache[text]

    embedding = embedding_model.encode([text])[0]
    embedding_cache[text] = embedding
    return embedding

app = FastAPI()
# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (개발 환경에서만 사용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 대화 상태를 유지하기 위한 메모리 기반 세션 관리
active_sessions = {}

# Ollama 서버 URL 설정
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma3:1b")


@app.api_route("/", methods=["GET", "POST"], response_class=HTMLResponse)
async def index(request: Request, session_id: str = None, q: str = Form(None)):
    if request.method == "POST":
        form = await request.form()
        session_id = form.get("session_id") or str(uuid.uuid4())
        q = form.get("q")
    else:
        if not session_id:
            session_id = str(uuid.uuid4())

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "session_id": session_id, "query": q}
    )
    
# 서버 상태 확인 엔드포인트
@app.get("/api/status")
async def check_model_status():
    """모델 및 인덱스 로딩 상태 확인 API"""
    return {
        "ready": models_ready,
        "components": {
            "embedding_model": embedding_model is not None,
            "category_index": category_index is not None,
            "intent_index": intent_index is not None
        },
        "stats": {
            "category_count": len(category_labels) if category_labels else 0,
            "intent_count": len(intent_labels) if intent_labels else 0,
            "device": str(device)
        }
    }

@app.post("/classify-question")
async def classify_question(question: str = Body(..., embed=True)):
    category = predict_category(question)
    return {"category": category}

@app.post("/classify-intent")
async def classify_intent(question: str = Body(..., embed=True)):
    intent = predict_intent(question)
    return {"intent": intent}

@app.post("/chat")
async def chat(prompt: str = Form(...), session_id: str = Form(...)):
    # 세션을 통한 대화 상태 유지
    if session_id not in active_sessions:
        active_sessions[session_id] = []

    # 질문 분류 및 의도 분류 (예외 처리 포함)
    try:
        category = predict_category(prompt)
        intent = predict_intent(prompt)
        print(f"[질문 분류] 입력: {prompt} → 카테고리: {category}, 의도: {intent}")
        
        classification_message = f"사용자의 질문은"
        
        if category != "알 수 없음":
            classification_message += f" '{category}' 카테고리"
            
        if intent != "알 수 없음":
            if category != "알 수 없음":
                classification_message += f", '{intent}' 의도에 해당합니다."
            else:
                classification_message += f" '{intent}' 의도에 해당합니다."
        else:
            if category != "알 수 없음":
                classification_message += "에 해당합니다."
            else:
                classification_message = "사용자의 질문에 대해 응답해 주세요."
        
        # 시스템 메시지로 카테고리와 의도 추가
        if not any(msg["role"] == "system" for msg in active_sessions[session_id]):
            active_sessions[session_id].append({
                "role": "system",
                "content": classification_message + " 해당 주제와 의도에 적절한 방식으로 답변하세요."
            })
    except Exception as e:
        print(f"분류 과정에서 오류 발생: {e}")
        # 오류 발생 시 기본 시스템 메시지 사용
        if not any(msg["role"] == "system" for msg in active_sessions[session_id]):
            active_sessions[session_id].append({
                "role": "system",
                "content": "사용자의 질문에 대해 응답해 주세요."
            })

    # 사용자 메시지 추가
    active_sessions[session_id].append({
        "role": "user",
        "content": prompt
    })

    # 응답 메시지 생성
    response_message = "메시지가 처리되었습니다."
    if category != "알 수 없음" or intent != "알 수 없음":
        response_message = f"메시지가"
        if category != "알 수 없음":
            response_message += f" '{category}' 카테고리"
        if intent != "알 수 없음":
            if category != "알 수 없음":
                response_message += f", '{intent}' 의도로"
            else:
                response_message += f" '{intent}' 의도로"
        response_message += " 분류되어 처리되었습니다."

    return JSONResponse(content={
        "status": "success",
        "message": response_message
    })

@app.get("/chat-stream")
async def chat_stream(session_id: str = Query(...)):
    if session_id not in active_sessions:
        return JSONResponse(
            status_code=404,
            content={"error": "세션을 찾을 수 없습니다."}
        )

    async def event_generator():
        try:
            # 첫 번째 이벤트 - 연결 확인
            yield {"event": "ping", "data": "연결되었습니다"}

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{OLLAMA_API_URL}/v1/chat/completions", json={
                    "model": OLLAMA_MODEL_NAME,
                    "messages": active_sessions[session_id],
                    "stream": True
                })
                response.raise_for_status()

                # 응답 데이터가 올 때까지 스트림 처리
                buffer = ""
                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()
                    if not line:
                        continue

                    # "data:" 접두사 제거
                    if line.startswith("data:"):
                        line = line[5:].strip()

                    # [DONE] 신호 확인
                    if line == "[DONE]":
                        yield {"data": "[DONE]"}
                        break

                    try:
                        # JSON 파싱 및 전송
                        data = json.loads(line)
                        yield {"data": json.dumps(data)}
                    except json.JSONDecodeError:
                        print(f"JSON 파싱 실패: {line}")
                        continue

            # 응답 메시지 저장
            if session_id in active_sessions and len(active_sessions[session_id]) > 0:
                # 마지막 응답의 모든 청크를 합쳐서 저장하는 로직 필요 (현재는 더미 텍스트)
                active_sessions[session_id].append({
                    "role": "assistant",
                    "content": "AI 응답"  # 실제 응답 내용은 클라이언트에서 조합됨
                })

        except httpx.HTTPStatusError as e:
            yield {"event": "error", "data": f"HTTP 오류 발생: {e.response.status_code}"}
        except httpx.ReadTimeout as e:
            yield {"event": "error", "data": "응답 시간 초과"}
        except Exception as e:
            yield {"event": "error", "data": f"오류 발생: {str(e)}"}

    # SSE 응답 반환
    return EventSourceResponse(event_generator())


# 서버 시작 시 필요한 디렉토리 생성
def setup_directories():
    Path("static").mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)


if __name__ == "__main__":
    setup_directories()
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
