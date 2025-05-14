// 타이핑 효과 관련 변수
let typewriterQueue = [];
let isTyping = false;
let typingSpeed = 2; // 타이핑 속도 (ms)
let botMessageContainer = null;
let typingIndicator = null;
let botMessageContent = ''; // 마크다운 텍스트를 저장할 변수

/**
 * Mermaid 다이어그램에서 주석을 제거하는 함수
 * @param {string} mermaidContent - Mermaid 다이어그램 내용
 * @returns {string} 주석이 제거된 Mermaid 다이어그램 내용
 */
function preprocessMermaidDiagram(mermaidContent) {
  if (!mermaidContent) return mermaidContent;
  
  // 각 줄을 처리합니다
  const lines = mermaidContent.split('\n');
  const cleanedLines = lines.map(line => {
    // 행 내 주석 제거 (스페이스 + // + 나머지 텍스트)
    let cleanedLine = line.replace(/\s+\/\/.*$/, '');
    
    // 행의 시작부분에 있는 주석 제거 (// + 나머지 텍스트)
    cleanedLine = cleanedLine.replace(/^\/\/.*$/, '');
    
    return cleanedLine;
  });
  
  // 빈 줄 제거 (선택적)
  const result = cleanedLines.filter(line => line.trim() !== '').join('\n');
  
  return result;
}


// 코드 블록에 복사 버튼 추가하는 함수
function addCopyButtonsToCodeBlocks(container) {
    const codeBlocks = container.querySelectorAll('pre');

    codeBlocks.forEach((codeBlock) => {
        // 이미 버튼이 있는지 확인
        if (codeBlock.querySelector('.copy-button')) {
            return;
        }

        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '<i class="fa-regular fa-copy"></i>'; // Font Awesome 복사 아이콘
        copyButton.setAttribute('aria-label', '코드 복사하기');
        copyButton.setAttribute('title', '클립보드에 복사');

        // 버튼 클릭 이벤트 추가
        copyButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            // 코드 블록 내용 가져오기
            const code = codeBlock.querySelector('code');
            if (!code) {
                return;
            }

            const textToCopy = code.textContent;

            // 클립보드에 복사
            navigator.clipboard.writeText(textToCopy).then(() => {
                // 복사 성공 시 버튼 스타일 변경
                copyButton.innerHTML = '<i class="fa-solid fa-check"></i>'; // 체크 아이콘으로 변경
                copyButton.classList.add('copied');

                // 1.5초 후 원래 상태로 복원
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fa-regular fa-copy"></i>';
                    copyButton.classList.remove('copied');
                }, 1500);
            }).catch(err => {
                copyButton.innerHTML = '<i class="fa-solid fa-xmark"></i>'; // 실패 아이콘
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fa-regular fa-copy"></i>';
                }, 1500);
            });
        });

        // 코드 블록에 버튼 추가
        codeBlock.style.position = 'relative';
        codeBlock.prepend(copyButton);

        // 언어 표시 추가
        const codeElement = codeBlock.querySelector('code');
        if (codeElement && codeElement.className) {
            // language-xxx 형식에서 언어 부분 추출
            const languageMatch = codeElement.className.match(/language-([^\s]+)/);
            if (languageMatch && languageMatch[1]) {
                const language = languageMatch[1];
                
                // 언어 라벨 생성
                const languageLabel = document.createElement('div');
                languageLabel.className = 'language-label';
                languageLabel.textContent = language;
                languageLabel.style.position = 'absolute';
                languageLabel.style.top = '0';
                languageLabel.style.left = '0';
                languageLabel.style.fontSize = '12px';
                languageLabel.style.padding = '2px 6px';
                languageLabel.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
                languageLabel.style.color = '#fff';
                languageLabel.style.borderRadius = '0 0 4px 0';
                languageLabel.style.zIndex = '1';
                
                // 코드 블록에 라벨 추가
                codeBlock.prepend(languageLabel);
            }
        }

        // Mermaid 다이어그램일 경우 팝업 버튼 추가
        console.log(codeBlock.classList.contains('language-mermaid'));
        if (codeBlock.classList.contains('language-mermaid')) {
          const mermaidButton = document.createElement('button');
          mermaidButton.className = 'mermaid-button';
          mermaidButton.innerHTML = '<i class="fas fa-project-diagram"></i>';
          mermaidButton.title = 'Mermaid 다이어그램 팝업으로 보기';
          mermaidButton.onclick = function() {
            const mermaidCode = codeBlock.textContent;
            createMermaidPopup(mermaidCode);
          };
          codeBlock.prepend(mermaidButton);
        }
    });
}

