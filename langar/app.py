from os import urandom, environ
from pydoc import cli

import requests
from flask import Flask, render_template, request, redirect, Response
from flask_login import LoginManager, login_user, login_required, logout_user
from oauthlib.oauth2 import WebApplicationClient

from langar.models import Client, CheckIn, CheckIns, User, UserNotFoundException, reset_db

ALLOWED_EMAIL_DOMAIN = environ.get('ALLOWED_EMAIL_DOMAIN', 'nederlandfoodpantry.org')
GOOGLE_CLIENT_ID = environ.get('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_CLIENT_SECRET = environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
GOOGLE_PROVIDER_CONF = requests.get(GOOGLE_DISCOVERY_URL).json()

WAC = WebApplicationClient(GOOGLE_CLIENT_ID)

app = Flask(__name__)
app.secret_key = urandom(24)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

_redirect_url_base = lambda: request.base_url.replace('http://', 'https://')

@lm.user_loader
def load_user(id):
    try:
        print(f'getting user {id}')
        user = User.from_id(id)
        print(user.get_id())
        return user
    except UserNotFoundException:
        return None

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    print('login start')
    authorization_endpoint = GOOGLE_PROVIDER_CONF["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google

    request_uri = WAC.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=_redirect_url_base() + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    print('callback start')
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    token_endpoint = GOOGLE_PROVIDER_CONF["token_endpoint"]
    
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = WAC.prepare_token_request(
        token_endpoint,
        authorization_response=request.url.replace('http://', 'https://'),
        redirect_url=_redirect_url_base(),
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    
    WAC.parse_request_body_response(token_response.text)
    
    userinfo_endpoint = GOOGLE_PROVIDER_CONF["userinfo_endpoint"]
    uri, headers, body = WAC.add_token(userinfo_endpoint)
    userinfo = requests.get(uri, headers=headers, data=body).json()
    
    if userinfo['email'].lower().endswith(ALLOWED_EMAIL_DOMAIN):
        user = User(**userinfo)
        print(f'found {user}')
        login_user(user)
        print('user logged in - redirecting')
        return redirect('/')
    else:
        return Response(status=503)

@app.route("/logout")
@login_required
def logout():
    print('logout start')
    logout_user()
    return redirect('https://accounts.google.com/Logout')


@app.route('/')
@app.route('/check-in')
@login_required
def check_in_get():
    print('check-in get start')
    query = request.args.get('query')
    id = request.args.get('id')
    results = None
    client = None

    ## checking in client path
    if id is not None:
        _results = Client.find(f'@id:{id}')
        client = _results[0]
        checkins = CheckIn().checkins_to_list()
        existing_checkin_ids = [checkin['id'] for checkin in checkins]
        if id not in existing_checkin_ids:
            checkins = CheckIn(**client).checkins_to_list()
    ## finding client path
    elif query is not None:
        if '"' not in query:
            _query = f'{query}*'
        else:
            _query = query
        results = Client.find(_query)
        checkins = CheckIn().checkins_to_list()
    ## default path
    else:
        checkins = CheckIn().checkins_to_list()
    
    checkins.reverse()
    totals = _get_totals(checkins)

    return render_template('check_in.html', results=results, query=query, checkins=checkins, totals=totals, clients=Client.batch_to_dict(), client=client)
    
@app.route('/register')
@login_required
def register_get():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
@login_required
def register_post():
    client = Client(**request.form)
    client.save()
    CheckIn(**client.__dict__)
    return render_template('register.html', success=True)

@app.route('/download/<string:what>')
@login_required
def download(what:str):
    if what.lower() == 'today':
        checkin = CheckIn()
        return Response(checkin.stream_file(), mimetype='text/csv', headers={"content-disposition":"attachment; filename=" + checkin.file.split('/')[-1]})
    else:
        checkins = CheckIns()
        what_split = what.split('-')
        
        if len(what_split) == 2:
            return Response(checkins.stream_month_file(what), mimetype='text/csv')
        elif len(what_split) == 3:
            return Response(checkins.stream_day_file(what), mimetype='text/csv')
        else:
            return Response(status_code=404)

@app.route('/reports')
@login_required
def reports():
    checkins = CheckIns()
    _type =  request.args.get('type', '')
    if _type == 'daily':
        selected = request.args.get('when-daily')
        checkins_list = checkins.day_list(selected)
    elif _type == 'monthly':
        selected = request.args.get('when-monthly')
        checkins_list = checkins.month_list(selected)
    else:
        checkins_list = checkins.month_list(checkins.months[0])
        selected = ''

    totals = _get_totals(checkins_list)
    
    return render_template('reports.html', months=checkins.months, days=checkins.days, checkins=checkins_list, totals=totals, selected=selected, type=_type)

def _get_totals(checkins):
    totals = {'adults':0, 'minors':0, 'seniors':0}
    for checkin in checkins:
        totals['adults'] += int(checkin['adults'])
        totals['minors'] += int(checkin['minors'])
        totals['seniors'] += int(checkin['seniors'])

    return totals

def run():
    reset_db()
    app.run(debug=True, ssl_context="adhoc")