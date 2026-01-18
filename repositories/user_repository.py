from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
import json
import base64
from typing import Dict, List

from models.users import User
from config import USERS_DB_FILE


class UserRepository(ABC):
    @abstractmethod
    def get_user(self, username: str) -> User | None:
        pass

    @abstractmethod
    def save_user(self, user: User) -> None:
        pass

    @abstractmethod
    def delete_user(self, username: str) -> bool:
        pass

    @abstractmethod
    def list_users(self) -> list[User]:
        pass


class JsonUserRepository(UserRepository):
    """
    Локальное хранилище пользователей в JSON-файле.
    Нужно, чтобы пользователи/роли не пропадали при перезапуске приложения/сессии.
    """

    def __init__(self, db_file: Path = USERS_DB_FILE):
        self._db_file = db_file
        self._users: Dict[str, User] = {}
        self._load()

    def _load(self) -> None:
        if not self._db_file.exists():
            self._users = {}
            return
        raw = self._db_file.read_text(encoding="utf-8").strip()
        if not raw:
            self._users = {}
            return
        data = json.loads(raw)

        users: Dict[str, User] = {}
        for username, payload in data.items():
            # password_hash хранится как base64 строка
            pwd_b64 = payload["password_hash_b64"]
            pwd_hash = base64.b64decode(pwd_b64.encode("ascii"))
            users[username] = User(
                username=username,
                password_hash=pwd_hash,
                role=payload["role"],
            )
        self._users = users

    def _flush(self) -> None:
        data = {}
        for username, user in self._users.items():
            data[username] = {
                "role": user.role,
                "password_hash_b64": base64.b64encode(user.password_hash).decode("ascii"),
            }
        self._db_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_user(self, username: str) -> User | None:
        return self._users.get(username)

    def save_user(self, user: User) -> None:
        self._users[user.username] = user
        self._flush()

    def delete_user(self, username: str) -> bool:
        if username in self._users:
            del self._users[username]
            self._flush()
            return True
        return False

    def list_users(self) -> list[User]:
        return list(self._users.values())