// 전체 메시지에 복사 버튼 추가
function addCopyButtonToMessage(messageContainer) {
    // 이미 버튼이 있는지 확인
    if (messageContainer.querySelector('.message-copy-button')) {
        return;
    }

    const copyButton = document.createElement('button');
    copyButton.className = 'message-copy-button';
    copyButton.innerHTML = '<i class="fa-regular fa-copy"></i>'; // Font Awesome 복사 아이콘
    copyButton.setAttribute('aria-label', '전체 응답 복사하기');
    copyButton.setAttribute('title', '전체 응답 복사');

    // 버튼 클릭 이벤트 추가
    copyButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        // 메시지 내용 가져오기 (HTML 태그 제외)
        const textToCopy = botMessageContent;

        // 클립보드에 복사
        navigator.clipboard.writeText(textToCopy).then(() => {
            // 복사 성공 시 버튼 스타일 변경
            copyButton.innerHTML = '<i class="fa-solid fa-check"></i>';
            copyButton.classList.add('copied');

            // 1.5초 후 원래 상태로 복원
            setTimeout(() => {
                copyButton.innerHTML = '<i class="fa-regular fa-copy"></i>';
                copyButton.classList.remove('copied');
            }, 1500);
        }).catch(err => {
            copyButton.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            setTimeout(() => {
                copyButton.innerHTML = '<i class="fa-regular fa-copy"></i>';
            }, 1500);
        });
    });

    // 메시지 컨테이너에 버튼 추가
    messageContainer.style.position = 'relative';
    messageContainer.appendChild(copyButton);
}

// Mermaid 다이어그램 팝업 생성 함수
function createMermaidPopup(diagram) {
    // 팝업 창 생성
    const popup = window.open('', '_blank', 'width=800,height=600');
    
    // 다이어그램 내용 전처리
    let processedDiagram = preprocessMermaidDiagram(diagram);
    // 대괄호 안 소괄호 공백 처리
    processedDiagram = preprocessMermaidDiagram_brackets(processedDiagram);
    // 중괄호 안 소괄호 공백 처리
    processedDiagram = preprocessMermaidDiagram_curly_brackets(processedDiagram);
    // 괄호 균형 검사 및 수정
    processedDiagram = checkAndFixBracketBalance(processedDiagram);

    processedDiagram = processedDiagram.replace(/mermaid/g, '');

    console.log(processedDiagram);
    // 팝업 HTML 작성
    popup.document.write(`
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Mermaid 다이어그램</title>
            <script src="/static/js/mermaid.min.js"></script>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 100%;
                    margin: 0 auto;
                }
                h1 {
                    color: #333;
                    font-size: 24px;
                    margin-bottom: 20px;
                    text-align: center;
                }
                #mermaid-diagram {
                    display: flex;
                    justify-content: center;
                    overflow: auto;
                }
                .mermaid {
                    margin: 0 auto;
                }
                .error-message {
                    color: #e74c3c;
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    border: 1px solid #e74c3c;
                    border-radius: 4px;
                    display: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Mermaid 다이어그램</h1>
                <div id="error-container" class="error-message"></div>
                <div id="mermaid-diagram">
                    <pre class="mermaid">
${processedDiagram}
                    </pre>
                </div>
            </div>
            <script>
                mermaid.initialize({
                    startOnLoad: true,
                    theme: 'default',
                    securityLevel: 'loose',
                    logLevel: 1,
                    flowchart: {
                        useMaxWidth: false,
                        htmlLabels: true,
                        diagramPadding: 8
                    },
                    sequence: {
                        diagramMarginX: 50,
                        diagramMarginY: 10,
                        actorMargin: 50,
                        width: 150,
                        height: 65
                    },
                    er: {
                        diagramPadding: 20
                    }
                });
                
                window.onload = function() {
                    try {
                        // 일정 시간 후에 mermaid 다시 초기화 (로딩 이슈 해결용)
                        setTimeout(() => {
                            try {
                                mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                            } catch(err) {
                                console.error('Mermaid 초기화 오류:', err);
                                document.getElementById('error-container').textContent = '다이어그램 렌더링 오류: ' + err.message;
                                document.getElementById('error-container').style.display = 'block';
                            }
                        }, 500);
                    } catch(err) {
                        console.error('Mermaid 오류:', err);
                        document.getElementById('error-container').textContent = '다이어그램 렌더링 오류: ' + err.message;
                        document.getElementById('error-container').style.display = 'block';
                    }
                }
            </script>
        </body>
        </html>
    `);
    
    popup.document.close();
}

