    import os
    from app import create_app

    # Define o ambiente padrão como 'production' se a variável não existir
    # Isso garante segurança máxima no deploy (Fail-Fast)
    env = os.getenv('FLASK_ENV', 'production')

    # Cria a aplicação usando a fábrica que você definiu
    app = create_app(env)

    if __name__ == "__main__":
        app.run()