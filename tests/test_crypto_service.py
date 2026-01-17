"""Тесты для CryptoService"""
import pytest
from services.crypto_service import CryptoService


class TestCryptoService:
    """Тесты сервиса шифрования"""
    
    def setup_method(self):
        """Инициализация перед каждым тестом"""
        self.crypto = CryptoService()
        self.test_data = b"Hello, World! This is test data for encryption."
    
    def test_compress_decompress(self):
        """Тест: сжатие и распаковка данных"""
        compressed = self.crypto.compress(self.test_data)
        
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0
        
        decompressed = self.crypto.decompress(compressed)
        
        assert decompressed == self.test_data
    
    def test_encrypt_decrypt_symmetric(self):
        """Тест: симметричное шифрование и расшифровка"""
        encrypted = self.crypto.encrypt_symmetric(self.test_data)
        
        assert isinstance(encrypted, bytes)
        assert encrypted != self.test_data
        assert len(encrypted) > len(self.test_data)  # IV + TAG + ciphertext
        
        decrypted = self.crypto.decrypt_symmetric(encrypted)
        
        assert decrypted == self.test_data
    
    def test_encrypt_different_iv(self):
        """Тест: разные шифрования дают разные результаты (из-за IV)"""
        encrypted1 = self.crypto.encrypt_symmetric(self.test_data)
        encrypted2 = self.crypto.encrypt_symmetric(self.test_data)
        
        # Разные IV должны давать разные шифротексты
        assert encrypted1 != encrypted2
        
        # Но расшифровка должна давать одинаковый результат
        assert self.crypto.decrypt_symmetric(encrypted1) == self.test_data
        assert self.crypto.decrypt_symmetric(encrypted2) == self.test_data
    
    def test_sign_verify_signature(self):
        """Тест: подпись и проверка подписи"""
        signature = self.crypto.sign_data(self.test_data)
        
        assert isinstance(signature, bytes)
        assert len(signature) > 0
        
        is_valid = self.crypto.verify_signature(self.test_data, signature)
        
        assert is_valid is True
    
    def test_verify_signature_invalid(self):
        """Тест: проверка недействительной подписи"""
        signature = self.crypto.sign_data(self.test_data)
        modified_data = self.test_data + b"modified"
        
        is_valid = self.crypto.verify_signature(modified_data, signature)
        
        assert is_valid is False
    
    def test_encrypt_compress_decrypt_decompress_workflow(self):
        """Тест: полный цикл сжатие-шифрование-расшифровка-распаковка"""
        # 1. Сжатие
        compressed = self.crypto.compress(self.test_data)
        # 2. Шифрование
        encrypted = self.crypto.encrypt_symmetric(compressed)
        # 3. Расшифровка
        decrypted = self.crypto.decrypt_symmetric(encrypted)
        # 4. Распаковка
        original = self.crypto.decompress(decrypted)
        
        assert original == self.test_data
    
    def test_empty_data(self):
        """Тест: работа с пустыми данными"""
        empty_data = b""
        
        compressed = self.crypto.compress(empty_data)
        decompressed = self.crypto.decompress(compressed)
        
        assert decompressed == empty_data
        
        encrypted = self.crypto.encrypt_symmetric(empty_data)
        decrypted = self.crypto.decrypt_symmetric(encrypted)
        
        assert decrypted == empty_data

