# services/dashboard_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import Counter

from db import models
from services.eav_service import EAVService


class DashboardService:
    def __init__(self, db: Session, eav_service: EAVService, current_user: models.User):
        self.db = db
        self.eav_service = eav_service
        self.user = current_user

    def get_aggregated_data_for_ai(self, days_back: int = 30):
        """
        Собирает и агрегирует ключевые метрики из таблиц интеграций
        для последующей передачи в AI-модель.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_filter = {
            "op": "is_within",
            "value": [start_date.isoformat(), end_date.isoformat()]
        }

        # --- 1. Сбор данных ---
        try:
            tochka_ops = self.eav_service.get_all_entities_for_type(
                "tochka_operations", self.user, filters=[{"field": "operation_date", **date_filter}], limit=10000
            )['data']
        except Exception:
            tochka_ops = []

        try:
            modulbank_ops = self.eav_service.get_all_entities_for_type(
                "banking_operations", self.user, filters=[{"field": "operation_date", **date_filter}], limit=10000
            )['data']
        except Exception:
            modulbank_ops = []

        try:
            beeline_calls = self.eav_service.get_all_entities_for_type(
                "beeline_calls", self.user, filters=[{"field": "call_date", **date_filter}], limit=10000
            )['data']
        except Exception:
            beeline_calls = []

        all_bank_ops = tochka_ops + modulbank_ops

        # --- 2. Агрегация данных ---

        # Финансы
        incomes = [op for op in all_bank_ops if op.get('operation_type') == 'Поступление']
        expenses = [op for op in all_bank_ops if op.get('operation_type') == 'Списание']

        total_income = sum(op.get('amount', 0) for op in incomes)
        total_expense = sum(op.get('amount', 0) for op in expenses)

        top_incomes = sorted(incomes, key=lambda x: x.get('amount', 0), reverse=True)[:3]
        top_expenses = sorted(expenses, key=lambda x: x.get('amount', 0), reverse=True)[:3]

        # Телефония
        most_active_employee = "Не определен"
        if beeline_calls:
            employee_counter = Counter(
                call.get('internal_user') for call in beeline_calls if call.get('internal_user')
            )
            if employee_counter:
                most_active_employee = employee_counter.most_common(1)[0][0]

        # --- 3. Формирование результата ---
        return {
            "period_days": days_back,
            "financials": {
                "total_income": round(total_income, 2),
                "total_expense": round(total_expense, 2),
                "net_flow": round(total_income - total_expense, 2),
                "top_incomes": [
                    {"amount": op.get('amount'), "contractor": op.get('contractor_name')} for op in top_incomes
                ],
                "top_expenses": [
                    {"amount": op.get('amount'), "contractor": op.get('contractor_name'), "purpose": op.get('purpose')}
                    for op in top_expenses
                ]
            },
            "telephony": {
                "total_calls": len(beeline_calls),
                "incoming_calls": len([c for c in beeline_calls if c.get('direction') == 'IN']),
                "outgoing_calls": len([c for c in beeline_calls if c.get('direction') == 'OUT']),
                "total_duration_minutes": round(sum(c.get('duration_seconds', 0) for c in beeline_calls) / 60),
                "most_active_employee": most_active_employee
            }
        }