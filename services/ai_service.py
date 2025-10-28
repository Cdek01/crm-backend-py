# services/ai_service.py
from openai import OpenAI
from core.config import settings
from db import models
from typing import List, Dict, Any
import json


class AIService:
    def __init__(self, current_user: models.User):
        self.user = current_user
        # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
        # Инициализируем клиент OpenAI, но указываем URL и ключ от DeepSeek
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        # ------------------------

    def parse_natural_language_to_filter(self, query: str, table_schema: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Преобразует текстовый запрос в JSON-фильтр для API с помощью DeepSeek.
        """

        # --- ПРОМПТ ОСТАЕТСЯ ПОЧТИ ТАКИМ ЖЕ ---
        # Мы просто делаем его более формальным для чат-модели
        system_prompt = f"""
        Ты — AI-ассистент, встроенный в CRM. Твоя задача — преобразовать запрос пользователя на естественном языке в JSON-массив фильтров.

        Вот схема колонок таблицы, с которой работает пользователь:
        {json.dumps(table_schema, indent=2, ensure_ascii=False)}

        Правила:
        1. Используй системные имена (`name`) для поля "field".
        2. Для текстового поиска используй оператор "contains".
        3. Для точного совпадения (например, статус "новый") используй оператор "eq".
        4. Для дат используй специальные значения: 'today', 'yesterday', 'one_week_ago'.
        5. Если пользователь говорит "за последнюю неделю", используй оператор "is_on_or_after" и значение "one_week_ago".
        6. Твой ответ должен быть ТОЛЬКО JSON-массивом в одну строку, без ```json и других пояснений. Если не можешь разобрать запрос, верни пустой массив [].
        """

        user_prompt = f"""
        Преобразуй этот запрос: "{query}"

        Пример ответа для запроса "новые лиды ивана за последнюю неделю":
        [
          {{"field": "lead_status", "op": "eq", "value": "Новый"}},
          {{"field": "responsible_manager", "op": "contains", "value": "иван"}},
          {{"field": "created_at", "op": "is_on_or_after", "value": "one_week_ago"}}
        ]
        """

        try:
            # --- ИЗМЕНЕНИЯ ЗДЕСЬ: Новый способ вызова ---
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # Указываем модель DeepSeek
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # Просим модель вернуть ответ строго в формате JSON
                response_format={"type": "json_object"}
            )

            # Извлекаем и парсим JSON из ответа
            json_response_text = response.choices.message.content

            # DeepSeek может вернуть JSON в виде {"result": [...]}. Извлекаем массив.
            parsed_data = json.loads(json_response_text)
            filters = parsed_data.get("result", parsed_data)  # Пытаемся взять ключ 'result', иначе берем как есть

            if isinstance(filters, list):
                return filters
            return []
        except Exception as e:
            print(f"Ошибка при работе с AI моделью DeepSeek: {e}")
            return []