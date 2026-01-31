import os
import logging

class Config:
    # Segurança Básica
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-troque-em-prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Segurança de Cookies (Padrão Hardened)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuração de Logs Padrão (Stdout)
    LOG_LEVEL = logging.INFO

    # Rate Limit padrão (Memória - Ok para Dev)
    RATELIMIT_STORAGE_URI = "memory://"

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///cineorca.db')
    SESSION_COOKIE_SECURE = False 

class ProductionConfig(Config):
    DEBUG = False

    # P2: Obriga HTTPS nos Cookies
    SESSION_COOKIE_SECURE = True 

    # --- Configuração Neon / Postgres ---
    # Captura a URL do banco
    _db_url = os.environ.get('DATABASE_URL')

    # Correção 1: Heroku/Neon usam postgres://, mas SQLAlchemy exige postgresql://
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    # Correção 2: Neon exige SSL
    if _db_url and '?' not in _db_url:
        _db_url += '?sslmode=require'

    SQLALCHEMY_DATABASE_URI = _db_url

    # Correção 3: Engine Options para evitar desconexões do Neon
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,        # Testa a conexão antes de usar (Crítico para Neon)
        "pool_recycle": 300,          # Recicla a cada 5 min
        "pool_size": 10,              # Ajuste conforme seu plano
        "max_overflow": 20,
        "pool_timeout": 30
    }

    # --- Configuração Redis (Obrigatório para Rate Limit em Prod) ---
    REDIS_URL = os.environ.get('REDIS_URL')
    if REDIS_URL:
        RATELIMIT_STORAGE_URI = REDIS_URL

    # P2: Observabilidade Sentry
    SENTRY_DSN = os.environ.get('SENTRY_DSN')

    @classmethod
    def init_app(cls, app):
        # 1. Configurar Logs
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        # 2. FAIL-FAST: Validação de Segurança Crítica
        cls.check_production_security()

    @classmethod
    def check_production_security(cls):
        """Verifica se as variáveis críticas existem. Se não, crasha o app."""
        errors = []

        # Valida Secret Key
        if cls.SECRET_KEY == 'dev-key-troque-em-prod' or len(cls.SECRET_KEY) < 20:
            errors.append("❌ SECRET_KEY está fraca ou padrão de dev.")

        # Valida Banco de Dados
        if not cls.SQLALCHEMY_DATABASE_URI:
            errors.append("❌ DATABASE_URL não definida.")
        elif 'sqlite' in cls.SQLALCHEMY_DATABASE_URI:
            errors.append("❌ Tentativa de usar SQLite em Produção.")

        # Valida Redis (Rate Limit não funciona sem ele em Gunicorn/Render)
        if not cls.REDIS_URL:
            errors.append("❌ REDIS_URL ausente. O Rate Limit não funcionará corretamente.")

        if errors:
            raise ValueError("\n".join(["\n🚨 ERRO DE CONFIGURAÇÃO DE PRODUÇÃO:"] + errors))

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}