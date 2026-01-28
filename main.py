from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_mvp_cineorca'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cineorca.db'
db = SQLAlchemy(app)

# --- MODELOS DO BANCO DE DADOS ---

class UserConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hourly_rate = db.Column(db.Float, default=0.0)
    monthly_goal = db.Column(db.Float)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    purchase_value = db.Column(db.Float)
    rental_value = db.Column(db.Float) # Sugestão automática

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.String(100))
    title = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total_cost = db.Column(db.Float)
    final_price = db.Column(db.Float)
    margin_percent = db.Column(db.Integer)
    status = db.Column(db.String(20), default='Rascunho')

# --- ROTAS ---

@app.route('/')
def index():
    # Verifica se o usuário já configurou sua vida financeira
    config = UserConfig.query.first()
    if not config:
        return redirect(url_for('onboarding'))
    return redirect(url_for('dashboard'))

@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if request.method == 'POST':
        goal = float(request.form['goal'])
        costs = float(request.form['costs'])
        days = int(request.form['days'])

        # Lógica da Calculadora de Vida
        daily_needed = (goal + costs) / days
        hourly = daily_needed / 8 # Baseado em 8h diárias

        config = UserConfig.query.first()
        if not config:
            config = UserConfig(monthly_goal=goal, hourly_rate=hourly)
            db.session.add(config)
        else:
            config.monthly_goal = goal
            config.hourly_rate = hourly

        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('onboarding.html')

@app.route('/dashboard')
def dashboard():
    budgets = Budget.query.order_by(Budget.date.desc()).all()
    config = UserConfig.query.first()
    equip_count = Equipment.query.count()
    return render_template('dashboard.html', budgets=budgets, config=config, equip_count=equip_count)

@app.route('/equipamentos', methods=['GET', 'POST'])
def my_equipment():
    if request.method == 'POST':
        name = request.form['name']
        value = float(request.form['value'])
        # Regra de Ouro: 4% do valor para aluguel
        rental = value * 0.04 

        new_gear = Equipment(name=name, purchase_value=value, rental_value=rental)
        db.session.add(new_gear)
        db.session.commit()
        return redirect(url_for('my_equipment'))

    gears = Equipment.query.all()
    return render_template('my_equipment.html', gears=gears)

@app.route('/equipamentos/delete/<int:id>')
def delete_equipment(id):
    gear = Equipment.query.get_or_404(id)
    db.session.delete(gear)
    db.session.commit()
    return redirect(url_for('my_equipment'))

@app.route('/orcamento/novo', methods=['GET', 'POST'])
def new_budget():
    config = UserConfig.query.first()
    gears = Equipment.query.all()

    if request.method == 'POST':
        # Salvar orçamento (Simplificado para o MVP)
        b = Budget(
            client=request.form['client'],
            title=request.form['title'],
            total_cost=float(request.form['total_cost_input']),
            final_price=float(request.form['final_price_input']),
            margin_percent=int(request.form['margin_range']),
            status='Gerado'
        )
        db.session.add(b)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('budget_form.html', config=config, gears=gears)

# Inicializa o Banco de Dados se não existir
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)