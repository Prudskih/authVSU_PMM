# config.py
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

import os
from pathlib import Path


# Путь к директории с ключами
KEYS_DIR = Path(__file__).parent / "keys"
KEYS_DIR.mkdir(exist_ok=True)

AES_KEY_FILE = KEYS_DIR / "aes_key.bin"
RSA_PRIVATE_KEY_FILE = KEYS_DIR / "rsa_private_key.pem"
RSA_PUBLIC_KEY_FILE = KEYS_DIR / "rsa_public_key.pem"


def get_or_create_aes_key() -> bytes:
    """Получает AES ключ из файла или создает новый"""
    if AES_KEY_FILE.exists():
        return AES_KEY_FILE.read_bytes()
    else:
        # Генерируем новый ключ
        key = os.urandom(32)
        AES_KEY_FILE.write_bytes(key)
        return key


def get_or_create_rsa_keys():
    """Получает RSA ключи из файлов или создает новые"""
    if RSA_PRIVATE_KEY_FILE.exists() and RSA_PUBLIC_KEY_FILE.exists():
        # Загружаем существующие ключи
        with open(RSA_PRIVATE_KEY_FILE, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
        with open(RSA_PUBLIC_KEY_FILE, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        return private_key, public_key
    else:
        # Генерируем новые ключи
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Сохраняем ключи
        with open(RSA_PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(RSA_PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        return private_key, public_key


# Симметричный ключ (AES): 32 байта = AES-256
AES_KEY = get_or_create_aes_key()

# Асимметричные ключи RSA (для ЭП)
RSA_PRIVATE_KEY, RSA_PUBLIC_KEY = get_or_create_rsa_keys()

# Flask секретный ключ из переменной окружения
# Если .env файл не читается или ключа нет - используем fallback
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not FLASK_SECRET_KEY:
    FLASK_SECRET_KEY = 'change-this-in-production-secret-key-dev-only'

 # Локальная "БД" пользователей (JSON)
USERS_DB_FILE = Path(__file__).parent / "data" / "users.json"
USERS_DB_FILE.parent.mkdir(exist_ok=True)

