from main import app, db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    # Verifica se a tabela existe
    if 'budget_item' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('budget_item')]
        print("\n--- DIAGNÓSTICO DO BANCO NEON ---")
        print(f"Colunas encontradas na tabela 'budget_item': {columns}")

        if 'days' in columns:
            print("✅ SUCESSO: A coluna 'days' JÁ EXISTE no banco!")
            print("Você pode rodar o sistema, não precisa de migração.")
        else:
            print("❌ AVISO: A coluna 'days' NÃO ESTÁ no banco.")
            print("O Alembic está confuso. Vamos forçar a criação.")
    else:
        print("❌ A tabela 'budget_item' nem sequer existe ainda.")