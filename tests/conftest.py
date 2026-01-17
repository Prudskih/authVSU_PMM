"""Конфигурация pytest"""
import pytest
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app as flask_app


@pytest.fixture
def app():
    """Создание тестового Flask приложения"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    return flask_app


@pytest.fixture
def client(app):
    """Создание тестового клиента"""
    return app.test_client()


@pytest.fixture
def auth_headers(client, app):
    """Создание пользователя и получение заголовков аутентификации"""
    app.auth_service.create_user("testuser", "testpass", "user")
    
    with client.session_transaction() as sess:
        sess['username'] = "testuser"
        sess['role'] = "user"
    
    return client


@pytest.fixture
def admin_headers(client, app):
    """Создание администратора и получение заголовков"""
    app.auth_service.create_user("admin", "adminpass", "admin")
    
    with client.session_transaction() as sess:
        sess['username'] = "admin"
        sess['role'] = "admin"
    
    return client

