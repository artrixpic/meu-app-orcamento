from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import config

# Instanciamos as extensões GLOBALMENTE
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Configurações do Login
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Faça login para acessar esta página.'
login_manager.login_message_category = 'info'

limiter = Limiter(key_func=get_remote_address)

def create_app(config_name='default'):
    app = Flask(__name__)

    # Carrega configurações
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # Configuração do Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Filtro de Moeda
    @app.template_filter('format_currency')
    def format_currency(value):
        if value is None: 
            value = 0
        try:
            return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "0,00"

    # Registro de Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.budget import budget_bp
    from app.routes.operations import operations_bp

    app.register_blueprint(dashboard_bp) 
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(budget_bp, url_prefix='/budget')
    app.register_blueprint(operations_bp, url_prefix='/operations')

    return app
