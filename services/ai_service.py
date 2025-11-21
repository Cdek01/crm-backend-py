# services/ai_service.py
from openai import AsyncOpenAI  # <-- ИМПОРТИРУЕМ АСИНХРОННЫЙ КЛИЕНТ
from core.config import settings
from db import models
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, current_user: models.User):
        self.user = current_user
        # --- ИЗМЕНЕНИЕ: Создаем АСИНХРОННЫЙ клиент ---
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )

    # --- ИЗМЕНЕНИЕ: Метод теперь async ---
    async def parse_natural_language_to_filter(self, query: str, table_schema: List[Dict[str, Any]]) -> List[
        Dict[str, Any]]:
        """
        Преобразует текстовый запрос в JSON-фильтр для API с помощью DeepSeek.
        """
        system_prompt = f"""
        Твоя задача - преобразовать текст пользователя в JSON-фильтр.
        Действуй строго по правилам. Не добавляй никаких пояснений.
        Твой ответ - это всегда ТОЛЬКО JSON-массив.

        Схема доступных полей:
        {json.dumps(table_schema, indent=2, ensure_ascii=False)}

        Доступные операторы (op):
        - для текста: "contains", "eq"
        - для чисел: "eq", "gt", "lt", "gte", "lte"
        - для дат: "is", "is_not", "is_after", "is_before"
        - специальные значения для дат: "today", "yesterday", "one_week_ago"

        Пример запроса: "новые сделки ивана на сумму больше 10000"
        Твой JSON-ответ:
        [
          {{"field": "status", "op": "eq", "value": "Новая"}},
          {{"field": "manager", "op": "contains", "value": "иван"}},
          {{"field": "amount", "op": "gt", "value": 10000}}
        ]
        """
        user_prompt = f'Запрос пользователя: "{query}"'

        try:
            logger.info("-> Отправка ASYNC запроса в DeepSeek API...")
            # --- ИЗМЕНЕНИЕ: Используем await ---
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_tokens=1000,
            )

            if not response.choices:
                raise ValueError("DeepSeek API вернул пустой ответ в 'choices'")

            json_response_text = response.choices[0].message.content
            logger.info(f"<- Получен сырой ответ от DeepSeek: {json_response_text}")

            json_start = json_response_text.find('[')
            json_end = json_response_text.rfind(']') + 1
            if json_start == -1 or json_end == -1:
                raise ValueError("Не удалось найти JSON-массив в ответе модели")

            json_string = json_response_text[json_start:json_end]
            filters = json.loads(json_string)

            if isinstance(filters, list):
                logger.info(f"<- Успешно распарсен JSON: {filters}")
                return filters

            logger.warning("-> Ответ модели не является списком после парсинга.")
            return []

        except Exception as e:
            logger.error(f"!!! Ошибка при работе с AI моделью DeepSeek: {e}", exc_info=True)
            return []

        # --- НАЧАЛО: Добавьте этот новый метод в класс AIService ---

    async def generate_dashboard_summary(self, aggregated_data: dict) -> str:
        """
        Генерирует текстовую аналитическую сводку по агрегированным данным.
        """
        data_json = json.dumps(aggregated_data, indent=2, ensure_ascii=False)

        system_prompt = f"""
         Ты — опытный бизнес-аналитик, который готовит краткую ежедневную сводку для руководителя компании.
         Твоя задача — проанализировать предоставленные JSON-данные и написать понятный, лаконичный отчет на русском языке.
         Говори как эксперт: четко, по делу, подсвечивая самое важное. Не используй общие фразы.

         Структура твоего отчета должна быть такой:
         1.  **Финансы:** Сначала главный вывод о денежном потоке (положительный или отрицательный). Затем укажи на 1-2 самые крупные операции, которые на это повлияли.
         2.  **Клиентская активность:** Свяжи финансовые данные с активностью по звонкам. Сделай предположение о связи между звонками и деньгами.
         3.  **Внутренняя эффективность:** Упомяни общую активность колл-центра и выдели самого активного сотрудника.

         Анализируй эти данные:
         {data_json}

         Твой ответ — это только текст отчета, без заголовков "Отчет" или "Анализ". Начни сразу с сути.
         """

        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": system_prompt}],
                temperature=0.5,
                max_tokens=500,
            )

            summary = response.choices[0].message.content
            return summary.strip()

        except Exception as e:
            logger.error(f"Ошибка при генерации AI-сводки: {e}", exc_info=True)
            return "Не удалось сгенерировать аналитическую сводку. Пожалуйста, проверьте данные."
    # --- КОНЕЦ ---