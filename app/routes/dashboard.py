import json
import calendar
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func

# IMPORTS CORRETOS
from app import db
from app.models import Budget, UserConfig
from app.utils import safe_decimal

# CRIAÇÃO DO BLUEPRINT
dashboard_bp = Blueprint('dashboard', __name__)

# --- NOVO: ROTA RAIZ (Redireciona para o dashboard) ---
@dashboard_bp.route('/')
def index():
    return redirect(url_for('dashboard.dashboard'))
# ------------------------------------------------------

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Usa getattr para segurança caso config seja None
    config = getattr(current_user, 'config', None)
    if not config: 
        return redirect(url_for('dashboard.onboarding'))

    month = request.args.get('month', datetime.now().month, type=int)
    year = datetime.now().year
    
    # Tratamento de erro para calendário
    last_day = calendar.monthrange(year, month)[1]
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    page = request.args.get('page', 1, type=int)

    base_query = Budget.query.filter(
        Budget.user_id == current_user.id, 
        Budget.date >= start_date, 
        Budget.date <= end_date
    )

    def get_total_sql(status_name):
        return db.session.query(func.coalesce(func.sum(Budget.final_price), 0.0)).filter(
            Budget.user_id == current_user.id, 
            Budget.date >= start_date, 
            Budget.date <= end_date, 
            Budget.status == status_name
        ).scalar()

    total_approved = float(get_total_sql('Aprovado'))
    total_pending = float(get_total_sql('Pendente'))
    total_lost = float(get_total_sql('Perdido'))

    goal = float(config.monthly_goal)
    goal_percent = int((total_approved / goal) * 100) if goal > 0 else 0

    pagination = base_query.order_by(Budget.date.desc()).paginate(page=page, per_page=10, error_out=False)

    # Query para o gráfico anual
    yearly_results = db.session.query(
        db.extract('month', Budget.date).label('month'),
        func.sum(Budget.final_price).label('total')
    ).filter(
        Budget.user_id == current_user.id,
        db.extract('year', Budget.date) == year,
        Budget.status == 'Aprovado'
    ).group_by(db.extract('month', Budget.date)).all()

    revenue_data = [0] * 12
    for m, total in yearly_results:
        revenue_data[int(m) - 1] = float(total)

    status_data = [total_approved, total_pending, total_lost]

    return render_template('dashboard.html', 
                           budgets=pagination.items, 
                           pagination=pagination, 
                           config=config, 
                           month=month, 
                           total_approved=total_approved, 
                           total_pending=total_pending, 
                           total_lost=total_lost, 
                           goal_percent=goal_percent,
                           revenue_data=json.dumps(revenue_data), 
                           status_data=json.dumps(status_data))

@dashboard_bp.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    config = getattr(current_user, 'config', None)
    
    if request.method == 'POST':
        goal = safe_decimal(request.form.get('goal'))
        costs = safe_decimal(request.form.get('costs'))
        days = safe_decimal(request.form.get('days'))
        
        if days == 0: days = Decimal('20.0')
        hourly = ((goal + costs) / days) / Decimal('8.0')

        if not config:
            config = UserConfig(user_id=current_user.id)
            db.session.add(config)
        
        config.monthly_goal = goal
        config.hourly_rate = hourly
        db.session.commit()
        
        return redirect(url_for('dashboard.dashboard'))
        
    return render_template('onboarding.html')

@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    config = getattr(current_user, 'config', None)
    
    if request.method == 'POST':
        if not config:
            config = UserConfig(user_id=current_user.id)
            db.session.add(config)
            
        config.company_name = request.form.get('company_name')
        config.cnpj = request.form.get('cnpj')        
        config.address = request.form.get('address') 
        config.whatsapp = request.form.get('whatsapp')
        config.logo_url = request.form.get('logo_url')
        config.brand_color = request.form.get('brand_color', '#00ffa3')
        
        db.session.commit()
        flash('Configurações atualizadas!', 'success')
        return redirect(url_for('dashboard.dashboard'))
        
    return render_template('settings.html', config=config)
