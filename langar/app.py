from flask import Flask, render_template, request

from langar.models import Client, CheckIn

app = Flask(__name__)

@app.route('/')
@app.route('/check-in')
def check_in_get():
    query = request.args.get('query')
    id = request.args.get('id')

    if id is not None:
        results = Client.find(f'@id:{id}')
        client = results[0]
        CheckIn(**client)
    elif query is not None:
        results = Client.find(query)
    else:
        results = None

    return render_template('check_in.html', results=results, query=query)
    
@app.route('/register')
def register_get():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    client = Client(**request.form)
    client.save()
    CheckIn(**client.__dict__)
    return render_template('register.html', success=True)

def run():
    Client.batch_from_json()
    app.run(debug=True)