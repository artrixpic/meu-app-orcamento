from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_v9_crm_clientes'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cineorca.db'
db = SQLAlchemy(app)

# --- LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MODELOS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)

    config = db.relationship('UserConfig', backref='user', uselist=False, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True)
    equipments = db.relationship('Equipment', backref='user', lazy=True)
    freelancers = db.relationship('Freelancer', backref='user', lazy=True)
    clients = db.relationship('Client', backref='user', lazy=True) # NOVO

class UserConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    hourly_rate = db.Column(db.Float, default=0.0)
    monthly_goal = db.Column(db.Float, default=10000.0)
    company_name = db.Column(db.String(100), default="Minha Produtora")
    cnpj = db.Column(db.String(30))       
    address = db.Column(db.String(200))   
    whatsapp = db.Column(db.String(20))
    logo_url = db.Column(db.String(500))
    brand_color = db.Column(db.String(20), default="#00ffa3")

# NOVA TABELA DE CLIENTES
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))
    cnpj = db.Column(db.String(30))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))
    purchase_value = db.Column(db.Float)
    rental_value = db.Column(db.Float)

class Freelancer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(50))
    daily_rate = db.Column(db.Float)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    client = db.Column(db.String(100))
    client_cnpj = db.Column(db.String(30))      
    client_address = db.Column(db.String(200))  
    client_phone = db.Column(db.String(20))

    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    labor_days = db.Column(db.Float, default=1.0) 
    extra_cost = db.Column(db.Float, default=0.0)

    freelancer_total = db.Column(db.Float, default=0.0)
    equipment_total = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    final_price = db.Column(db.Float, default=0.0)
    margin_percent = db.Column(db.Integer, default=30)
    status = db.Column(db.String(20), default='Pendente')

    items = db.relationship('BudgetItem', backref='budget', lazy=True, cascade="all, delete-orphan")

    def get_items_json(self):
        data = [{'name': i.name, 'value': i.value, 'type': i.item_type} for i in self.items]
        return json.dumps(data)

class BudgetItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    name = db.Column(db.String(100))
    value = db.Column(db.Float)
    item_type = db.Column(db.String(20))

# --- FUNÇÕES ---
def safe_float(val):
    try: return float(val) if val else 0.0
    except: return 0.0

def safe_int(val, default=0):
    try: return int(float(val)) if val else default
    except: return default

