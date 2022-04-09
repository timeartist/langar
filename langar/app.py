from json import dumps

from flask import Flask, render_template, request

from langar.models import Client

app = Flask(__name__)

@app.route('/')
def registration():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    print(request.form)
    client = Client(**request.form)
    return (client.__dict__)

def run():
    app.run(debug=True)