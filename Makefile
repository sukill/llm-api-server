.PHONY: help install run dev clean

# Variables
UV = uv
VENV = .venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python
UVICORN = $(BIN)/uvicorn
RUFF = $(BIN)/ruff

APP = app.main:app
HOST = 0.0.0.0
PORT = 8000

help: ## 도움말 표시
	@grep -E '^[a-zA- activism.Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 의존성 설치 및 가상환경 설정
	$(UV) sync

run: ## 프로덕션 모드로 서버 실행
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT)

dev: ## 개발 모드로 서버 실행 (Hot Reload)
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT) --reload

clean: ## 캐시 및 가상환경 제거
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

setup: install ## 초기 설정 (install과 동일)

lint: ## 코드 스타일 검사 및 포맷팅 (ruff)
	$(RUFF) format .
	$(RUFF) check --fix .

test: ## 테스트 실행 (pytest가 설치되어 있어야 함)
	$(BIN)/pytest
