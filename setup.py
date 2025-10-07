#!/usr/bin/env python3
"""
Скрипт настройки проекта ResumeMate
"""

import os
import sys
import subprocess
import venv
from pathlib import Path

def print_header():
    """Вывод заголовка"""
    print("🤖 ResumeMate Setup")
    print("=" * 50)

def check_python_version():
    """Проверка версии Python"""
    print("🔍 Проверка версии Python...")

    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {sys.version}")
        return False

    print(f"✅ Python {sys.version.split()[0]}")
    return True

def create_venv():
    """Создание виртуального окружения"""
    print("🏗️ Создание виртуального окружения...")

    venv_path = Path("venv")

    if venv_path.exists():
        print("✅ Виртуальное окружение уже существует")
        return True

    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Виртуальное окружение создано")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании виртуального окружения: {e}")
        return False

def activate_venv():
    """Активация виртуального окружения"""
    venv_path = Path("venv")

    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/MacOS
        activate_script = venv_path / "bin" / "activate"
        python_executable = venv_path / "bin" / "python"

    if python_executable.exists():
        os.environ["PATH"] = f"{python_executable.parent}{os.pathsep}{os.environ['PATH']}"
        return True

    return False

def install_dependencies():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

        print("✅ Зависимости установлены")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False
    except FileNotFoundError:
        print("❌ Файл requirements.txt не найден")
        return False

def create_env_file():
    """Создание файла .env"""
    print("⚙️ Настройка конфигурации...")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        print("✅ Файл .env уже существует")
        return True

    if not env_example.exists():
        print("❌ Файл .env.example не найден")
        return False

    try:
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ Файл .env создан из шаблона")
        print("⚠️ Не забудьте заполнить TELEGRAM_BOT_TOKEN в файле .env")
        return True

    except Exception as e:
        print(f"❌ Ошибка при создании .env файла: {e}")
        return False

def check_directories():
    """Создание необходимых директорий"""
    print("📁 Создание директорий...")

    dirs = ["uploads"]

    for dir_name in dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)

        # Создаем .gitkeep файл
        gitkeep = dir_path / ".gitkeep"
        gitkeep.touch(exist_ok=True)

    print("✅ Директории созданы")
    return True

def run_tests():
    """Запуск базовых тестов"""
    print("🧪 Запуск тестов...")

    try:
        # Тест импорта основных модулей
        import fastapi
        import aiogram
        import PyPDF2
        import docx

        print("✅ Все основные модули импортированы успешно")
        return True

    except ImportError as e:
        print(f"❌ Ошибка импорта модулей: {e}")
        return False

def print_success():
    """Вывод сообщения об успешной настройке"""
    print("\n🎉 Настройка завершена успешно!")
    print("\n📋 Следующие шаги:")
    print("1. Получите токен бота у @BotFather в Telegram")
    print("2. Заполните .env файл:")
    print("   - TELEGRAM_BOT_TOKEN=ваш_токен")
    print("3. Запустите сервер: python run_api.py")
    print("4. В новом терминале запустите бота: python run_bot.py")
    print("\n📖 Подробная документация в README.md")

def main():
    """Главная функция"""
    print_header()

    steps = [
        ("Проверка Python версии", check_python_version),
        ("Создание виртуального окружения", create_venv),
        ("Установка зависимостей", install_dependencies),
        ("Создание .env файла", create_env_file),
        ("Создание директорий", check_directories),
        ("Запуск тестов", run_tests),
    ]

    success = True

    for step_name, step_func in steps:
        print(f"\n📌 {step_name}")
        if not step_func():
            success = False
            print(f"❌ Шаг '{step_name}' не выполнен")

    if success:
        print_success()
    else:
        print("\n❌ Настройка завершена с ошибками")
        print("📞 Обратитесь к документации в README.md")
        sys.exit(1)

if __name__ == "__main__":
    main()
