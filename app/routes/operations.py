from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user

# --- CORREÇÕES DE IMPORT ---
from app import db
from app.models import Client, Freelancer, Equipment
from app.utils import safe_decimal

# --- CRIAÇÃO DO BLUEPRINT ---
operations_bp = Blueprint('operations', __name__)

# ==============================================================================
# CLIENTES
# ==============================================================================
@operations_bp.route('/clients', methods=['GET', 'POST'])
@login_required
def my_clients():
    if request.method == 'POST':
        new_client = Client(
            user_id=current_user.id, 
            name=request.form.get('name'), 
            cnpj=request.form.get('cnpj'), 
            phone=request.form.get('phone'), 
            address=request.form.get('address'),
            # Checkbox: Se vier no form, é True. Se não, False. Default na criação é True.
            active=True if request.form.get('active') else True 
        )
        db.session.add(new_client)
        db.session.commit()
        flash('Cliente adicionado com sucesso!', 'success')
        return redirect(url_for('operations.my_clients'))

    # Lista todos os clientes do usuário
    return render_template('clients.html', clients=Client.query.filter_by(user_id=current_user.id).all())

@operations_bp.route('/clients/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    # SEGURANÇA: Filtra pelo ID e pelo Dono ao mesmo tempo
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        client.name = request.form.get('name')
        client.cnpj = request.form.get('cnpj')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')

        # CORREÇÃO DO CHECKBOX:
        # Checkboxes HTML só enviam a chave se estiverem marcados.
        # Se 'active' estiver no request.form, é True. Senão, vira False.
        client.active = True if request.form.get('active') else False

        db.session.commit()
        flash('Cliente atualizado!', 'success')
        return redirect(url_for('operations.my_clients'))

    return render_template('edit_client.html', client=client)

@operations_bp.route('/clients/delete/<int:id>', methods=['POST'])
@login_required
def delete_client(id):
    # SEGURANÇA: Só deleta se for do usuário logado
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    db.session.delete(client)
    db.session.commit()
    flash('Cliente removido.', 'info')
    return redirect(url_for('operations.my_clients'))

# ==============================================================================
# FREELANCERS
# ==============================================================================
@operations_bp.route('/freelas', methods=['GET', 'POST'])
@login_required
def freelancers():
    if request.method == 'POST':
        new_freela = Freelancer(
            user_id=current_user.id, 
            name=request.form.get('name'), 
            role=request.form.get('role'), 
            daily_rate=safe_decimal(request.form.get('daily_rate'))
        )
        db.session.add(new_freela)
        db.session.commit()
        flash('Freelancer adicionado!', 'success')
        return redirect(url_for('operations.freelancers'))

    return render_template('freelancers.html', freelas=Freelancer.query.filter_by(user_id=current_user.id).all())

@operations_bp.route('/freelas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_freelancer(id):
    # SEGURANÇA
    freela = Freelancer.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        freela.name = request.form.get('name')
        freela.role = request.form.get('role')
        freela.daily_rate = safe_decimal(request.form.get('daily_rate'))

        db.session.commit()
        flash('Freelancer atualizado!', 'success')
        return redirect(url_for('operations.freelancers'))

    return render_template('edit_freelancer.html', freela=freela)

@operations_bp.route('/freelas/delete/<int:id>', methods=['POST'])
@login_required
def delete_freelancer(id):
    # SEGURANÇA
    freela = Freelancer.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    db.session.delete(freela)
    db.session.commit()
    flash('Freelancer removido.', 'info')
    return redirect(url_for('operations.freelancers'))

# ==============================================================================
# EQUIPAMENTOS
# ==============================================================================
@operations_bp.route('/equipamentos', methods=['GET', 'POST'])
@login_required
def my_equipment():
    if request.method == 'POST':
        new_gear = Equipment(
            user_id=current_user.id, 
            name=request.form.get('name'), 
            purchase_value=safe_decimal(request.form.get('purchase_value')), 
            rental_value=safe_decimal(request.form.get('rental_value'))
        )
        db.session.add(new_gear)
        db.session.commit()
        flash('Equipamento adicionado!', 'success')
        return redirect(url_for('operations.my_equipment'))

    return render_template('my_equipment.html', equipments=Equipment.query.filter_by(user_id=current_user.id).all())

@operations_bp.route('/equipamentos/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    # SEGURANÇA
    gear = Equipment.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        gear.name = request.form.get('name')
        gear.purchase_value = safe_decimal(request.form.get('purchase_value'))
        gear.rental_value = safe_decimal(request.form.get('rental_value'))

        db.session.commit()
        flash('Equipamento atualizado!', 'success')
        return redirect(url_for('operations.my_equipment'))

    return render_template('edit_equipment.html', gear=gear)

@operations_bp.route('/equipamentos/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    # SEGURANÇA
    gear = Equipment.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    db.session.delete(gear)
    db.session.commit()
    flash('Equipamento removido.', 'info')
    return redirect(url_for('operations.my_equipment'))

# ==============================================================================
# API (JSON)
# ==============================================================================
@operations_bp.route('/api/quick_save_client', methods=['POST'])
@login_required
def quick_save_client():
    data = request.get_json(silent=True)
    if not data: 
        return jsonify({'success': False, 'error': 'Payload inválido'}), 400

    name = str(data.get('name', '')).strip()
    if not name: 
        return jsonify({'success': False, 'error': 'Nome obrigatório'}), 400

    # Verifica se já existe para este usuário
    existing = Client.query.filter_by(user_id=current_user.id, name=name).first()
    if existing: 
        # Se existe, retorna os dados dele e avisa que já existia (opcional)
        return jsonify({'success': True, 'id': existing.id, 'name': existing.name, 'is_existing': True})

    new_client = Client(
        user_id=current_user.id, 
        name=name, 
        cnpj=str(data.get('cnpj',''))[:20], 
        phone=str(data.get('phone',''))[:20], 
        address=str(data.get('address',''))[:200],
        active=True # Cliente criado no orçamento entra como ativo
    )

    db.session.add(new_client)
    db.session.commit()

    return jsonify({'success': True, 'id': new_client.id, 'name': new_client.name})