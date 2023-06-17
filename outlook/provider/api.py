from azure.identity import ClientSecretCredential
from msal import PublicClientApplication, ConfidentialClientApplication
import requests, os, json, time, html, msal
from pathlib import Path
from flask import Flask, request, redirect, session, url_for
from bs4 import BeautifulSoup
from database.db import get_db
BASE_DIR = Path(__file__).resolve().parent

# Azure AD app credentials
CLIENT_ID = 'b48b87e5-b328-4aa9-850e-d62a6b551b25'
CLIENT_SECRET = 'Sl68Q~~pXYvhp_texZF_nj~0JgeD9SFqb5fnpbfH'
TENANT_ID = 'common'

# Microsoft Graph API endpoints
GRAPH_URL = 'https://graph.microsoft.com/v1.0'
ME_URL = GRAPH_URL + '/me'
MESSAGES_URL = 'https://graph.microsoft.com/v1.0/me/mailfolders/inbox/messages'

REDIRECT_URI = 'http://localhost/outlook/redirect'

SCOPE = ['https://graph.microsoft.com/Mail.Read', 'https://graph.microsoft.com/User.Read.All']

# Initialize the Azure AD app credentials
credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)

# Initialize the Microsoft Graph API client
msal_app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=f'https://login.microsoftonline.com/{TENANT_ID}'
)

class SecretNotFoundException(Exception):
    pass


def add_secret(user, value):
    db = get_db()

    select_query = '''
        SELECT * FROM providers WHERE type = 'outlook' AND user = ?
    '''
    row = db.execute(select_query, (user,)).fetchone()

    if row is None:
        insert_query = '''
            INSERT INTO providers (type, user, value) VALUES (?, ?, ?)
        '''
        db.execute(insert_query, ('outlook', user, value))
    else:
        update_query = '''
            UPDATE providers SET value = ? WHERE type = 'outlook' AND user = ?
        '''
        db.execute(update_query, (value, user))
    
    db.commit()

def get_secret(name):
    db = get_db()

    select_query = '''
        SELECT value FROM providers
        WHERE type = 'outlook' AND user = ?
    '''
    result = db.execute(select_query, (name,)).fetchone()

    if result is None:
        raise SecretNotFoundException(f'Secret "{name}" not found')

    secret = result['value']
    return secret

# refresh token
def refresh_token(email):
    try:
        print("asdfghjkl")
        refresh_token = get_secret(email + "_refresh")  # get refresh token
    except SecretNotFoundException:
        return "404 user not found, Signin"
    
    result = msal_app.acquire_token_by_refresh_token(
        refresh_token=refresh_token,
        scopes=['https://graph.microsoft.com/Mail.Read', 'https://graph.microsoft.com/User.Read.All'],
    )
    if "access_token" in result:
        access_token = result["access_token"]
        add_secret(email + "_access", access_token)  # store new access token
        return access_token
    else:
        print(result.get("error"))

    return None

# Function to initiate user authentication
def o_auth():
    auth_url = msal_app.get_authorization_request_url(
        scopes=['https://graph.microsoft.com/Mail.Read'],
        redirect_uri=REDIRECT_URI,
        authority=f'https://login.microsoftonline.com/{TENANT_ID}'
    )
    return redirect(auth_url)

# Function to handle redirect after user authentication
def o_auth_callback():
    code = request.args.get('code')
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=['https://graph.microsoft.com/Mail.Read', 'https://graph.microsoft.com/User.Read.All'],
        redirect_uri=REDIRECT_URI
    )
    username = result['id_token_claims']['preferred_username']
    access_token = result['access_token']
    refresh_token = result['refresh_token']  # get refresh token from the result

    add_secret(username + "_access", access_token)  # store access token
    add_secret(username + "_refresh", refresh_token)  # store refresh token

    return redirect("/outlook/"+username)


# Function to fetch a mail using the authenticated access token
def o_getMail(email, message_id):
    try:
        access_token = get_secret(email + "_access")
    except SecretNotFoundException as e:
        return "404 user not found, Signin"
    response = requests.get(
        'https://graph.microsoft.com/v1.0/me/messages/'+message_id+'?$select=id,receivedDateTime,subject,sender,body',
        headers={
            'Authorization': 'Bearer ' + access_token,
            'Accept': 'application/json'
        }
    )
    #print(response.status_code)
    if response.status_code == 401:  # Access token expired
        access_token = refresh_token(email)
        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/messages/'+message_id+'?$select=id,receivedDateTime,subject,sender,body/content',
            headers={
                'Authorization': 'Bearer ' + access_token,
                'Accept': 'application/json'
            }
        )
    message = response.json()
    message_date = message['receivedDateTime']
    message_subject = message['subject']
    message_sender = message['sender']
    message_body = message['body']['content']
    message_body = BeautifulSoup(message_body, 'html.parser').get_text()
    message_label = message['singleValueExtendedProperties'][0]['value'] if 'singleValueExtendedProperties' in message else None
    result = {'id': message['id'], 'date': message_date, 'subject': message_subject, 'sender': message_sender, 'body': message_body, 'label': message_label}
    return result

# Function to fetch messages using the authenticated access token
def o_getMails(email, length):
    try:
        access_token = get_secret(email + "_access")
    except SecretNotFoundException as e:
        return "404 user not found, Signin"
    response = requests.get(
        'https://graph.microsoft.com/v1.0/me/messages?$select=id,receivedDateTime,subject,sender,bodyPreview&$top='+length,
        headers={
            'Authorization': 'Bearer ' + access_token,
            'Accept': 'application/json'
        }
    )
    #print(response.status_code)
    if response.status_code == 401:  # Access token expired
        access_token = refresh_token(email)
        print(access_token)
        print("access_token")
        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/messages?$select=id,receivedDateTime,subject,sender,bodyPreview&$top='+length,
            headers={
                'Authorization': 'Bearer ' + access_token,
                'Accept': 'application/json'
            }
        )
    print(response)
    messages = response.json()['value']
    result = []
    for message in messages:
        message_date = message['receivedDateTime']
        message_subject = message['subject']
        sender = message['sender']
        snippet = message['bodyPreview']
        snippet = snippet.replace("\r\n", "")
        snippet = snippet.encode().decode('unicode_escape')
        result.append({'id': message['id'], 'date': message_date, 'sender':sender, 'subject': message_subject, 'snippet': snippet})
    return result


