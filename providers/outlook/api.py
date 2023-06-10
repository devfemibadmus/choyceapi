from azure.identity import ClientSecretCredential
from msal import PublicClientApplication, ConfidentialClientApplication
import requests, os, json, time, html
from pathlib import Path
from flask import Flask, request, redirect, session, url_for
from bs4 import BeautifulSoup
BASE_DIR = Path(__file__).resolve().parent

# Azure AD app credentials
CLIENT_ID = 'b48b87e5-b328-4aa9-850e-d62a6b551b25'
CLIENT_SECRET = 'Sl68Q~~pXYvhp_texZF_nj~0JgeD9SFqb5fnpbfH'
TENANT_ID = 'common'

# Microsoft Graph API endpoints
GRAPH_URL = 'https://graph.microsoft.com/v1.0'
ME_URL = GRAPH_URL + '/me'
MESSAGES_URL = 'https://graph.microsoft.com/v1.0/me/mailfolders/inbox/messages'

REDIRECT_URI = 'http://37.221.193.135:8000/outlook/redirect'

# Initialize the Azure AD app credentials
credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)

# Initialize the Microsoft Graph API client
msal_app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=f'https://login.microsoftonline.com/{TENANT_ID}'
)

# functions
def create_file(user, content):
    file = os.path.join(BASE_DIR, 'test_users/'+user+'.json')
    with open(file, 'w') as file:
        file.write(content)
        
# refresh token
def refresh_token(email):
    with open(os.path.join(BASE_DIR, 'test_users/'+email+'.json'), 'r') as f:
        refresh_token = f.read()

    response = requests.post(
        'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        data={
            'client_id': 'your_client_id_here',
            'client_secret': 'your_client_secret_here',
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'scope': 'https://graph.microsoft.com/.default'
        }
    )
    access_token = response.json()['access_token']
    create_file(email, access_token)

    return access_token



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
    create_file(result['id_token_claims']['preferred_username'], result['access_token'])

    return redirect("/outlook/"+result['id_token_claims']['preferred_username'])

# Function to fetch a mail using the authenticated access token
def o_getMail(email, message_id):
    file = os.path.join(BASE_DIR, 'test_users/'+email+'.json')
    with open(file, 'r') as f:
        access_token = f.read()
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
    file = os.path.join(BASE_DIR, 'test_users/'+email+'.json')
    with open(file, 'r') as f:
        access_token = f.read()
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
        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/messages?$select=id,receivedDateTime,subject,sender,bodyPreview&$top='+length,
            headers={
                'Authorization': 'Bearer ' + access_token,
                'Accept': 'application/json'
            }
        )
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


