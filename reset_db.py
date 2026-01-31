from app import create_app, db
from sqlalchemy import text

app = create_app('default')

with app.app_context():
    print("Conectando ao banco de dados...")
    # 1. Apaga todas as tabelas definidas nos seus Models
    db.drop_all()
    
    # 2. Força a exclusão da tabela de versão do Alembic (que causa o erro)
    try:
        db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
        db.session.commit()
        print("Tabela alembic_version removida.")
    except Exception as e:
        print(f"Aviso: {e}")

    print("Banco de dados limpo com sucesso! Agora você pode criar as migrações.")
