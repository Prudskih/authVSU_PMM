"""Тесты для AuthService"""
import pytest
from services.auth_service import AuthService
from services.password_service import PasswordService
from repositories.user_repository import InMemoryUserRepository
from models.users import User


class TestAuthService:
    """Тесты сервиса аутентификации"""
    
    def setup_method(self):
        """Инициализация перед каждым тестом"""
        self.user_repo = InMemoryUserRepository()
        self.pwd_service = PasswordService()
        self.auth_service = AuthService(self.user_repo, self.pwd_service)
    
    def test_create_user_success(self):
        """Тест: успешное создание пользователя"""
        result = self.auth_service.create_user("testuser", "password123", "user")
        
        assert result is True
        user = self.user_repo.get_user("testuser")
        assert user is not None
        assert user.username == "testuser"
        assert user.role == "user"
    
    def test_create_user_duplicate(self):
        """Тест: попытка создать существующего пользователя"""
        self.auth_service.create_user("testuser", "password123", "user")
        
        result = self.auth_service.create_user("testuser", "password456", "admin")
        
        assert result is False
    
    def test_create_user_default_role(self):
        """Тест: создание пользователя с ролью по умолчанию"""
        self.auth_service.create_user("testuser", "password123")
        
        user = self.user_repo.get_user("testuser")
        assert user.role == "user"
    
    def test_authenticate_success(self):
        """Тест: успешная аутентификация"""
        self.auth_service.create_user("testuser", "password123", "user")
        
        user = self.auth_service.authenticate("testuser", "password123")
        
        assert user is not None
        assert user.username == "testuser"
    
    def test_authenticate_wrong_password(self):
        """Тест: аутентификация с неправильным паролем"""
        self.auth_service.create_user("testuser", "password123", "user")
        
        user = self.auth_service.authenticate("testuser", "wrong_password")
        
        assert user is None
    
    def test_authenticate_nonexistent_user(self):
        """Тест: аутентификация несуществующего пользователя"""
        user = self.auth_service.authenticate("nonexistent", "password123")
        
        assert user is None
    
    def test_remove_user_success(self):
        """Тест: успешное удаление пользователя"""
        self.auth_service.create_user("testuser", "password123", "user")
        
        result = self.auth_service.remove_user("testuser", "other_user")
        
        assert result is True
        assert self.user_repo.get_user("testuser") is None
    
    def test_remove_user_self(self):
        """Тест: попытка удалить самого себя"""
        self.auth_service.create_user("testuser", "password123", "user")
        
        result = self.auth_service.remove_user("testuser", "testuser")
        
        assert result is False
        assert self.user_repo.get_user("testuser") is not None

