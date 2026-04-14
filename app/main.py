import os
import json
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import mlx.core as mx
from dotenv import load_dotenv

from mlx_lm import load
from mlx_lm.generate import generate_step

# Load environment variables from .env
load_dotenv()


# Global instances for model and tokenizer
class ModelState:
    model = None
    tokenizer = None


model_state = ModelState()


# Request/Response Models
class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stream: bool = False


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stream: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load the model on startup.
    By default, it uses a small model for demonstration.
    """
    model_path = os.getenv("MODEL_PATH", "mlx-community/Meta-Llama-3-8B-Instruct-4bit")
    print(f"🚀 Initializing MLX Model: {model_path}")

    try:
        # Load the model and tokenizer
        model_state.model, model_state.tokenizer = load(model_path)
        print("✅ Model loaded and ready for inference.")
    except Exception as e:
        print(f"❌ Failed to load model: {str(e)}")
        # We don't raise here to allow the server to start (maybe for health checks)

    yield
    print("💤 Shutting down server...")


app = FastAPI(
    title="MLX LLM Serving API",
    description="A lightweight FastAPI wrapper for serving LLMs using Apple's MLX framework.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": model_state.model is not None,
        "device": "apple_silicon (mlx)",
    }


@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    if not model_state.model:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    if request.stream:

        async def stream_generator():
            # Tokenize the prompt
            prompt_tokens = mx.array(model_state.tokenizer.encode(request.prompt))

            # For streaming in MLX-LM
            for response in generate_step(
                prompt_tokens,
                model_state.model,
            ):
                token, _ = response
                text = model_state.tokenizer.decode([token])
                yield f"data: {json.dumps({'text': text})}\n\n"

                # Check for EOS
                if token == model_state.tokenizer.eos_token_id:
                    break

            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # Custom non-streaming generation loop to avoid library bugs
        prompt_tokens = mx.array(model_state.tokenizer.encode(request.prompt))
        tokens = []
        for response in generate_step(
            prompt_tokens,
            model_state.model,
        ):
            token, _ = response
            if token == model_state.tokenizer.eos_token_id:
                break
            tokens.append(token)
            if len(tokens) >= request.max_tokens:
                break

        response_text = model_state.tokenizer.decode(tokens)
        return {"text": response_text}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if not model_state.model or not model_state.tokenizer:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    # Apply chat template
    prompt = model_state.tokenizer.apply_chat_template(
        [m.model_dump() for m in request.messages],
        tokenize=False,
        add_generation_prompt=True,
    )

    if request.stream:

        async def stream_generator():
            # Tokenize the prompt
            prompt_tokens = mx.array(model_state.tokenizer.encode(prompt))

            for response in generate_step(
                prompt_tokens,
                model_state.model,
            ):
                token, _ = response
                text = model_state.tokenizer.decode([token])

                chunk = {
                    "choices": [{"delta": {"content": text}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(chunk)}\n\n"

                if token == model_state.tokenizer.eos_token_id:
                    break

            yield f"data: {json.dumps({'choices': [{'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # Custom non-streaming generation loop
        prompt_tokens = mx.array(model_state.tokenizer.encode(prompt))
        tokens = []
        for response in generate_step(
            prompt_tokens,
            model_state.model,
        ):
            token, _ = response
            if token == model_state.tokenizer.eos_token_id:
                break
            tokens.append(token)
            if len(tokens) >= request.max_tokens:
                break

        response_text = model_state.tokenizer.decode(tokens)
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop",
                }
            ]
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
