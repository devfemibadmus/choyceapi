import json, os, base64, re
from pathlib import Path
from bs4 import BeautifulSoup
from email import message_from_bytes
from email.header import decode_header
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from flask import Flask, redirect, render_template, request, session

BASE_DIR = Path(__file__).resolve().parent

# Google OAuth 2.0 configuration
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'credential.json')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'
REDIRECT_URI = 'http://localhost:8000/auth/callback/'

# website authentication
def auth():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    #print(state)
    #print("Hi")
    session['oauth_state'] = state
    return redirect(authorization_url)
# website authentication call back
def auth_callback():
    state = session['oauth_state']
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI, state=state)
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    try:
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        email = profile['emailAddress']
        create_file(email, credentials.to_json())
        return email+" is authenticated"
    except HttpError as error:
        return "An error occurred, do the authentication again"
# get all mails from user
def getMails(email, length):
    # Get the user's credentials from the Flask session
    file = os.path.join(BASE_DIR, 'test_users/'+email+'.json')
    with open(file, 'r') as f:
        credentials_dict = json.load(f)

    #print(credentials_dict)
    credentials = Credentials.from_authorized_user_info(credentials_dict, scopes=SCOPES)

    try:
        # Authenticate and build the Gmail API client
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

        # Call the Gmail API to retrieve the user's messages
        messages_data = service.users().messages().list(userId=email, maxResults=length).execute()
        messages = []

        # Loop through each message and extract the required fields
        for message in messages_data['messages']:
            message_data = service.users().messages().get(userId=email, id=message['id'], format='full').execute()
            message_date = next(item['value'] for item in message_data['payload']['headers'] if item['name'] == 'Date')
            message_subject = next(item['value'] for item in message_data['payload']['headers'] if item['name'] == 'Subject')
            snippet = message_data['snippet'].encode('ascii', 'ignore').decode('ascii').encode('utf-8').decode('unicode_escape')

            messages.append({'id': message['id'], 'date': message_date, 'subject': message_subject, 'snippet': snippet})

        # Pass the messages to the template for rendering
        return messages
    except HttpError as error:
        # Handle any errors that occur during the API request
        return error
# get detail mail from user
def getMail(email, id):
    # Get the user's credentials from the Flask session
    file = os.path.join(BASE_DIR, 'test_users/'+email+'.json')
    with open(file, 'r') as f:
        credentials_dict = json.load(f)
    #print(credentials_dict)
    credentials = Credentials.from_authorized_user_info(credentials_dict, scopes=SCOPES)

    try:
        # Authenticate and build the Gmail API client
        service = build('gmail', 'v1', credentials=credentials)
        # Call the Gmail API to retrieve the user's message
        message_data = service.users().messages().get(userId='me', id=id, format='full').execute()
        # Decode the message body and subject
        message_parts = message_data['payload']['parts']
        message_bytes = base64.urlsafe_b64decode(message_parts[0]['body']['data'] + '===')

        message = message_from_bytes(message_bytes)
        #print(message_parts)
        body = get_message_body(message)

        mail = {'body': body, 'id': id}

        # Pass the message to the template for rendering
        return mail
    except HttpError as error:
        # Handle any errors that occur during the API request
        return error



# functions
def create_file(user, content):
    file = os.path.join(BASE_DIR, 'test_users/'+user+'.json')
    with open(file, 'w') as file:
        file.write(content)

def get_decoded_header(header):
    """Decode an email header value and return a Unicode string."""
    value, encoding = decode_header(header)[0]
    if encoding:
        return value.decode(encoding)
    else:
        return value

def get_message_body(message):
    """Extract the body text from a MIME message object."""
    if message.is_multipart():
        # If the message contains multiple parts, recurse into the parts
        for part in message.get_payload():
            body = get_message_body(part)
            if body:
                return body
    else:
        # If the message is not multipart, get the text/plain part
        if message.get_content_type() == 'text/plain':
            body = message.get_payload(decode=True).decode('utf-8')
            return body

