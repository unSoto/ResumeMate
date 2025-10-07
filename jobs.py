import httpx
import asyncio
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class JobSearchService:
    """Сервис для поиска вакансий"""

    def __init__(self):
        self.hh_api_token = os.getenv('HH_API_TOKEN')
        self.base_url = "https://api.hh.ru"

    async def search_jobs_hh(self, skills: List[str], limit: int = 10) -> List[Dict]:
        """Поиск вакансий на HeadHunter"""
        jobs = []

        # Создаем поисковый запрос из навыков
        search_query = " ".join(skills[:5])  # Берем первые 5 навыков

        headers = {}
        if self.hh_api_token:
            headers['Authorization'] = f'Bearer {self.hh_api_token}'

        params = {
            'text': search_query,
            'per_page': min(limit, 50),
            'order_by': 'relevance'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/vacancies",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get('items', []):
                    job = {
                        'id': item['id'],
                        'title': item['name'],
                        'company': item['employer']['name'],
                        'location': item.get('area', {}).get('name', 'Не указан'),
                        'remote': 'удаленно' in item['name'].lower() or 'remote' in item['name'].lower(),
                        'salary': self._format_salary(item.get('salary')),
                        'url': item['alternate_url'],
                        'requirements': item.get('snippet', {}).get('requirement', ''),
                        'match_score': self._calculate_match_score(skills, item)
                    }
                    jobs.append(job)

        except Exception as e:
            print(f"Ошибка при поиске вакансий на HH: {str(e)}")

        return jobs

    def _format_salary(self, salary_data: Optional[Dict]) -> str:
        """Форматирование зарплаты"""
        if not salary_data:
            return "Не указана"

        salary_from = salary_data.get('from')
        salary_to = salary_data.get('to')
        currency = salary_data.get('currency', 'RUB')

        if salary_from and salary_to:
            return f"{salary_from:,} - {salary_to:,} {currency}"
        elif salary_from:
            return f"от {salary_from:,} {currency}"
        elif salary_to:
            return f"до {salary_to:,} {currency}"

        return "Не указана"

    def _calculate_match_score(self, user_skills: List[str], job_data: Dict) -> int:
        """Расчет match score между навыками пользователя и вакансией"""
        # Простая эвристика для демо
        # В реальности можно использовать более сложные алгоритмы

        job_text = (job_data.get('name', '') + ' ' +
                   job_data.get('snippet', {}).get('requirement', '')).lower()

        matches = 0
        for skill in user_skills:
            if skill.lower() in job_text:
                matches += 1

        # Возвращаем score от 0 до 100
        max_possible_matches = min(len(user_skills), 10)  # Максимум 10 совпадений
        score = int((matches / max_possible_matches) * 100) if max_possible_matches > 0 else 0

        return min(score, 100)

    async def get_sample_jobs(self) -> List[Dict]:
        """Получить примеры вакансий для демо"""
        return [
            {
                'id': 'sample_1',
                'title': 'Senior Python Developer',
                'company': 'TechCorp Inc.',
                'location': 'Москва',
                'remote': True,
                'salary': '200,000 - 300,000 ₽',
                'url': 'https://example.com/job1',
                'requirements': 'Python, Django, PostgreSQL, опыт 3+ лет',
                'match_score': 95
            },
            {
                'id': 'sample_2',
                'title': 'Full Stack Developer',
                'company': 'Digital Solutions',
                'location': 'Санкт-Петербург',
                'remote': False,
                'salary': '150,000 - 250,000 ₽',
                'url': 'https://example.com/job2',
                'requirements': 'React, Node.js, опыт работы с API',
                'match_score': 87
            },
            {
                'id': 'sample_3',
                'title': 'Data Scientist',
                'company': 'Analytics Pro',
                'location': 'Москва',
                'remote': False,
                'salary': '180,000 - 280,000 ₽',
                'url': 'https://example.com/job3',
                'requirements': 'Python, SQL, анализ данных, визуализация',
                'match_score': 82
            }
        ]

    async def search_jobs(self, skills: List[str], use_real_api: bool = False) -> List[Dict]:
        """Основной метод поиска вакансий"""
        if use_real_api and self.hh_api_token:
            return await self.search_jobs_hh(skills)
        else:
            return await self.get_sample_jobs()

class CoverLetterGenerator:
    """Генератор сопроводительных писем"""

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

    async def generate_cover_letter(self, resume_text: str, job_data: Dict) -> str:
        """Генерация сопроводительного письма"""

        if self.openai_api_key:
            return await self._generate_with_ai(resume_text, job_data)
        else:
            return self._generate_template(resume_text, job_data)

    def _generate_template(self, resume_text: str, job_data: Dict) -> str:
        """Генерация шаблонного сопроводительного письма"""

        template = f"""
Уважаемые коллеги!

Меня заинтересовала вакансия {job_data['title']} в компании {job_data['company']}.

На основе моего опыта и навыков, я уверен, что могу внести значительный вклад в вашу команду.
Ключевые навыки, релевантные для этой позиции:
• Навыки из резюме будут добавлены здесь

Готов обсудить детали сотрудничества и ответить на все интересующие вопросы.

С уважением,
[Ваше имя]
        """

        return template

    async def _generate_with_ai(self, resume_text: str, job_data: Dict) -> str:
        """Генерация сопроводительного письма с помощью AI"""
        # Здесь будет интеграция с OpenAI
        # Пока возвращаем шаблон
        return self._generate_template(resume_text, job_data)

class ResumeAuditService:
    """Сервис аудита резюме"""

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

    async def audit_resume(self, resume_text: str, skills: List[str]) -> Dict:
        """Аудит резюме и оценка готовности к рынку"""

        # Простая эвристика для оценки
        score = self._calculate_readiness_score(resume_text, skills)

        recommendations = self._generate_recommendations(resume_text, skills)

        return {
            'overall_score': score,
            'grade': self._get_grade(score),
            'recommendations': recommendations,
            'skills_count': len(skills),
            'text_length': len(resume_text)
        }

    def _calculate_readiness_score(self, resume_text: str, skills: List[str]) -> int:
        """Расчет общей готовности резюме"""
        score = 50  # Базовый score

        # Длина резюме
        if len(resume_text) > 1000:
            score += 15
        elif len(resume_text) > 500:
            score += 10

        # Количество навыков
        if len(skills) >= 10:
            score += 20
        elif len(skills) >= 5:
            score += 10

        # Проверка ключевых разделов
        sections = ['опыт', 'образование', 'навыки', 'контакты']
        found_sections = sum(1 for section in sections if section in resume_text.lower())
        score += found_sections * 3

        return min(score, 100)

    def _get_grade(self, score: int) -> str:
        """Получение буквенной оценки"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'E'

    def _generate_recommendations(self, resume_text: str, skills: List[str]) -> List[str]:
        """Генерация рекомендаций по улучшению резюме"""
        recommendations = []

        if len(resume_text) < 500:
            recommendations.append("📝 Добавьте больше деталей в описание опыта работы")

        if len(skills) < 5:
            recommendations.append("🎯 Укажите больше технических навыков")

        if 'опыт' not in resume_text.lower():
            recommendations.append("💼 Добавьте раздел с опытом работы")

        if 'образование' not in resume_text.lower():
            recommendations.append("🎓 Добавьте информацию об образовании")

        if 'контакт' not in resume_text.lower():
            recommendations.append("📞 Укажите контактную информацию")

        if not recommendations:
            recommendations.append("✅ Резюме выглядит хорошо!")

        return recommendations
