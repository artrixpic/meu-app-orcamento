from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Index

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    # Integridade: Email e Senha obrigatórios
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False) 
    name = db.Column(db.String(1000), nullable=False)

    # Relacionamentos
    config = db.relationship('UserConfig', backref='user', uselist=False, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='owner', lazy='dynamic')

class UserConfig(db.Model):
    __tablename__ = 'user_config'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    monthly_goal = db.Column(db.Numeric(12, 2), default=0.00)
    hourly_rate = db.Column(db.Numeric(12, 2), default=0.00)
    company_name = db.Column(db.String(100))
    cnpj = db.Column(db.String(20))
    address = db.Column(db.String(200))
    whatsapp = db.Column(db.String(20))
    logo_url = db.Column(db.String(500))
    brand_color = db.Column(db.String(7), default='#00ffa3')

class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    # Index=True acelera a busca de clientes do usuário logado
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True, index=True) # Índice para filtrar ativos rapidamente

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)
    purchase_value = db.Column(db.Numeric(12, 2), default=0.00)
    rental_value = db.Column(db.Numeric(12, 2), default=0.00)

class Freelancer(db.Model):
    __tablename__ = 'freelancer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    daily_rate = db.Column(db.Numeric(12, 2), default=0.00)

class Budget(db.Model):
    __tablename__ = 'budget'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Dados do Cliente (Denormalizados para histórico)
    client = db.Column(db.String(100), nullable=False)
    client_cnpj = db.Column(db.String(20))
    client_phone = db.Column(db.String(20))
    client_address = db.Column(db.String(200))

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='Pendente', index=True)

    # Valores Financeiros
    labor_days = db.Column(db.Numeric(10, 2), default=0.00)
    margin_percent = db.Column(db.Integer, default=30)
    tax_percent = db.Column(db.Numeric(5, 2), default=0.00) 
    extra_cost = db.Column(db.Numeric(12, 2), default=0.00)
    total_cost = db.Column(db.Numeric(12, 2), default=0.00)
    final_price = db.Column(db.Numeric(12, 2), default=0.00)

    items = db.relationship('BudgetItem', backref='budget', lazy=True, cascade="all, delete-orphan")

    # ÍNDICES COMPOSTOS PARA DASHBOARD
    __table_args__ = (
        # Acelera query: "Meus orçamentos ordenados por data"
        Index('idx_budget_user_date', 'user_id', 'date'),
        # Acelera query: "Quantos orçamentos aprovados eu tenho?" (Dashboard Totals)
        Index('idx_budget_user_status', 'user_id', 'status'),
    )

class BudgetItem(db.Model):
    __tablename__ = 'budget_item'
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)
    item_type = db.Column(db.String(20))
    value = db.Column(db.Numeric(12, 2), default=0.00)
    days = db.Column(db.Numeric(10, 2), default=1.00)

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.item_type,
            'value': float(self.value) if self.value is not None else 0.0,
            'days': float(self.days) if self.days is not None else 1.0
        }