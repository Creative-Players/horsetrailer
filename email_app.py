from flask import Flask, redirect, request, session, url_for, render_template, send_file
from flask_session import Session
import secrets
import base64
import hashlib
import requests
import pandas as pd
import os
from bs4 import BeautifulSoup
from urllib.parse import urlencode

flask_app = Flask(__name__)  # Renamed the Flask application variable
flask_app.secret_key = os.urandom(24)
flask_app.config['SESSION_COOKIE_SAMESITE'] = 'None'
flask_app.config['SESSION_COOKIE_SECURE'] = True  # Only set this if using HTTPS

# Configure Flask-Session
flask_app.config['SESSION_TYPE'] = 'filesystem'  # You can choose other session types as well
Session(flask_app)

# Azure AD Application Configurations
CLIENT_ID = '8422262b-3977-4f51-a717-df6db38f1148'
CLIENT_SECRET = '1At8Q~wFk~4wdk3HosBGQMxNn5jBoVARSu902aJl'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTHORITY = 'https://login.microsoftonline.com/common'
SCOPE = ['User.Read', 'Mail.Read']

# Microsoft Graph API URLs
GRAPH_API_URL = 'https://graph.microsoft.com/v1.0/me/messages'

def get_access_token():
    if 'access_token' in session:
        return session['access_token']

    return None

def generate_code_verifier():
    """Generates a 'code_verifier' for PKCE."""
    token = secrets.token_urlsafe(64)
    return token

def generate_code_challenge(code_verifier):
    """Generates a 'code_challenge' based on the provided 'code_verifier'."""
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().replace("=", "")
    return code_challenge

def generate_state_parameter():
    """Generates a 'state' parameter for CSRF protection."""
    state = secrets.token_urlsafe(16)
    return state

def strip_html_tags(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

@flask_app.route('/')
def home():
    access_token = get_access_token()
    if access_token:
        return render_template('index.html', authenticated=True)
    return render_template('index.html', authenticated=False)

@flask_app.route('/login')
def login():
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = generate_state_parameter()

    # Store the code_verifier and state in the user's session for later use
    session['code_verifier'] = code_verifier
    session['state'] = state

    auth_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'response_mode': 'query',
        'redirect_uri': REDIRECT_URI,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': state,
        'scope': 'openid User.Read Mail.Read',  # Include necessary scopes
    }
    redirect_url = auth_url + urlencode(params)
    return redirect(redirect_url)

@flask_app.route('/callback')
def callback():
    print(session)
    if request.args.get('state') != session.get('state'):
        return 'State value did not match', 400

    code = request.args.get('code')
    if not code:
        return 'Code not found in the request', 400

    token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    body = {
        'client_id': CLIENT_ID,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': session.pop('code_verifier'),
        'client_secret':  CLIENT_SECRET
    }
    token_response = requests.post(token_url, headers=headers, data=body)

    if token_response.status_code == 200:
        token_data = token_response.json()
        session['access_token'] = token_data['access_token']
        return redirect(url_for('home'))
    else:
        # Log the error response for debugging
        print("Failed to fetch access token:")
        print("HTTP Status Code:", token_response.status_code)
        print("Response:", token_response.text)
        return f'Failed to fetch access token. Status code: {token_response.status_code}, Response: {token_response.text}'

@flask_app.route('/logout')
def logout():
    session.pop('access_token', None)
    return redirect(url_for('home'))

@flask_app.route('/export-emails')
def export_emails():
    access_token = get_access_token()
    if not access_token:
        return redirect(url_for('login'))

    query_params = "$select=subject,from,toRecipients,body"

    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(f"{GRAPH_API_URL}?{query_params}", headers=headers)

    if response.status_code == 200:
        emails = response.json()['value']
        for email in emails:
            email_body = email['body']['content']
            email['body'] = strip_html_tags(email_body) if email['body']['contentType'] == 'html' else email_body

        df = pd.DataFrame(emails)
        csv_filename = 'emails.csv'
        df.to_csv(csv_filename, index=False)
        return send_file(csv_filename, as_attachment=True, download_name='emails.csv', mimetype='text/csv')
    else:
        return f'Failed to fetch emails. Status code: {response.status_code}'

if __name__ == "__main__":
    flask_app.run(debug=True)
