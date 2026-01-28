from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/onboarding')
def onboarding():
    return render_template('onboarding.html')

@app.route('/budget')
def budget_form():
    return render_template('budget_form.html')

@app.route('/equipment')
def my_equipment():
    return render_template('my_equipment.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
