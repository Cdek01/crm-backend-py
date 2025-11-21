# tasks/analytics.py
import asyncio
from celery_worker import celery_app
from db.session import SessionLocal
from db import models
from services.eav_service import EAVService
from services.dashboard_service import DashboardService
from services.ai_service import AIService
from services.alias_service import AliasService  # AliasService может быть нужен EAVService


@celery_app.task
def generate_dashboard_summary_task(user_id: int) -> str:
    """
    Фоновая задача, которая выполняет полный цикл генерации AI-сводки.
    """
    db = SessionLocal()
    try:
        # 1. Получаем пользователя и инициализируем сервисы внутри задачи
        current_user = db.query(models.User).get(user_id)
        if not current_user:
            return "Ошибка: пользователь не найден."

        # EAVService требует AliasService как зависимость
        alias_service = AliasService(db=db)
        eav_service = EAVService(db=db, alias_service=alias_service)

        dashboard_service = DashboardService(db, eav_service, current_user)
        ai_service = AIService(current_user)

        # 2. Собираем и агрегируем данные
        aggregated_data = dashboard_service.get_aggregated_data_for_ai(days_back=30)

        # 3. Генерируем сводку с помощью AI
        # Поскольку метод в AIService асинхронный, мы запускаем его с помощью asyncio
        summary = asyncio.run(ai_service.generate_dashboard_summary(aggregated_data))

        return summary
    except Exception as e:
        # В случае ошибки возвращаем текст, который можно показать пользователю
        return f"Произошла ошибка при генерации отчета: {e}"
    finally:
        db.close()