// Mermaid 다이어그램 전처리 함수 - 구문 오류 방지
function preprocessMermaidDiagram_brackets(diagram) {
    // 대괄호([]) 안의 소괄호(()) 처리
    // 대괄호 내의 텍스트에서 괄호 쌍이 있는 경우 이스케이프
    let processedDiagram = diagram.replace(/\[(.*?)\]/g, function(match, content) {
        // 대괄호 내용 중 소괄호를 HTML 엔티티로 변환
        // let processed = content.replace(/\(/g, '&lpar;').replace(/\)/g, '&rpar;');
        let processed = content.replace(/\(/g, ' ').replace(/\)/g, '');
        console.log(processed)
        return '[' + processed + ']';
    });
    
    // 줄 끝의 공백 제거 (불필요한 공백으로 인한 오류 방지)
    processedDiagram = processedDiagram.split('\n').map(line => line.trimRight()).join('\n');
    
    // 다이어그램 시작/끝에 빈 줄 제거
    processedDiagram = processedDiagram.trim();
    
    return processedDiagram;
}
// Mermaid 다이어그램 전처리 함수 - 구문 오류 방지
function preprocessMermaidDiagram_curly_brackets(diagram) {
    // 대괄호([]) 안의 소괄호(()) 처리
    // 대괄호 내의 텍스트에서 괄호 쌍이 있는 경우 이스케이프
    let processedDiagram = diagram.replace(/\{(.*?)\}/g, function(match, content) {
        // 대괄호 내용 중 소괄호를 HTML 엔티티로 변환
        // let processed = content.replace(/\(/g, '&lpar;').replace(/\)/g, '&rpar;');
        let processed = content.replace(/\(/g, ' ').replace(/\)/g, '');
        console.log(processed)
        return '{' + processed + '}';
    });

    // 줄 끝의 공백 제거 (불필요한 공백으로 인한 오류 방지)
    processedDiagram = processedDiagram.split('\n').map(line => line.trimRight()).join('\n');

    // 다이어그램 시작/끝에 빈 줄 제거
    processedDiagram = processedDiagram.trim();

    return processedDiagram;
}

// Mermaid 다이어그램 감지 및 처리 함수 (HTML 기반)
function detectAndHandleMermaid() {
    try {
        // 렌더링된 HTML에서 Mermaid 코드 블록 찾기
        const mermaidElements = botMessageContainer.querySelectorAll('code.language-mermaid');
        
        if (mermaidElements.length > 0) {
            // 첫 번째 Mermaid 코드 블록 가져오기
            const diagramContent = mermaidElements[0].textContent.trim();
            console.log('mermaid 다이어그램 감지됨');
            
            // 내용이 있으면 팝업 생성
            if (diagramContent) {
                // 1초 지연 후 팝업 생성 (마크다운 렌더링 완료 후)
                setTimeout(() => {
                    createMermaidPopup(diagramContent);
                }, 1000);
            }
        }
    } catch (error) {
        console.error('Mermaid 다이어그램 처리 오류:', error);
    }
}

