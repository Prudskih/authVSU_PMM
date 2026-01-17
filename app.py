from flask import Flask, request, render_template, redirect, url_for, flash, session
from repositories.user_repository import InMemoryUserRepository
from services.password_service import PasswordService
from services.auth_service import AuthService
from services.crypto_service import CryptoService
from services.file_service import FileService
from datetime import datetime
from config import FLASK_SECRET_KEY
import os

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Режим отладки из переменной окружения
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Добавляем фильтр для форматирования времени в шаблонах
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d.%m.%Y %H:%M'):
    """Форматирует timestamp в читаемую дату"""
    if value:
        return datetime.fromtimestamp(value).strftime(format)
    return ''

# Инициализация зависимостей
user_repo = InMemoryUserRepository()
pwd_service = PasswordService()
auth_service = AuthService(user_repo, pwd_service)
crypto_service = CryptoService()
file_service = FileService(crypto_service)

# Создаём демо-пользователей при запуске
if not user_repo.get_user("admin"):
    auth_service.create_user("admin", "admin123", "admin")
if not user_repo.get_user("user1"):
    auth_service.create_user("user1", "user123", "user")

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = auth_service.authenticate(username, password)
        if user:
            session['username'] = user.username
            session['role'] = user.role
            flash(f"Добро пожаловать, {user.username}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Неверное имя пользователя или пароль.", "error")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html',
                           current_user=session['username'],
                           role=session['role'])

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']
        user = user_repo.get_user(session['username'])
        if not pwd_service.verify_password(old, user.password_hash):
            flash("Старый пароль неверен.", "error")
        else:
            user.password_hash = pwd_service.hash_password(new)
            user_repo.save_user(user)
            flash("Пароль успешно изменён.", "success")
            return redirect(url_for('dashboard'))
    return '''
    <form method="post">
        Старый пароль: <input type="password" name="old_password" required><br>
        Новый пароль: <input type="password" name="new_password" required><br>
        <button type="submit">Сменить</button>
    </form>
    <a href="/dashboard">← Назад</a>
    '''

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        flash("Доступ запрещён.", "error")
        return redirect(url_for('dashboard'))
    users = user_repo.list_users()
    return render_template('admin.html', users=users, current_user=session['username'])

@app.route('/admin/create', methods=['POST'])
def admin_create_user():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    if auth_service.create_user(username, password, role):
        flash(f"Пользователь {username} создан.", "success")
    else:
        flash(f"Пользователь {username} уже существует.", "error")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete', methods=['POST'])
def admin_delete_user():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    username = request.form['username']
    if auth_service.remove_user(username, session['username']):
        flash(f"Пользователь {username} удалён.", "success")
    else:
        flash("Невозможно удалить текущего пользователя.", "error")
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Вы вышли из системы.", "success")
    return redirect(url_for('login'))

def get_admin_usernames() -> list[str]:
    """Возвращает список имен пользователей с ролью 'admin'"""
    all_users = user_repo.list_users()
    return [user.username for user in all_users if user.role == 'admin']

@app.route('/files')
def files():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role', 'user')
    admin_usernames = get_admin_usernames() if user_role == 'user' else None
    
    user_files = file_service.list_user_files(
        session['username'],
        user_role=user_role,
        admin_usernames=admin_usernames
    )
    return render_template('files.html', 
                         username=session['username'],
                         role=user_role,
                         files=user_files)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'username' not in session:
        return redirect(url_for('login'))
    # Только администраторы могут загружать файлы
    if session.get('role') != 'admin':
        flash("У вас нет прав для загрузки файлов", "error")
        return redirect(url_for('files'))
    if 'pdf' not in request.files:
        flash("Файл не выбран", "error")
        return redirect(url_for('files'))
    file = request.files['pdf']
    if file.filename == '':
        flash("Файл не выбран", "error")
        return redirect(url_for('files'))
    if not file.filename.lower().endswith('.pdf'):
        flash("Только PDF!", "error")
        return redirect(url_for('files'))

    try:
        filename = file_service.save_pdf(file, session['username'])
        flash(f"Файл {filename} загружен и защищён!", "success")
    except Exception as e:
        flash("Ошибка при загрузке файла", "error")
    return redirect(url_for('files'))

@app.route('/view_pdf/<filename>')
def view_pdf(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('role', 'user')
    admin_usernames = get_admin_usernames() if user_role == 'user' else None
    
    pdf_data = file_service.load_pdf_for_user(
        filename,
        session['username'],
        user_role=user_role,
        admin_usernames=admin_usernames
    )
    if pdf_data is None:
        flash("Файл не найден или повреждён", "error")
        return redirect(url_for('files'))
    return pdf_data, 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'inline; filename="{filename}"'
    }

if __name__ == '__main__':
    app.run(debug=DEBUG)