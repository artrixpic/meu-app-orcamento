from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# CORREÇÃO 1: Ajuste dos imports para apontar para o pacote 'app'
from app import db
from app.models import User, UserConfig

# CORREÇÃO 2: Renomear 'bp' para 'auth_bp' para facilitar o import no __init__.py
auth_bp = Blueprint('auth', __name__)

# Rota raiz do blueprint (/auth/)
@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        # Certifique-se que no dashboard.py o blueprint se chama 'dashboard' e a função 'dashboard'
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            current_app.logger.info(f'Login realizado: {email}')

            # Redireciona para onde o usuário queria ir antes de logar, ou dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.dashboard'))

        flash('Email ou senha incorretos.', 'error')

    return render_template('login.html') # Certifique-se que login.html está na pasta templates

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        # Validação básica
        if not email or not password or len(password) < 6:
            flash('Dados inválidos. A senha deve ter no mínimo 6 caracteres.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return redirect(url_for('auth.register'))

        # Criar Usuário
        new_user = User(
            email=email, 
            name=name, 
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )

        db.session.add(new_user)
        db.session.commit() # Commit para gerar o ID do usuário

        # Criar Configuração Inicial
        db.session.add(UserConfig(user_id=new_user.id))
        db.session.commit()

        login_user(new_user)

        # Certifique-se que existe uma função 'onboarding' no dashboard.py
        return redirect(url_for('dashboard.onboarding'))

    return render_template('register.html')

@auth_bp.route('/logout', methods=['GET', 'POST']) # Adicionei GET para facilitar testes, mas POST é mais seguro
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))