function submitOnEnter(event) {
    if (event.key === 'Enter') {
        if (!event.shiftKey) {
            if (!event.repeat) {
                event.preventDefault();
                const newEvent = new Event("submit", {cancelable: true});
                event.target.form.dispatchEvent(newEvent);
            }
        }
    }
}

document.getElementById("prompt").addEventListener("keydown", submitOnEnter);

// Marked.js 설정 커스터마이징
document.addEventListener('DOMContentLoaded', function() {
    // Marked 설정 - 줄바꿈 처리 및 Prism.js를 사용한 구문 강조 적용
    marked.setOptions({
        renderer: new marked.Renderer(),
        highlight: function(code, lang) {
            // 적절한 언어로 코드 강조 처리
            if (Prism.languages[lang]) {
                return Prism.highlight(code, Prism.languages[lang], lang);
            } else {
                return code;
            }
        },
        pedantic: false,
        gfm: true,
        breaks: true,          // 여기가 중요: 일반 줄바꿈을 <br> 태그로 변환
        sanitize: false,
        smartypants: true,
        xhtml: false
    });

    // Mermaid 초기화
    mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
        flowchart: {
            useMaxWidth: false,
            htmlLabels: true
        }
    });
});

// 타이핑 효과 함수
function typeNextChunk() {
    if (typewriterQueue.length === 0) {
        isTyping = false;
        if (typingIndicator) {
            typingIndicator.remove();
            typingIndicator = null;
        }
        // 타이핑이 완료되면 마크다운을 HTML로 변환하여 표시
        renderMarkdown();
        return;
    }

    isTyping = true;
    const nextChunk = typewriterQueue.shift();

    // 원본 마크다운 텍스트 저장
    botMessageContent += nextChunk;

    // 실시간으로 마크다운 렌더링 (타이핑 중에도 마크다운 적용)
    renderMarkdownWithTypingIndicator();

    // 다음 청크 처리 예약
    setTimeout(typeNextChunk, typingSpeed * 2);
}

