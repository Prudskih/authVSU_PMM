from models.users import User
from repositories.user_repository import UserRepository
from services.password_service import PasswordService

class AuthService:
    def __init__(self, user_repo: UserRepository, pwd_service: PasswordService):
        self.user_repo = user_repo
        self.pwd_service = pwd_service

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.user_repo.get_user(username)
        if user and self.pwd_service.verify_password(password, user.password_hash):
            return user
        return None

    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        if self.user_repo.get_user(username):
            return False
        pwd_hash = self.pwd_service.hash_password(password)
        user = User(username=username, password_hash=pwd_hash, role=role)
        self.user_repo.save_user(user)
        return True

    def remove_user(self, username: str, current_user: str) -> bool:
        if username == current_user:
            return False
        return self.user_repo.delete_user(username)