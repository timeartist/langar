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
        checkins = CheckIn(**client).checkins_to_list()
    elif query is not None:
        results = Client.find(query)
        checkins = CheckIn().checkins_to_list()
    else:
        results = None
        checkins = CheckIn().checkins_to_list()

    totals = {'adults':0, 'minors':0, 'seniors':0}
    for checkin in checkins:
        totals['adults'] += int(checkin['adults'])
        totals['minors'] += int(checkin['minors'])
        totals['seniors'] += int(checkin['seniors'])

    return render_template('check_in.html', results=results, query=query, checkins=checkins, totals=totals, clients=Client.batch_to_dict())
    
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
    Client.batch_from_csv()
    app.run(debug=True)