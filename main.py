from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import PyPDF2
import docx
import re
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ResumeMate API", description="API для обработки резюме и поиска вакансий")

# Хранилище для загруженных резюме (в продакшене лучше использовать базу данных)
resumes_storage = {}

def extract_text_from_pdf(file_path: str) -> str:
    """Извлечение текста из PDF файла"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обработке PDF: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    """Извлечение текста из DOCX файла"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обработке DOCX: {str(e)}")

def extract_skills_from_text(text: str) -> List[str]:
    """Извлечение ключевых навыков из текста резюме"""
    # Расширенный список технических навыков
    technical_skills = {
        # Программирование
        'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
        'typescript', 'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'laravel',
        'html', 'css', 'sass', 'scss', 'bootstrap', 'tailwind',

        # Базы данных
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',

        # DevOps и инструменты
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'gitlab', 'github', 'git',
        'linux', 'nginx', 'apache', 'terraform', 'ansible',

        # Анализ данных
        'pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn', 'tensorflow', 'pytorch',
        'jupyter', 'tableau', 'power bi', 'excel',

        # Мобильная разработка
        'android', 'ios', 'flutter', 'react native', 'xamarin',

        # Тестирование
        'selenium', 'pytest', 'junit', 'testng', 'cypress', 'jest',

        # Дизайн
        'figma', 'photoshop', 'illustrator', 'adobe xd', 'sketch',

        # Маркетинг и аналитика
        'google analytics', 'yandex metrika', 'seo', 'sem', 'smm', 'crm',

        # Управление проектами
        'agile', 'scrum', 'kanban', 'jira', 'confluence', 'trello'
    }

    found_skills = []
    text_lower = text.lower()

    # Поиск технических навыков с более точным сопоставлением
    for skill in technical_skills:
        # Используем word boundaries для более точного поиска
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill.title())

    # Поиск опыта работы (только разумные цифры)
    experience_patterns = [
        r'(\d+)\s*(?:год|года|лет)\s*(?:опыта|стажа)',
        r'опыт\s*(?:работы\s*)?(\d+)\s*(?:год|года|лет)',
        r'стаж\s*(\d+)\s*(?:год|года|лет)'
    ]

    experience_years = []
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            years = int(match)
            if 1 <= years <= 50:  # Разумный диапазон опыта
                experience_years.append(str(years))

    if experience_years:
        found_skills.append(f"Опыт: {', '.join(set(experience_years))} лет")

    # Удаляем дубликаты и сортируем
    unique_skills = list(set(found_skills))
    unique_skills.sort(key=lambda x: len(x), reverse=True)  # Длинные названия первыми

    return unique_skills

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Загрузка и обработка резюме"""
    try:
        # Создаем директорию для загрузок если её нет
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Сохраняем файл
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Извлекаем текст в зависимости от типа файла
        if file.filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file.filename.lower().endswith(('.docx', '.doc')):
            text = extract_text_from_docx(file_path)
        else:
            raise HTTPException(status_code=400, detail="Поддерживаются только PDF и DOCX файлы")

        # Извлекаем навыки
        skills = extract_skills_from_text(text)

        # Сохраняем в хранилище
        resume_id = f"resume_{len(resumes_storage) + 1}"
        resumes_storage[resume_id] = {
            "text": text,
            "skills": skills,
            "filename": file.filename
        }

        # Удаляем файл после обработки
        os.remove(file_path)

        return {
            "resume_id": resume_id,
            "skills": skills,
            "text_length": len(text),
            "message": "Резюме успешно обработано"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")

@app.post("/extract-skills")
async def extract_skills(data: dict):
    """Извлечение навыков из текста резюме"""
    try:
        text = data.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Текст резюме обязателен")

        skills = extract_skills_from_text(text)

        return {
            "skills": skills,
            "count": len(skills)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении навыков: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "healthy", "service": "ResumeMate API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
