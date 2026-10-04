#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

wait_service() {
    for attempt in {1..15}; do
        if curl -fsS --max-time 5 "$1" >/dev/null 2>&1; then return; fi
        sleep 2
    done
    echo "服务未就绪：$1，请检查日志" >&2
    return 1
}

cd "$PROJECT_DIR"
case "${1:-docker}" in
    docker)
        if [ ! -f "$BACKEND_DIR/.env.production" ]; then
            cp "$BACKEND_DIR/.env.production.example" "$BACKEND_DIR/.env.production"
            echo '已复制生产配置模板，模型功能可稍后配置。'
        fi
        if docker compose version >/dev/null 2>&1; then
            docker compose up -d --build
        else
            docker-compose up -d --build
        fi
        wait_service http://localhost:8000/health
        wait_service http://localhost/
        echo '服务已启动：http://localhost'
        ;;
    local)
        if command -v python3 >/dev/null; then PYTHON_CMD=python3; else PYTHON_CMD=python; fi
        [ -d "$BACKEND_DIR/.venv" ] || "$PYTHON_CMD" -m venv "$BACKEND_DIR/.venv"
        PYTHON_PATH="$BACKEND_DIR/.venv/bin/python"
        "$PYTHON_PATH" -m pip install -r "$BACKEND_DIR/requirements.txt"
        [ -f "$BACKEND_DIR/.env" ] || cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        "$PYTHON_PATH" -m playwright install chromium
        "$PYTHON_PATH" "$BACKEND_DIR/init_data.py"
        cd "$FRONTEND_DIR"
        npm ci
        npm run build
        mkdir -p "$BACKEND_DIR/logs"
        cd "$BACKEND_DIR"
        nohup "$PYTHON_PATH" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 >logs/backend-output.log 2>&1 &
        BACKEND_PID=$!
        wait_service http://localhost:8000/health
        cd "$FRONTEND_DIR"
        nohup npm run preview -- --host 127.0.0.1 --port 4173 --strictPort >"$BACKEND_DIR/logs/frontend-output.log" 2>&1 &
        FRONTEND_PID=$!
        wait_service http://localhost:4173/
        echo "服务已启动：http://localhost:4173；后端进程 $BACKEND_PID，前端进程 $FRONTEND_PID"
        ;;
    *)
        echo '用法：bash deploy.sh [docker|local]' >&2
        exit 1
        ;;
esac
