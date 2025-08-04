from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from database import DatabaseManager
import sqlite3
from datetime import datetime
from functools import wraps

# Blueprint para autenticação
auth_bp = Blueprint('auth', __name__)

# Inicializar extensões
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

class User(UserMixin):
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    db = DatabaseManager()
    user_data = db.get_user_by_id(user_id)
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[4])
    return None

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', 
                                   validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Função', choices=[('admin', 'Administrador'), ('operator', 'Operador')], 
                      default='operator')
    submit = SubmitField('Cadastrar')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    form = LoginForm()
    if form.validate_on_submit():
        db = DatabaseManager()
        user_data = db.authenticate_user(form.username.data, form.password.data)
        
        if user_data:
            user = User(user_data[0], user_data[1], user_data[2], user_data[4])
            login_user(user)
            db.update_last_login(user_data[0])
            
            next_page = request.args.get('next')
            flash(f'Bem-vindo, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('admin'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Apenas admins podem registrar novos usuários
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem registrar usuários.', 'danger')
        return redirect(url_for('admin'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        db = DatabaseManager()
        
        # Verificar se usuário já existe
        if db.get_user_by_username(form.username.data):
            flash('Nome de usuário já existe.', 'danger')
            return render_template('register.html', form=form)
        
        if db.get_user_by_email(form.email.data):
            flash('Email já está em uso.', 'danger')
            return render_template('register.html', form=form)
        
        # Criar novo usuário
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user_id = db.create_user(form.username.data, form.email.data, hashed_password, form.role.data)
        
        if user_id:
            flash(f'Usuário {form.username.data} criado com sucesso!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Erro ao criar usuário.', 'danger')
    
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@auth_bp.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('admin'))
    
    db = DatabaseManager()
    users = db.get_all_users()
    return render_template('users.html', users=users)

def init_auth(app):
    """Inicializa a autenticação na aplicação Flask"""
    bcrypt.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Criar usuário admin padrão se não existir
    with app.app_context():
        db = DatabaseManager()
        if not db.get_user_by_username('admin'):
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            db.create_user('admin', 'admin@clinica.com', hashed_password, 'admin')
            print("✅ Usuário admin padrão criado: admin/admin123")