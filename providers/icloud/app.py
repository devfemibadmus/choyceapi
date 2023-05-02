from flask import Flask, redirect, request
import requests
import json, os
from pathlib import Path
from urllib.parse import urlencode
BASE_DIR = Path(__file__).resolve().parent
CLIENT_ID = 'com.lendr.one'
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, 'secret.txt')

# Read client secret from file
with open(CLIENT_SECRET_FILE, 'r') as f:
    CLIENT_SECRET = f.read().strip()
# print(CLIENT_SECRET)
REDIRECT_URI = 'https://dev1.lendr.one/return'
SCOPE = 'https://www.icloud.com/auth/scopes/mail'


def icloud():
    # Check if user has already granted permission
    email = request.args.get('email')
    token_file = f'{email}.txt'
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = f.read()
    else:
        # Redirect user to permission page
        params = {
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPE,
        }
        auth_url = 'https://appleid.apple.com/auth/authorize'
        url = auth_url + '?' + urlencode(params)
        return redirect(url)

    # Use token to fetch user's emails
    api_url = 'https://api.icloud.com/emails/v4/mailboxes/inbox/messages'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(api_url, headers=headers)
    response_json = json.loads(response.text)
    emails = response_json['emails']

    # Render the fetched emails as HTML
    html = '<br>'.join([f'{e["subject"]} from {e["from"]["address"]}' for e in emails])
    return f'<html><body>{html}</body></html>'


def icloudcallback():
    # Obtain authorization code from callback URL
    code = request.args.get('code')

    # Exchange authorization code for access token
    params = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
    }
    token_url = 'https://appleid.apple.com/auth/token'
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
    }
    data = urlencode(params)
    response = requests.post(token_url, headers=headers, data=data)
    response_json = json.loads(response.text)
    access_token = response_json['access_token']

    # Get user's email
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get('https://api.icloud.com/system/user/v1/details', headers=headers)
    response_json = json.loads(response.text)
    email = response_json['appleId']

    # Save access token to file
    with open(f'{email}.txt', 'w') as f:
        f.write(access_token)

    # Redirect user back to home page
    return redirect(f'/icloud?email={email}')



