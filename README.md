# MLX FastAPI Serving Server

Apple Silicon(Mac)에서 `MLX` 프레임워크를 사용하여 LLM을 서빙하는 FastAPI 서버입니다. `uv`를 사용하여 패키지를 관리합니다.

## Prerequisites

- **Mac with Apple Silicon** (M1, M2, M3 등)
- [uv](https://github.com/astral-sh/uv) 설치됨

## 설치 및 실행

1. **저장소 클론 및 패키지 설치**

```bash
# 의존성 설치 및 가상환경 설정
uv sync
```

2. **서버 실행**

```bash
# 서버 실행 (기본 모델: Llama-3-8B-Instruct-4bit)
uv run uvicorn app.main:app --reload
```

## API 사용법

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Chat Completions (OpenAI 호환)
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "안녕하세요, MLX에 대해 설명해주세요."}
    ],
    "stream": false
  }'
```

### 3. Streaming 지원
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "1부터 10까지 세어줘."}
    ],
    "stream": true
  }'
```

## 설정

`.env` 파일을 수정하여 설정을 변경할 수 있습니다:

```env
MODEL_PATH=mlx-community/Meta-Llama-3-8B-Instruct-4bit
PORT=8000
HOST=0.0.0.0
HF_TOKEN=your_huggingface_token_here
```

> [!IMPORTANT]
> **Llama 3**와 같은 모델은 Hugging Face에서 [gated access] 승인이 필요합니다.
> 1. Hugging Face에서 해당 모델 사용 승인을 신청하세요.
> 2. [Settings > Access Tokens](https://huggingface.co/settings/tokens)에서 Token을 생성하세요.
> 3. `.env` 파일의 `HF_TOKEN` 항목에 해당 토큰을 입력하세요.

## 주요 의존성
- `mlx`: Apple Silicon을 위한 배열 연산 프레임워크
- `mlx-lm`: MLX를 이용한 LLM 로딩 및 생성 도구
- `fastapi`: API 서빙용 프레임워크
- `uvicorn`: ASGI 서버