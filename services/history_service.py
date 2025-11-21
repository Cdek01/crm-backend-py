# services/history_service.py
from sqlalchemy.orm import Session
from db import models
import json
from datetime import datetime


# --- НАЧАЛО: Добавьте эту вспомогательную функцию ---
def json_converter(o):
    """Конвертер для объектов, которые не сериализуются в JSON стандартным способом."""
    if isinstance(o, datetime):
        return o.isoformat() # Превращаем datetime в строку формата ISO 8601

def to_json_serializable(data):
    """Рекурсивно преобразует словарь, чтобы он стал JSON-сериализуемым."""
    if data is None:
        return None
    # Мы просто кодируем и декодируем, используя наш кастомный конвертер.
    # Это простой трюк, чтобы обработать все вложенные datetime.
    return json.loads(json.dumps(data, default=json_converter))
# --- КОНЕЦ ---




class HistoryService:
    def __init__(self, db: Session, eav_service: 'EAVService'):
        self.db = db
        self.eav_service = eav_service

    def record_action(self, user_id, action_type, entity_type_name, entity_id, state_before, state_after, description):
        """Записывает действие в историю и очищает стек 'повтора'."""

        # 1. Удаляем все будущие действия (которые можно было бы 'повторить')
        self.db.query(models.ActionHistory).filter(
            models.ActionHistory.user_id == user_id,
            models.ActionHistory.is_undone == True
        ).delete(synchronize_session=False)

        # 2. Создаем новую запись в истории
        new_action = models.ActionHistory(
            user_id=user_id,
            action_type=action_type,
            entity_type_name=entity_type_name,
            entity_id=entity_id,
            state_before=to_json_serializable(state_before),
            state_after=to_json_serializable(state_after),
            description=description,
            is_undone=False
        )
        self.db.add(new_action)
        self.db.commit()

    def undo(self, user: models.User):
        """Отменяет последнее действие пользователя."""
        last_action = self.db.query(models.ActionHistory).filter(
            models.ActionHistory.user_id == user.id,
            models.ActionHistory.is_undone == False
        ).order_by(models.ActionHistory.timestamp.desc()).first()

        if not last_action:
            return {"message": "Нет действий для отмены."}

        # Применяем обратное действие
        if last_action.action_type == 'CREATE':
            self.eav_service.delete_entity(last_action.entity_id, user, source="history")
        elif last_action.action_type == 'DELETE':
            self.eav_service.create_entity(last_action.entity_type_name,
                                           {**last_action.state_before, "_source": "history"}, user)
        elif last_action.action_type == 'UPDATE':
            self.eav_service.update_entity(last_action.entity_id, {**last_action.state_before, "_source": "history"},
                                           user)

        # Помечаем действие как отмененное
        last_action.is_undone = True
        self.db.commit()
        return {"message": f"Действие '{last_action.description}' отменено."}

    def redo(self, user: models.User):
        """Повторяет последнее отмененное действие пользователя."""
        last_undone_action = self.db.query(models.ActionHistory).filter(
            models.ActionHistory.user_id == user.id,
            models.ActionHistory.is_undone == True
        ).order_by(models.ActionHistory.timestamp.asc()).first()

        if not last_undone_action:
            return {"message": "Нет действий для повтора."}

        # Применяем прямое действие
        if last_undone_action.action_type == 'CREATE':
            self.eav_service.create_entity(last_undone_action.entity_type_name,
                                           {**last_undone_action.state_after, "_source": "history"}, user)
        elif last_undone_action.action_type == 'DELETE':
            self.eav_service.delete_entity(last_undone_action.entity_id, user, source="history")
        elif last_undone_action.action_type == 'UPDATE':
            self.eav_service.update_entity(last_undone_action.entity_id,
                                           {**last_undone_action.state_after, "_source": "history"}, user)

        # Помечаем действие как не отмененное
        last_undone_action.is_undone = False
        self.db.commit()
        return {"message": f"Действие '{last_undone_action.description}' повторено."}