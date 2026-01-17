"""Тесты для FileService"""
import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from services.file_service import FileService
from services.crypto_service import CryptoService


class TestFileService:
    """Тесты сервиса работы с файлами"""
    
    def setup_method(self):
        """Инициализация перед каждым тестом"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.crypto = CryptoService()
        
        # Создаем временный FileService с временной директорией
        self.file_service = FileService(self.crypto)
        self.file_service.upload_folder = self.temp_dir
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_save_pdf_creates_files(self):
        """Тест: сохранение PDF создает .enc и .sig файлы"""
        file_obj = BytesIO(b"fake pdf content")
        file_obj.filename = "test.pdf"
        
        safe_name = self.file_service.save_pdf(file_obj, "testuser")
        
        enc_path = self.temp_dir / (safe_name + ".enc")
        sig_path = self.temp_dir / (safe_name + ".sig")
        
        assert enc_path.exists()
        assert sig_path.exists()
        assert safe_name == "testuser_test.pdf"
    
    def test_load_pdf_for_user_success(self):
        """Тест: успешная загрузка PDF"""
        file_obj = BytesIO(b"original pdf content")
        file_obj.filename = "test.pdf"
        
        safe_name = self.file_service.save_pdf(file_obj, "testuser")
        original_filename = "test.pdf"
        
        loaded_data = self.file_service.load_pdf_for_user(
            original_filename, "testuser"
        )
        
        assert loaded_data == b"original pdf content"
    
    def test_load_pdf_for_user_nonexistent(self):
        """Тест: загрузка несуществующего PDF"""
        loaded_data = self.file_service.load_pdf_for_user(
            "nonexistent.pdf", "testuser"
        )
        
        assert loaded_data is None
    
    def test_list_user_files_empty(self):
        """Тест: список файлов пустого пользователя"""
        files = self.file_service.list_user_files("testuser")
        
        assert files == []
    
    def test_list_user_files_with_files(self):
        """Тест: список файлов пользователя с файлами"""
        file1 = BytesIO(b"content1")
        file1.filename = "file1.pdf"
        file2 = BytesIO(b"content2")
        file2.filename = "file2.pdf"
        
        self.file_service.save_pdf(file1, "testuser")
        self.file_service.save_pdf(file2, "testuser")
        
        files = self.file_service.list_user_files("testuser")
        
        assert len(files) == 2
        filenames = [f['filename'] for f in files]
        assert "file1.pdf" in filenames
        assert "file2.pdf" in filenames
    
    def test_list_user_files_includes_admin_files_for_user_role(self):
        """Тест: пользователи видят файлы администраторов"""
        admin_file = BytesIO(b"admin content")
        admin_file.filename = "admin_file.pdf"
        user_file = BytesIO(b"user content")
        user_file.filename = "user_file.pdf"
        
        self.file_service.save_pdf(admin_file, "admin")
        self.file_service.save_pdf(user_file, "user1")
        
        files = self.file_service.list_user_files(
            "user1",
            user_role="user",
            admin_usernames=["admin"]
        )
        
        assert len(files) == 2
        filenames = [f['filename'] for f in files]
        assert "admin_file.pdf" in filenames
        assert "user_file.pdf" in filenames