// 타이핑 중에도 마크다운 렌더링을 적용하는 함수
function renderMarkdownWithTypingIndicator() {
    if (botMessageContainer && botMessageContent) {
        // Marked.js를 사용하여 마크다운 텍스트를 HTML로 변환
        botMessageContainer.innerHTML = marked.parse(botMessageContent);

        // 타이핑 인디케이터 다시 추가
        if (typingIndicator) {
            botMessageContainer.appendChild(typingIndicator);
        }

        // 코드 블록 처리 - Prism.js의 자동 강조 적용
        Prism.highlightAllUnder(botMessageContainer);

        // 메시지 컨테이너 스크롤 자동화
        const messagesContainer = document.querySelector('.messages-container');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// 마크다운을 HTML로 변환하여 렌더링하는 함수 (최종)
function renderMarkdown() {
    if (botMessageContainer && botMessageContent) {
        // Marked.js를 사용하여 마크다운 텍스트를 HTML로 변환
        botMessageContainer.innerHTML = marked.parse(botMessageContent);

        // 코드 블록 처리 - Prism.js의 자동 강조 적용
        Prism.highlightAllUnder(botMessageContainer);

        // 코드 블록에 복사 버튼 추가
        addCopyButtonsToCodeBlocks(botMessageContainer);

        // 전체 메시지에 복사 버튼 추가
        addCopyButtonToMessage(botMessageContainer);

        // Mermaid 다이어그램 초기화
        mermaid.init(undefined, botMessageContainer.querySelectorAll('.mermaid'));

        // 메시지 컨테이너 스크롤 자동화
        const messagesContainer = document.querySelector('.messages-container');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// 타이핑 큐에 텍스트 추가
function addToTypingQueue(text) {
    // 텍스트를 한 글자씩 분할하지 않고, 단어나 문장 단위로 처리
    const chunks = [];
    const lines = text.split('\n');

    // 줄바꿈을 보존하기 위해 각 줄을 개별 청크로 처리
    for (let i = 0; i < lines.length; i++) {
        if (lines[i]) {
            // 줄바꿈이 아닌 경우, 단어 단위로 나누기
            const words = lines[i].match(/\S+|\s+/g) || [];
            chunks.push(...words);
        }
        // 줄바꿈 자체를 하나의 청크로 추가 (마지막 줄이 아닌 경우)
        if (i < lines.length - 1) {
            chunks.push('\n');
        }
    }

    typewriterQueue.push(...chunks);

    if (!isTyping) {
        typeNextChunk();
    }
}

function sendMessage() {
    const promptInput = document.getElementById('prompt');
    const prompt = promptInput.value;
    const session_id = document.getElementById('session_id').value;

    if (!prompt.trim()) return false;

    // 사용자 메시지 표시
    const userMessage = document.createElement('div');
    userMessage.classList.add('message', 'user-message');
    userMessage.textContent = prompt;
    document.getElementById('chat-messages').appendChild(userMessage);

    // 봇 메시지 컨테이너 생성
    botMessageContainer = document.createElement('div');
    botMessageContainer.classList.add('message', 'bot-message', 'markdown-body');
    document.getElementById('chat-messages').appendChild(botMessageContainer);

    // 타이핑 인디케이터 추가
    typingIndicator = document.createElement('span');
    typingIndicator.classList.add('typing-indicator');
    botMessageContainer.appendChild(typingIndicator);

    // 타이핑 큐 초기화
    typewriterQueue = [];
    botMessageContent = '';
    isTyping = false;

    // 스크롤 자동화
    const messagesContainer = document.querySelector('.messages-container');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // 폼 제출 - x-www-form-urlencoded 형식으로
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `prompt=${encodeURIComponent(prompt)}&session_id=${encodeURIComponent(session_id)}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP 오류: ${response.status}`);
        }
        return response.text();
    })
    .then(() => {
        console.log('메시지 전송 완료');

        // 이전 EventSource 닫기
        if (window.eventSource) {
            window.eventSource.close();
        }

        // 새 EventSource 생성
        window.eventSource = new EventSource(`/chat-stream?session_id=${encodeURIComponent(session_id)}`);

        window.eventSource.onmessage = function(event) {
            if (event.data === '[DONE]') {
                window.eventSource.close();
                // 메시지가 모두 수신되면 복사 버튼 추가
                addCopyButtonsToCodeBlocks(botMessageContainer);
                addCopyButtonToMessage(botMessageContainer);
        
                // 메시지 수신이 완료되면 mermaid 다이어그램 확인 및 처리
                setTimeout(function () {
                    detectAndHandleMermaid();
                }, 5000);
        
                return;
            }
    
            try {
                const data = JSON.parse(event.data);
                if (data.choices && data.choices.length > 0 && data.choices[0].delta &&
                    data.choices[0].delta.content !== undefined) {

                    const content = data.choices[0].delta.content;
                    // 타이핑 큐에 추가
                    addToTypingQueue(content);
                }
            } catch (e) {
                console.error('JSON 파싱 오류:', e, event.data);
            }
        };

        window.eventSource.onerror = function(error) {
            console.error('SSE 연결 오류:', error);
            if (typingIndicator) {
                typingIndicator.remove();
                typingIndicator = null;
            }
            // 에러 메시지는 즉시 표시
            botMessageContainer.textContent = '응답을 가져오는 중 오류가 발생했습니다. 다시 시도해주세요.';
            window.eventSource.close();
        };
    })
    .catch(error => {
        console.error('에러:', error);
        if (typingIndicator) {
            typingIndicator.remove();
            typingIndicator = null;
        }
        botMessageContainer.textContent = '메시지 전송 중 오류가 발생했습니다: ' + error.message;
    });

    promptInput.value = ''; // 입력 필드 비우기
    return false; // 기본 폼 제출 방지
}

