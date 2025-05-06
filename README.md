# AI 챗봇

| 항목 | 설명 |
|------|------|
| 이름 | Ollama 기반 AI 챗봇 |
| 목적 | LLM을 활용한 대화형 인공지능 챗봇 제공 |
| 기술 스택 | FastAPI, HTML/CSS/JS, Ollama API, Server-Sent Events |

---

## 📌 소개

이 프로젝트는 Ollama API를 활용한 대화형 AI 챗봇입니다. 사용자와 자연스러운 대화를 나누며 마크다운 형식으로 응답을 표시합니다. Server-Sent Events(SSE)를 통해 실시간 스트리밍 응답을 제공하며, 타이핑 효과로 더욱 자연스러운 대화 경험을 제공합니다.

## 🧩 주요 기능

- 실시간 스트리밍 응답 (타이핑 효과)
- 마크다운 형식 지원 (코드 블록, 표, 목록 등)
- 구문 강조 기능 (Prism.js)
- 세션 기반 대화 기록 유지
- 사용자 친화적인 UI

## 🔧 기술 상세

- **프론트엔드**: HTML, CSS, JavaScript
- **백엔드**: FastAPI (Python)
- **LLM 모델**: Ollama API (gemma3 기본 모델)
- **마크다운 렌더링**: Marked.js
- **코드 구문 강조**: Prism.js
- **스타일링**: GitHub Markdown CSS

## 🚀 실행 방법

### 1. 환경 설정

```shell script
# 저장소 클론
git clone https://github.com/hkjang/ai-chatbot.git
cd ai-chatbot

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 패키지 설치
pip install -r requirements.txt
```


### 2. Ollama 설정

Ollama API 서버가 실행 중이어야 합니다. 기본적으로 `http://127.0.0.1:11434`에서 실행되며, 필요에 따라 환경 변수로 설정을 변경할 수 있습니다.

### 3. 환경 변수 설정 (.env)

`.env` 파일 생성 후 다음 내용 입력:

```
OLLAMA_API_URL=http://127.0.0.1:11434
OLLAMA_MODEL_NAME=gemma3
```


### 4. 서버 실행

```shell script
python main.py
```


브라우저에서 `http://127.0.0.1:8000` 접속

## 💬 사용 방법

1. 웹 인터페이스에 접속합니다.
2. 입력 필드에 질문이나 메시지를 입력합니다.
3. "질문하기" 버튼을 클릭하거나 Enter 키를 누릅니다.
4. AI가 실시간으로 응답을 생성하고 마크다운 형식으로 표시합니다.

## 📁 디렉터리 구조

```
ai-chatbot/
├── main.py              # FastAPI 서버 코드
├── templates/           # HTML 템플릿
│   └── index.html       # 웹 UI 메인 페이지
├── static/              # 정적 자원
│   ├── style.css        # 스타일시트
│   └── chat.js          # 클라이언트 스크립트
├── .env                 # 환경 변수
└── requirements.txt     # 의존성 패키지
```


## 📦 의존 패키지 (requirements.txt)

```
fastapi
uvicorn
jinja2
sse-starlette
httpx
python-multipart
python-dotenv
```


## 🔄 마크다운 지원

챗봇은 다음과 같은 마크다운 형식을 지원합니다:

- 제목 및 소제목 (# ~ ######)
- 목록 (순서 있는/없는 목록)
- 코드 블록 (```
- 표 (|로 구분된 테이블)
- 인용문 (> 사용)
- 링크 및 이미지
- 굵게, 기울임, 취소선 등 텍스트 스타일링

## 🛠️ 커스터마이징

### 모델 변경

`.env` 파일의 `OLLAMA_MODEL_NAME` 값을 변경하여 다른 Ollama 모델을 사용할 수 있습니다.

### 스타일 변경

`static/style.css` 파일을 수정하여 UI 디자인을 변경할 수 있습니다.

## ⚠️ 주의사항

- Ollama API 서버가 사전에 실행되어 있어야 합니다.
- 대량의 트래픽 처리를 위해서는 추가적인 서버 최적화가 필요합니다.
- 현재 구현은 메모리 기반 세션 관리를 사용하므로 서버 재시작 시 대화 기록이 초기화됩니다.

## 📝 향후 개선 계획

- 영구적인 대화 기록 저장 (데이터베이스 연동)
- 사용자 인증 기능 추가
- 멀티 모델 선택 기능
- 응답 속도 및 품질 최적화
- 다국어 인터페이스 지원

## 📜 라이선스

MIT License

## 👥 기여

이슈나 PR을 통해 프로젝트 개선에 기여해주세요. 모든 기여를 환영합니다!
