from pathlib import Path
from werkzeug.utils import secure_filename
from services.crypto_service import CryptoService

BASE_DIR = Path(__file__).parent.parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

class FileService:
    def __init__(self, crypto_service: CryptoService):
        self.crypto = crypto_service
        self.upload_folder = UPLOAD_FOLDER

    def save_pdf(self, file, username: str) -> str:
        """Сохраняет PDF, шифрует его, сжимает, подписывает"""
        filename = secure_filename(file.filename)
        original_data = file.read()

        # 1. Сжатие
        compressed = self.crypto.compress(original_data)
        # 2. Шифрование
        encrypted = self.crypto.encrypt_symmetric(compressed)
        # 3. Подпись хеша исходных данных
        signature = self.crypto.sign_data(original_data)

        # Сохраняем зашифрованный файл + подпись отдельно
        safe_name = f"{username}_{filename}"
        enc_path = self.upload_folder / (safe_name + ".enc")
        sig_path = self.upload_folder / (safe_name + ".sig")
        with open(enc_path, "wb") as f:
            f.write(encrypted)
        with open(sig_path, "wb") as f:
            f.write(signature)

        return safe_name

    def load_pdf_for_user(self, filename: str, username: str, user_role: str = None, admin_usernames: list = None) -> bytes | None:
        """Расшифровывает, проверяет подпись, возвращает PDF.
        Если user_role == 'user', также проверяет файлы администраторов."""
        usernames_to_check = [username]
        
        # Если пользователь с ролью "user", также проверяем файлы админов
        if user_role == 'user' and admin_usernames:
            usernames_to_check.extend(admin_usernames)
        
        # Пробуем найти файл у пользователя или у админов
        for check_username in usernames_to_check:
            safe_name = f"{check_username}_{filename}"
            enc_path = self.upload_folder / (safe_name + ".enc")
            sig_path = self.upload_folder / (safe_name + ".sig")

            if enc_path.exists() and sig_path.exists():
                # Загружаем
                with open(enc_path, "rb") as f:
                    encrypted = f.read()
                with open(sig_path, "rb") as f:
                    signature = f.read()

                # Расшифровка
                try:
                    compressed = self.crypto.decrypt_symmetric(encrypted)
                    original_data = self.crypto.decompress(compressed)
                except Exception:
                    continue  # Пробуем следующий файл

                # Проверка подписи
                if self.crypto.verify_signature(original_data, signature):
                    return original_data
        
        return None

    def list_user_files(self, username: str, user_role: str = None, admin_usernames: list = None) -> list[dict]:
        """Возвращает список файлов пользователя с метаданными.
        Если user_role == 'user', также возвращает файлы всех администраторов."""
        files = []
        prefixes_to_check = [f"{username}_"]
        
        # Если пользователь с ролью "user", добавляем файлы всех админов
        if user_role == 'user' and admin_usernames:
            for admin_username in admin_usernames:
                prefixes_to_check.append(f"{admin_username}_")
        
        if not self.upload_folder.exists():
            return files
        
        # Ищем все .enc файлы для указанных префиксов
        for prefix in prefixes_to_check:
            for enc_file in self.upload_folder.glob(f"{prefix}*.enc"):
                # Извлекаем оригинальное имя файла
                safe_name = enc_file.stem  # убираем .enc
                original_filename = safe_name[len(prefix):]  # убираем префикс username_
                
                # Проверяем наличие соответствующего .sig файла
                sig_file = self.upload_folder / (safe_name + ".sig")
                if sig_file.exists():
                    # Получаем размер и дату изменения
                    file_size = enc_file.stat().st_size
                    modified_time = enc_file.stat().st_mtime
                    
                    # Определяем владельца файла
                    file_owner = prefix.rstrip('_')
                    is_owner = file_owner == username
                    
                    files.append({
                        'filename': original_filename,
                        'safe_name': safe_name,
                        'size': file_size,
                        'modified': modified_time,
                        'owner': file_owner,
                        'is_owner': is_owner
                    })
        
        # Сортируем по дате изменения (новые первыми)
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files