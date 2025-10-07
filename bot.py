import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import httpx
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()

# URL FastAPI сервера
API_BASE_URL = f"http://{os.getenv('FASTAPI_HOST', 'localhost')}:{os.getenv('FASTAPI_PORT', '8000')}"

# Хранилище состояний пользователей
user_data = {}

async def send_api_request(endpoint: str, method: str = "GET", data: dict = None, files: dict = None):
    """Вспомогательная функция для отправки запросов к API"""
    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                if files:
                    response = await client.post(url, files=files, data=data)
                else:
                    response = await client.post(url, json=data)
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP ошибка: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Ошибка при запросе к API: {str(e)}")
            return {"error": f"Ошибка соединения: {str(e)}"}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    welcome_text = """
🤖 Добро пожаловать в ResumeMate!

Я помогу вам:
• 📄 Проанализировать резюме и извлечь ключевые навыки
• 🔍 Найти подходящие вакансии
• 📧 Сгенерировать сопроводительные письма
• ⭐ Оценить готовность резюме к рынку труда

Используйте команды:
/resume - Загрузить и обработать резюме
/search - Найти вакансии

Для начала работы нажмите кнопку ниже:
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Загрузить резюме", callback_data="upload_resume")],
        [InlineKeyboardButton(text="🔍 Поиск вакансий", callback_data="search_jobs")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])

    await message.answer(welcome_text, reply_markup=keyboard)

@dp.message(Command("resume"))
async def cmd_resume(message: types.Message):
    """Обработка команды /resume"""
    user_id = message.from_user.id
    user_data[user_id] = {"awaiting_resume": True}

    await message.answer(
        "📄 Отправьте PDF или DOCX файл с вашим резюме.\n"
        "Я извлеку ключевые навыки и подготовлю анализ."
    )

@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    """Обработка команды /search"""
    # Показываем первую вакансию
    await show_job(message, 0)

async def show_job(message: types.Message, job_index: int = 0):
    """Показать одну вакансию"""
    try:
        from jobs import JobSearchService

        job_service = JobSearchService()
        jobs = await job_service.get_sample_jobs()

        if job_index >= len(jobs):
            await message.answer("❌ Больше вакансий нет")
            return

        job = jobs[job_index]

        # Проверяем, есть ли еще вакансии
        has_next = job_index + 1 < len(jobs)
        has_prev = job_index > 0

        job_text = f"""
🔍 Вакансия {job_index + 1} из {len(jobs)}

🏢 {job['title']}
🏢 {job['company']}
📍 {job['location']}
💰 {job['salary']}
⭐ Match: {job['match_score']}%

Обязанности:
• Разработка веб-приложений на Python/Django
• Работа с базами данных PostgreSQL
• Командная разработка

Требования:
• Опыт с Python 3+ лет
• Знание Django/Flask
• Опыт работы с базами данных
        """

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Откликнуться", callback_data=f"apply_job_{job_index}"),
                InlineKeyboardButton(text="❌ Пропустить", callback_data=f"skip_job_{job_index}")
            ]
        ])

        # Добавляем кнопки навигации
        nav_buttons = []
        if has_prev:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Предыдущая", callback_data=f"prev_job_{job_index}"))
        if has_next:
            nav_buttons.append(InlineKeyboardButton(text="➡️ Следующая", callback_data=f"next_job_{job_index}"))

        if nav_buttons:
            keyboard.inline_keyboard.append(nav_buttons)

        # Добавляем кнопку главного меню
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ])

        await message.answer(job_text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при показе вакансии: {str(e)}")
        await message.answer(
            "❌ Произошла ошибка при загрузке вакансий.\n"
            "Попробуйте еще раз или обратитесь в поддержку."
        )

@dp.callback_query()
async def handle_callbacks(callback: CallbackQuery):
    """Обработка нажатий на кнопки"""
    user_id = callback.from_user.id
    data = callback.data

    if data == "upload_resume":
        user_data[user_id] = {"awaiting_resume": True}
        await callback.message.answer(
            "📄 Отправьте PDF или DOCX файл с вашим резюме.\n"
            "Я извлеку ключевые навыки и подготовлю анализ."
        )

    elif data == "search_jobs":
        await show_job(callback.message, 0)

    elif data == "help":
        help_text = """
📋 Помощь по командам:

/start - Запуск бота и главное меню
/resume - Загрузить резюме для анализа
/search - Поиск вакансий

