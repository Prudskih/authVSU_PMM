from abc import ABC, abstractmethod
from models.users import User

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


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users = {}

    def get_user(self, username: str) -> User | None:
        return self._users.get(username)

    def save_user(self, user: User) -> None:
        self._users[user.username] = user

    def delete_user(self, username: str) -> bool:
        if username in self._users:
            del self._users[username]
            return True
        return False

    def list_users(self) -> list[User]:
        return list(self._users.values())