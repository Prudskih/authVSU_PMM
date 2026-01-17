"""Тесты для PasswordService"""
import pytest
from services.password_service import PasswordService


class TestPasswordService:
    """Тесты сервиса паролей"""
    
    def setup_method(self):
        """Инициализация перед каждым тестом"""
        self.pwd_service = PasswordService()
    
    def test_hash_password_returns_bytes(self):
        """Тест: хеширование пароля возвращает bytes"""
        password = "test_password_123"
        hashed = self.pwd_service.hash_password(password)
        
        assert isinstance(hashed, bytes)
        assert len(hashed) > 0
    
    def test_hash_password_different_results(self):
        """Тест: разные пароли дают разные хеши"""
        hash1 = self.pwd_service.hash_password("password1")
        hash2 = self.pwd_service.hash_password("password2")
        
        assert hash1 != hash2
    
    def test_hash_password_same_password_different_salt(self):
        """Тест: одинаковый пароль дает разные хеши (из-за соли)"""
        password = "same_password"
        hash1 = self.pwd_service.hash_password(password)
        hash2 = self.pwd_service.hash_password(password)
        
        # Разные хеши из-за разной соли
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Тест: проверка правильного пароля"""
        password = "correct_password"
        hashed = self.pwd_service.hash_password(password)
        
        assert self.pwd_service.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Тест: проверка неправильного пароля"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = self.pwd_service.hash_password(password)
        
        assert self.pwd_service.verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_string(self):
        """Тест: проверка пустого пароля"""
        password = ""
        hashed = self.pwd_service.hash_password(password)
        
        assert self.pwd_service.verify_password(password, hashed) is True
        assert self.pwd_service.verify_password("not_empty", hashed) is False

