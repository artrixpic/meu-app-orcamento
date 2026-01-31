import os
from app import create_app, db

# Pega a config do ambiente ou usa 'default' (desenvolvimento)
config_name = os.getenv('FLASK_CONFIG') or 'default'

app = create_app(config_name)

# Isso ajuda no comando 'flask shell' para você testar coisas no terminal
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, app=app)

if __name__ == '__main__':
    app.run()