🔧 Возможности бота:
• Анализ PDF/DOCX резюме
• Извлечение ключевых навыков
• Поиск вакансий с match-score
• Генерация сопроводительных писем
• Аудит готовности резюме

📞 Поддержка: @c4soto
        """
        await callback.message.answer(help_text)

    elif data == "main_menu":
        await cmd_start(callback.message)

    elif data.startswith("next_job_"):
        current_index = int(data.split("_")[-1])
        await show_job(callback.message, current_index + 1)

    elif data.startswith("prev_job_"):
        current_index = int(data.split("_")[-1])
        await show_job(callback.message, current_index - 1)

    elif data.startswith("apply_job_"):
        job_index = int(data.split("_")[-1])
        from jobs import JobSearchService
        job_service = JobSearchService()
        jobs = await job_service.get_sample_jobs()
        job = jobs[job_index]

        await callback.message.answer(
            f"📝 Генерация сопроводительного письма для вакансии:\n\n"
            f"🏢 {job['title']}\n"
            f"🏢 {job['company']}\n\n"
            "Это демо-функция. В реальной версии здесь будет:\n"
            "• Персонализированное сопроводительное письмо\n"
            "• Заполнение формы отклика\n"
            "• Отправка через API HH.ru или email"
        )

    elif data.startswith("skip_job_"):
        job_index = int(data.split("_")[-1])
        from jobs import JobSearchService
        job_service = JobSearchService()
        jobs = await job_service.get_sample_jobs()
        job = jobs[job_index]

        await callback.message.answer(
            f"❌ Вакансия пропущена:\n"
            f"🏢 {job['title']} - {job['company']}\n\n"
            "Показать следующую вакансию?"
        )

    await callback.answer()

@dp.message()
async def handle_files(message: types.Message):
    """Обработка загруженных файлов"""
    user_id = message.from_user.id

    # Проверяем, ожидает ли пользователь загрузки резюме
    if user_data.get(user_id, {}).get("awaiting_resume"):
        if message.document:
            # Получаем информацию о файле
            file = message.document

            # Проверяем тип файла
            if not (file.mime_type in ['application/pdf'] or
                   file.file_name.lower().endswith(('.pdf', '.docx', '.doc'))):
                await message.answer(
                    "❌ Поддерживаются только PDF и DOCX файлы.\n"
                    "Пожалуйста, загрузите резюме в правильном формате."
                )
                return

            try:
                # Получаем файл от Telegram
                file_info = await bot.get_file(file.file_id)
                file_path = file_info.file_path

                # Загружаем файл локально для отправки в API
                await bot.download_file(file_path, f"temp_{file.file_id}")

                # Отправляем файл в наш API
                with open(f"temp_{file.file_id}", 'rb') as f:
                    files = {'file': (file.file_name, f, file.mime_type)}

                    api_response = await send_api_request("/upload-resume", "POST", files=files)

                # Удаляем временный файл
                if os.path.exists(f"temp_{file.file_id}"):
                    os.remove(f"temp_{file.file_id}")

                if "error" in api_response:
                    await message.answer(
                        f"❌ Ошибка при обработке резюме: {api_response['error']}\n"
                        "Попробуйте еще раз или обратитесь в поддержку."
                    )
                else:
                    # Показываем результаты анализа
                    skills = api_response.get('skills', [])
                    resume_id = api_response.get('resume_id')

                    response_text = f"""
✅ Резюме успешно обработано!

📊 Найденные навыки ({len(skills)}):
{', '.join(skills[:10])}

{'...' if len(skills) > 10 else ''}

🔍 Что дальше?
Теперь вы можете использовать команду /search для поиска вакансий,
которые соответствуют вашим навыкам.

ID резюме: {resume_id}
                    """

                    await message.answer(response_text)

                    # Сбрасываем состояние ожидания
                    user_data[user_id] = {"resume_id": resume_id}

            except Exception as e:
                logger.error(f"Ошибка при обработке файла: {str(e)}")
                await message.answer(
                    "❌ Произошла ошибка при обработке файла.\n"
                    "Попробуйте еще раз или обратитесь в поддержку."
                )

        else:
            await message.answer(
                "📄 Пожалуйста, загрузите файл резюме (PDF или DOCX).\n"
                "Используйте команду /resume для начала процесса."
            )

async def main():
    """Запуск бота"""
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
