#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота
"""

import asyncio
import sys
from bot import main

if __name__ == "__main__":
    print("🤖 Запуск Telegram бота ResumeMate...")
    print("📋 Убедитесь, что:")
    print("   • Создан файл .env с токеном бота")
    print("   • FastAPI сервер запущен на указанном порту")
    print("   • Все зависимости установлены")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {str(e)}")
        sys.exit(1)
