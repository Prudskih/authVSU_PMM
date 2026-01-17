"""Тесты для Flask маршрутов"""
import pytest
from io import BytesIO


def test_login_get(app, client):
    """Тест: GET запрос на страницу входа"""
    response = client.get('/login')
    
    assert response.status_code == 200
    assert b'login' in response.data.lower()


def test_login_post_success(client, app):
    """Тест: успешный вход"""
    app.auth_service.create_user("testuser", "password123", "user")
    
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('username') == 'testuser'


def test_login_post_failure(client, app):
    """Тест: неудачный вход"""
    app.auth_service.create_user("testuser", "password123", "user")
    
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrong_password'
    })
    
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('username') is None


def test_dashboard_requires_login(client):
    """Тест: доступ к dashboard требует авторизации"""
    response = client.get('/dashboard', follow_redirects=True)
    
    assert b'login' in response.data.lower()


def test_dashboard_authenticated(auth_headers):
    """Тест: доступ к dashboard для авторизованного пользователя"""
    response = auth_headers.get('/dashboard')
    
    assert response.status_code == 200


def test_upload_pdf_requires_admin(admin_headers, auth_headers, app):
    """Тест: загрузка PDF требует прав администратора"""
    # Пользователь не может загрузить
    file_data = BytesIO(b"fake pdf content")
    file_data.filename = "test.pdf"
    
    response = auth_headers.post('/upload_pdf', 
                                data={'pdf': (file_data, 'test.pdf')},
                                follow_redirects=True)
    
    assert 'нет прав'.encode('utf-8') in response.data.lower() or b'no permission' in response.data.lower()
    
    # Администратор может загрузить
    file_data.seek(0)
    response = admin_headers.post('/upload_pdf',
                                  data={'pdf': (file_data, 'test.pdf')},
                                  follow_redirects=True)
    
    assert response.status_code == 200


def test_logout(client, auth_headers):
    """Тест: выход из системы"""
    response = auth_headers.get('/logout', follow_redirects=True)
    
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('username') is None

