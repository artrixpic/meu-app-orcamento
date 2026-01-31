import json
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Budget, BudgetItem, Client, Freelancer, Equipment
from app.utils import safe_decimal

def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default

budget_bp = Blueprint('budget', __name__)

@budget_bp.route('/orcamento/novo', methods=['GET', 'POST'])
@login_required
def new_budget(): 
    return handle_budget_form(None)

@budget_bp.route('/orcamento/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_budget(id): 
    # Busca segura (Anti-IDOR)
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return handle_budget_form(budget)

def handle_budget_form(budget):
    config = getattr(current_user, 'config', None)
    if not config: 
        return redirect(url_for('dashboard.onboarding'))

    if request.method == 'POST':
        # 1. Captura dados do formulário PRIMEIRO
        client_name = request.form.get('client', '').strip()
        title = request.form.get('title', '').strip()

        # Validação básica para evitar erro de banco
        if not client_name or not title:
            flash("Cliente e Título do projeto são obrigatórios.", "error")
            return redirect(request.url)

        # 2. Se for novo, cria a instância já com os dados obrigatórios
        if not budget:
            budget = Budget(
                user_id=current_user.id,
                client=client_name,
                title=title
            )
            db.session.add(budget)
            # Agora o flush funciona, pois client e title não são null
            db.session.flush() 
        else:
            # Se for edição, atualiza os campos e limpa itens antigos
            budget.client = client_name
            budget.title = title
            for item in budget.items: 
                db.session.delete(item)

        # 3. Preenche o restante dos dados
        budget.client_cnpj = request.form.get('client_cnpj', '')[:20]
        budget.client_phone = request.form.get('client_phone', '')[:20]
        budget.client_address = request.form.get('client_address', '')[:200]
        budget.description = request.form.get('description', '')

        budget.labor_days = safe_decimal(request.form.get('labor_days'))
        budget.margin_percent = safe_int(request.form.get('margin_range'), 30)
        budget.tax_percent = safe_decimal(request.form.get('tax_percent'))

        try:
            items_json_str = request.form.get('items_json', '[]')
            if not items_json_str: items_json_str = '[]'
            items_data_json = json.loads(items_json_str)
            if not isinstance(items_data_json, list): raise ValueError
        except:
            db.session.rollback()
            flash("Erro ao processar itens do orçamento.", "error")
            return redirect(url_for('dashboard.dashboard'))

        items_cost_sum = Decimal('0.00')

        for item in items_data_json:
            days = safe_decimal(item.get('days', 1))
            val = safe_decimal(item.get('value', 0))
            name = str(item.get('name', 'Item')).strip()
            item_type = str(item.get('type', 'Outro'))

            new_item = BudgetItem(
                budget_id=budget.id, name=name, value=val, item_type=item_type, days=days 
            )
            db.session.add(new_item)
            items_cost_sum += (val * days)

        hourly_rate = safe_decimal(config.hourly_rate) if config.hourly_rate else safe_decimal('0.00')
        daily_rate = hourly_rate * safe_decimal('8.00')

        labor_days_dec = safe_decimal(request.form.get('labor_days'))
        budget.labor_days = labor_days_dec
        labor_cost = labor_days_dec * daily_rate

        extra_cost = safe_decimal(request.form.get('extra_cost_input'))
        budget.extra_cost = extra_cost

        total_cost = labor_cost + extra_cost + items_cost_sum
        budget.total_cost = total_cost

        margin_dec = Decimal(budget.margin_percent) / Decimal(100)
        tax_dec = budget.tax_percent / Decimal(100)
        markup_factor = margin_dec + tax_dec
        divisor = Decimal(1) - markup_factor

        if divisor > Decimal('0.01'):
            budget.final_price = total_cost / divisor
        else:
            budget.final_price = total_cost 

        if not budget.status: budget.status = 'Pendente'

        db.session.commit()
        return redirect(url_for('dashboard.dashboard'))

    items_data = []
    if budget and budget.items:
        items_data = [item.to_dict() for item in budget.items]

    return render_template('budget_form.html', 
                           config=config, 
                           gears=Equipment.query.filter_by(user_id=current_user.id).all(), 
                           freelas=Freelancer.query.filter_by(user_id=current_user.id).all(), 
                           clients=Client.query.filter_by(user_id=current_user.id, active=True).all(), 
                           budget=budget,
                           items_data=items_data) 

@budget_bp.route('/orcamento/print/<int:id>', methods=['GET'])
@login_required
def print_budget(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('print_budget.html', budget=budget, config=current_user.config)

@budget_bp.route('/status/<int:id>/<new_status>', methods=['POST'])
@login_required
def change_status(id, new_status):
    if new_status not in ['Pendente', 'Aprovado', 'Perdido']: 
        return redirect(url_for('dashboard.dashboard'))

    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    budget.status = new_status
    db.session.commit()
    return redirect(url_for('dashboard.dashboard'))