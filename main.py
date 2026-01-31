from app import create_app, db
from app.models import User, Budget, Client, Freelancer, Equipment

app = create_app('default')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Budget': Budget,
        'Client': Client,
        'Freelancer': Freelancer,
        'Equipment': Equipment
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
