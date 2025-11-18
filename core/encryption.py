# core/encryption.py
from cryptography.fernet import Fernet
from core.config import settings

# Загружаем ключ и инициализируем шифратор ОДИН РАЗ
# Убедитесь, что ключ имеет правильную длину (32 байта, закодированные в base64)
# Для простоты, пока будем использовать его как есть, но в продакшене
# лучше использовать base64-кодированный ключ.
# Для генерации: from cryptography.fernet import Fernet; Fernet.generate_key()
fernet = Fernet(settings.ENCRYPTION_KEY.encode()) # Упрощенно, ключ должен быть base64

def encrypt_data(data: str) -> bytes:
    """Шифрует строку и возвращает байты."""
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes) -> str:
    """Расшифровывает байты и возвращает строку."""
    return fernet.decrypt(encrypted_data).decode()