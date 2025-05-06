from fastapi import FastAPI, Form, Query, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
import httpx
import uuid
import json
import os
import asyncio
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

# 의도 인덱스 로드 부분 추가
with open("question_categories.pkl", "rb") as f:
    data = pickle.load(f)
    category_labels = data["labels"]

category_index = faiss.read_index("question_categories.index")
category_model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

# 의도 인덱스 로드
with open("intent_categories.pkl", "rb") as f:
    intent_data = pickle.load(f)
    intent_labels = intent_data["labels"]

intent_index = faiss.read_index("intent_categories.index")
intent_model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

def predict_category(question: str) -> str:
    embedding = category_model.encode([question])
    D, I = category_index.search(np.array(embedding), k=1)
    return category_labels[I[0][0]]

# 의도 분류 함수 추가
def predict_intent(question: str) -> str:
    embedding = intent_model.encode([question])
    D, I = intent_index.search(np.array(embedding), k=1)
    return intent_labels[I[0][0]]
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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session_id: str = None, q: str = None):
    if not session_id:
        session_id = str(uuid.uuid4())
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "session_id": session_id, "query": q}
    )

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

    # 질문 분류
    category = predict_category(prompt)
    # 의도 분류 추가
    intent = predict_intent(prompt)
    print(f"[질문 분류] 입력: {prompt} → 카테고리: {category}, 의도: {intent}")

    # 시스템 메시지로 카테고리와 의도 추가
    if not any(msg["role"] == "system" for msg in active_sessions[session_id]):
        active_sessions[session_id].append({
            "role": "system",
            "content": f"사용자의 질문은 '{category}' 카테고리에 해당하며, '{intent}' 의도를 가집니다. 해당 주제와 의도에 적절한 방식으로 답변하세요."
        })

    # 사용자 메시지 추가
    active_sessions[session_id].append({
        "role": "user",
        "content": prompt
    })

    return JSONResponse(content={
        "status": "success",
        "message": f"메시지가 '{category}' 카테고리, '{intent}' 의도로 분류되어 처리되었습니다."
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