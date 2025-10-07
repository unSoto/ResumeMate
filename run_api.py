#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера
"""

import uvicorn
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("FASTAPI_HOST", "localhost")
    port = int(os.getenv("FASTAPI_PORT", "8000"))

    print(f"🚀 Запуск FastAPI сервера на {host}:{port}")
    print("📖 Документация API будет доступна по адресу: http://localhost:8000/docs")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        access_log=True
    )