# --- ROTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Email ou senha incorretos.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email já existe.', 'error')
            return redirect(url_for('register'))
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        db.session.add(UserConfig(user_id=new_user.id))
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('onboarding'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    config = current_user.config
    if request.method == 'POST':
        goal = safe_float(request.form.get('goal'))
        costs = safe_float(request.form.get('costs'))
        days = safe_int(request.form.get('days'), 20)
        if days == 0: days = 20
        hourly = ((goal + costs) / days) / 8
        if not config:
            config = UserConfig(user_id=current_user.id)
            db.session.add(config)
        config.monthly_goal = goal
        config.hourly_rate = hourly
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('onboarding.html')

@app.route('/dashboard')
@login_required
def dashboard():
    config = current_user.config
    if not config: return redirect(url_for('onboarding'))
    month = request.args.get('month', datetime.now().month, type=int)
    year = datetime.now().year
    budgets = Budget.query.filter_by(user_id=current_user.id).filter(db.extract('month', Budget.date) == month, db.extract('year', Budget.date) == year).order_by(Budget.date.desc()).all()
    total_approved = sum(b.final_price for b in budgets if b.status == 'Aprovado')
    total_pending = sum(b.final_price for b in budgets if b.status == 'Pendente')
    goal_percent = int((total_approved / config.monthly_goal) * 100) if config.monthly_goal > 0 else 0
    return render_template('dashboard.html', budgets=budgets, config=config, month=month, total_approved=total_approved, total_pending=total_pending, goal_percent=goal_percent)

@app.route('/status/<int:id>/<new_status>')
@login_required
def change_status(id, new_status):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id: return redirect(url_for('dashboard'))
    budget.status = new_status
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    config = current_user.config
    if request.method == 'POST':
        config.company_name = request.form['company_name']
        config.cnpj = request.form['cnpj']       
        config.address = request.form['address'] 
        config.whatsapp = request.form['whatsapp']
        config.logo_url = request.form['logo_url']
        config.brand_color = request.form['brand_color']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('settings.html', config=config)

# --- NOVA ROTA DE CLIENTES ---
@app.route('/clients', methods=['GET', 'POST'])
@login_required
def my_clients():
    if request.method == 'POST':
        db.session.add(Client(
            user_id=current_user.id,
            name=request.form['name'],
            cnpj=request.form['cnpj'],
            phone=request.form['phone'],
            address=request.form['address']
        ))
        db.session.commit()
        return redirect(url_for('my_clients'))
    return render_template('clients.html', clients=Client.query.filter_by(user_id=current_user.id).all())

@app.route('/clients/delete/<int:id>')
@login_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    if client.user_id == current_user.id:
        db.session.delete(client)
        db.session.commit()
    return redirect(url_for('my_clients'))

@app.route('/equipamentos', methods=['GET', 'POST'])
@login_required
def my_equipment():
    if request.method == 'POST':
        val = safe_float(request.form['value'])
        db.session.add(Equipment(user_id=current_user.id, name=request.form['name'], purchase_value=val, rental_value=val * 0.04))
        db.session.commit()
        return redirect(url_for('my_equipment'))
    return render_template('my_equipment.html', gears=Equipment.query.filter_by(user_id=current_user.id).all())

@app.route('/equipamentos/delete/<int:id>')
@login_required
def delete_equipment(id):
    gear = Equipment.query.get_or_404(id)
    if gear.user_id == current_user.id:
        db.session.delete(gear)
        db.session.commit()
    return redirect(url_for('my_equipment'))

@app.route('/freelas', methods=['GET', 'POST'])
@login_required
def freelancers():
    if request.method == 'POST':
        db.session.add(Freelancer(user_id=current_user.id, name=request.form['name'], role=request.form['role'], daily_rate=safe_float(request.form['daily_rate'])))
        db.session.commit()
        return redirect(url_for('freelancers'))
    return render_template('freelancers.html', freelas=Freelancer.query.filter_by(user_id=current_user.id).all())

@app.route('/freelas/delete/<int:id>')
@login_required
def delete_freelancer(id):
    freela = Freelancer.query.get_or_404(id)
    if freela.user_id == current_user.id:
        db.session.delete(freela)
        db.session.commit()
    return redirect(url_for('freelancers'))

@app.route('/orcamento/novo', methods=['GET', 'POST'])
@login_required
def new_budget(): return handle_budget_form(None)

@app.route('/orcamento/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_budget(id): 
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id: return redirect(url_for('dashboard'))
    return handle_budget_form(budget)

def handle_budget_form(budget):
    config = current_user.config
    if not config: return redirect(url_for('onboarding'))

    if request.method == 'POST':
        if not budget:
            budget = Budget(user_id=current_user.id)
            db.session.add(budget)
        else:
            for item in budget.items: db.session.delete(item)

        budget.client = request.form.get('client', '')
        budget.client_cnpj = request.form.get('client_cnpj', '')       
        budget.client_address = request.form.get('client_address', '') 
        budget.client_phone = request.form.get('client_phone', '')

        budget.title = request.form.get('title', '')
        budget.description = request.form.get('description', '')
        budget.labor_days = safe_float(request.form.get('labor_days'))
        budget.extra_cost = safe_float(request.form.get('extra_cost_input'))
        budget.margin_percent = safe_int(request.form.get('margin_range'), 30)

        items_json = request.form.get('items_json', '[]')
        items_data = json.loads(items_json)

        freela_sum = 0
        gear_sum = 0
        for item in items_data:
            new_item = BudgetItem(budget_id=budget.id, name=item['name'], value=item['value'], item_type=item['type'])
            budget.items.append(new_item)
            if item['type'] == 'freela': freela_sum += item['value']
            if item['type'] == 'gear': gear_sum += item['value']

        budget.freelancer_total = freela_sum
        budget.equipment_total = gear_sum

        base_daily = config.hourly_rate * 8
        total_cost = (base_daily * budget.labor_days) + budget.extra_cost + freela_sum + gear_sum
        budget.total_cost = total_cost
        budget.final_price = safe_float(request.form.get('final_price_input'))

        if not budget.status: budget.status = 'Pendente'

        db.session.commit()
        return redirect(url_for('dashboard'))

    # AQUI ESTÁ O TRUQUE: Passamos a lista de clients para o template
    return render_template(
        'budget_form.html', 
        config=config, 
        gears=Equipment.query.filter_by(user_id=current_user.id).all(), 
        freelas=Freelancer.query.filter_by(user_id=current_user.id).all(), 
        clients=Client.query.filter_by(user_id=current_user.id).all(), 
        budget=budget
    )

with app.app_context(): db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)