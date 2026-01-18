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

    def _safe_name(self, owner_username: str, original_filename: str) -> str:
        filename = secure_filename(original_filename)
        return f"{owner_username}_{filename}"

    def save_pdf(self, file, username: str) -> str:
        """
        Сохраняет PDF, шифрует его, сжимает, подписывает.
        Возвращает safe_name (username_filename).
        """
        filename = secure_filename(file.filename)
        original_data = file.read()

        compressed = self.crypto.compress(original_data)
        encrypted = self.crypto.encrypt_symmetric(compressed)
        signature = self.crypto.sign_data(original_data)

        safe_name = f"{username}_{filename}"
        enc_path = self.upload_folder / (safe_name + ".enc")
        sig_path = self.upload_folder / (safe_name + ".sig")

        enc_path.write_bytes(encrypted)
        sig_path.write_bytes(signature)

        return safe_name

    def _iter_all_safe_names(self):
        if not self.upload_folder.exists():
            return
        for enc_file in self.upload_folder.glob("*.enc"):
            safe_name = enc_file.stem  # without .enc
            sig_file = self.upload_folder / (safe_name + ".sig")
            if sig_file.exists():
                yield safe_name

    def _parse_owner_and_filename(self, safe_name: str) -> tuple[str, str] | None:
        # safe_name = "{owner}_{filename}"
        if "_" not in safe_name:
            return None
        owner, original = safe_name.split("_", 1)
        if not owner or not original:
            return None
        return owner, original

    def list_files(self, username: str, user_role: str) -> list[dict]:
        """
        user  -> только свои файлы
        admin -> все файлы
        """
        files = []

        if user_role == "admin":
            safe_names = list(self._iter_all_safe_names())
        else:
            # только свои
            safe_names = []
            prefix = f"{username}_"
            for enc_file in self.upload_folder.glob(f"{prefix}*.enc"):
                safe_name = enc_file.stem
                sig_file = self.upload_folder / (safe_name + ".sig")
                if sig_file.exists():
                    safe_names.append(safe_name)

        for safe_name in safe_names:
            parsed = self._parse_owner_and_filename(safe_name)
            if not parsed:
                continue
            owner, original_filename = parsed

            enc_path = self.upload_folder / (safe_name + ".enc")
            file_size = enc_path.stat().st_size
            modified_time = enc_path.stat().st_mtime

            files.append({
                "filename": original_filename,
                "safe_name": safe_name,     # важно: используем safe_name в URL
                "size": file_size,
                "modified": modified_time,
                "owner": owner,
                "is_owner": owner == username
            })

        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    def load_pdf(self, safe_name: str) -> bytes | None:
        """
        Загружает по safe_name (owner_filename) и расшифровывает.
        """
        enc_path = self.upload_folder / (safe_name + ".enc")
        sig_path = self.upload_folder / (safe_name + ".sig")
        if not enc_path.exists() or not sig_path.exists():
            return None

        encrypted = enc_path.read_bytes()
        signature = sig_path.read_bytes()

        try:
            compressed = self.crypto.decrypt_symmetric(encrypted)
            original_data = self.crypto.decompress(compressed)
        except Exception:
            return None

        if not self.crypto.verify_signature(original_data, signature):
            return None

        return original_data

    def can_access(self, safe_name: str, username: str, user_role: str) -> bool:
        """
        user  -> только если owner == username
        admin -> всегда
        """
        parsed = self._parse_owner_and_filename(safe_name)
        if not parsed:
            return False
        owner, _ = parsed
        return user_role == "admin" or owner == username
