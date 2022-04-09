from json import dumps

from flask import Flask, render_template, request

from langar.models import Client

app = Flask(__name__)

@app.route('/')
@app.route('/register')
def register_get():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    client = Client(**request.form)
    client.save()
    print(client.__dict__)
    return render_template('register.html', success=True)

def run():
    app.run(debug=True)