// 페이지 로드 시 실행되는 함수
window.onload = function() {
    const promptInput = document.getElementById('prompt');
    const initialQuery = document.getElementById('initial_query').value;

    // 입력 필드에 포커스 설정
    promptInput.focus();

    // URL에서 q 파라미터를 확인
    if (initialQuery && initialQuery.trim() !== '') {
        console.log('URL에서 쿼리 파라미터 감지:', initialQuery);

        // 입력 필드에 쿼리 파라미터 값 설정
        promptInput.value = decodeURIComponent(initialQuery);

        // 약간의 지연 후 자동으로 폼 제출 (사용자에게 입력값이 보일 수 있도록)
        setTimeout(() => {
            sendMessage();
        }, 500);
    } else {
        // URL 파라미터 체크 (백엔드에서 전달하지 않은 경우 클라이언트에서 처리)
        const urlParams = new URLSearchParams(window.location.search);
        const queryParam = urlParams.get('q');

        if (queryParam) {
            console.log('URL에서 직접 쿼리 파라미터 감지:', queryParam);
            promptInput.value = decodeURIComponent(queryParam);

            // 약간의 지연 후 자동으로 폼 제출
            setTimeout(() => {
                sendMessage();
            }, 500);
        }
    }
};

// 기존 코드 블록에 복사 버튼 추가 - 페이지 로드 시
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        const botMessages = chatMessages.querySelectorAll('.bot-message');
        botMessages.forEach((messageContainer) => {
            addCopyButtonsToCodeBlocks(messageContainer);
            addCopyButtonToMessage(messageContainer);
        });
    }
});

/**
 * 메시지가 추가될 때 호출되는 함수
 */
function onMessageAdded() {
  // Prism.js로 코드 블록 구문 강조 적용
  Prism.highlightAll();
  
  // 코드 블록에 버튼 추가
  // addButtonsToCodeBlocks();
  
  // 마크다운 렌더링 완료 후 스크롤 조정
  scrollToBottom();
}

// Mermaid 다이어그램의 괄호 균형을 검사하고 수정하는 함수
function checkAndFixBracketBalance(diagram) {
    if (!diagram) return diagram;
    
    const lines = diagram.split('\n');
    const processedLines = [];
    
    // 각 줄마다 괄호 균형 확인
    for (let line of lines) {
        const stack = [];
        let fixedLine = '';
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '{' || char === '[' || char === '(') {
                // 여는 괄호면 스택에 추가
                stack.push(char);
                fixedLine += char;
            } else if (char === '}' || char === ']' || char === ')') {
                // 닫는 괄호 처리
                if (stack.length === 0) {
                    // 스택이 비어있으면 괄호가 짝이 맞지 않음 - 해당 괄호 무시
                    console.warn('Unmatched closing bracket:', char);
                    continue;
                }
                
                const lastBracket = stack.pop();
                const matchingCloseBracket = lastBracket === '{' ? '}' : (lastBracket === '[' ? ']' : ')');
                
                if (
                    (lastBracket === '{' && char === '}') ||
                    (lastBracket === '[' && char === ']') ||
                    (lastBracket === '(' && char === ')')
                ) {
                    // 괄호 짝이 맞으면 그대로 추가
                    fixedLine += char;
                } else {
                    // 괄호 짝이 맞지 않으면 올바른 괄호로 대체
                    console.warn(`Mismatched brackets: ${lastBracket} and ${char}. Replacing with ${matchingCloseBracket}`);
                    fixedLine += matchingCloseBracket;
                }
            } else {
                // 괄호가 아닌 문자는 그대로 추가
                fixedLine += char;
            }
        }
        
        // 줄 끝에 열린 괄호가 남아있으면 닫아줌
        while (stack.length > 0) {
            const lastBracket = stack.pop();
            const matchingCloseBracket = lastBracket === '{' ? '}' : (lastBracket === '[' ? ']' : ')');
            console.warn(`Unclosed bracket at end of line: ${lastBracket}. Adding ${matchingCloseBracket}`);
            fixedLine += matchingCloseBracket;
        }
        
        processedLines.push(fixedLine);
    }
    
    return processedLines.join('\n');
}