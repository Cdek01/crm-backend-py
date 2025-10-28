# services/ai_service.py
from openai import OpenAI
from core.config import settings
from db import models
from typing import List, Dict, Any
import json
import logging # <-- ШАГ 1: Добавьте этот импорт
logger = logging.getLogger(__name__)

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

        # --- НАЧАЛО ИЗМЕНЕНИЙ В ПРОМПТЕ ---
        system_prompt = f"""
          Ты — AI-ассистент, встроенный в CRM. Твоя задача — преобразовать запрос пользователя на естественном языке в JSON-массив фильтров.

          Вот схема колонок таблицы, с которой работает пользователь:
          {json.dumps(table_schema, indent=2, ensure_ascii=False)}

          Правила:
          1. Для поля "field" всегда используй системные имена (`name`) из схемы.
          2. Для текстовых полей (`string`) используй оператор "contains".
          3. Для точного совпадения (статус, категория) используй "eq".
          4. Для числовых полей (`integer`, `float`) используй операторы "gt" (больше), "lt" (меньше), "gte" (больше или равно), "lte" (меньше или равно).
          5. Для дат используй специальные значения: 'today', 'yesterday', 'one_week_ago'.
          6. Если пользователь говорит "за последнюю неделю" или "за прошлую неделю", используй оператор "is_on_or_after" и значение "one_week_ago".
          7. Если не можешь разобрать часть запроса, проигнорируй ее. Если не можешь разобрать весь запрос, верни пустой массив [].
          8. Твой ответ должен быть ТОЛЬКО JSON-массивом в одну строку, без ```json и других пояснений.

          Пример запроса: "новые сделки ивана на сумму больше 10000 за последнюю неделю"
          Пример твоего ответа:
          [
            {{"field": "status", "op": "eq", "value": "Новая"}},
            {{"field": "manager", "op": "contains", "value": "иван"}},
            {{"field": "amount", "op": "gt", "value": 10000}},
            {{"field": "creation_date", "op": "is_on_or_after", "value": "one_week_ago"}}
          ]
          """

        user_prompt = f'Преобразуй этот запрос: "{query}"'
        # --- КОНЕЦ ИЗМЕНЕНИЙ В ПРОМПТЕ ---

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # response_format={"type": "json_object"} # Уберем это, чтобы получить сырой текст
            )

            json_response_text = response.choices.message.content
            # Более надежное извлечение JSON из ответа
            json_start = json_response_text.find('[')
            json_end = json_response_text.rfind(']') + 1
            if json_start != -1 and json_end != -1:
                json_response_text = json_response_text[json_start:json_end]

            filters = json.loads(json_response_text)

            if isinstance(filters, list):
                return filters
            return []
        except Exception as e:
            print(f"Ошибка при работе с AI моделью DeepSeek: {e}")
            return []