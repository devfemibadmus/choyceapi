import json, re, os
from google.auth.transport import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from google.oauth2.credentials import Credentials
from django.urls import reverse
import os
from lastnerd.settings import BASE_DIR
import base64
from email import message_from_bytes
from email.header import decode_header


def home(request):
    # Check if the user is authenticated with Google
    if 'google_auth' not in request.session:
        return redirect('auth')

    # Get the user's credentials from the Django session
    credentials_dict = json.loads(request.session['google_auth'])
    credentials = Credentials.from_authorized_user_info(credentials_dict, scopes=['https://www.googleapis.com/auth/gmail.readonly'])

    try:
        # Authenticate and build the Gmail API client
        service = build('gmail', 'v1', credentials=credentials)

        # Call the Gmail API to retrieve the user's messages
        messages_data = service.users().messages().list(userId='me', maxResults=13).execute()

        # Get the next set of messages (if any)
        next_page_token = messages_data.get('nextPageToken')
        if next_page_token:
            next_messages_data = service.users().messages().list(userId='me', maxResults=20, pageToken=next_page_token).execute()

        messages = []

        # Loop through each message and extract the required fields
        for message in next_messages_data['messages']:
            message_data = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            message_date = next(item['value'] for item in message_data['payload']['headers'] if item['name'] == 'Date')
            message_subject = next(item['value'] for item in message_data['payload']['headers'] if item['name'] == 'Subject')
            
            # Get the label IDs for the message
            label_ids = message_data['labelIds']
    
            # Call the Gmail API to retrieve the label information
            labels = service.users().labels().list(userId='me').execute()
    
            # Loop through the labels and find the label with the matching ID
            for label in labels['labels']:
                if label['id'] in label_ids:
                    message_label = label['name']
                    break
            
            # Traverse the parts list to find the text/plain part containing the message body
            parts = message_data['payload'].get('parts')
            message_body = ''
            if parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        message_body = base64.urlsafe_b64decode(message_body.encode('ASCII')).decode('utf-8')
                        break

            messages.append({'id': message['id'], 'threadId': message['threadId'], 'date': message_date, 'subject': message_subject, 'label': message_label, 'body': message_body})


        # Pass the messages to the template for rendering
        return render(request, 'home.html', {'messages': messages})
    except HttpError as error:
        # Handle any errors that occur during the API request
        return render(request, 'error.html', {'error': error})

def auth(request):
    flow = Flow.from_client_secrets_file(
        os.path.join(BASE_DIR, 'last_nerd.json'),
        scopes=['https://www.googleapis.com/auth/gmail.readonly'],
        redirect_uri=request.build_absolute_uri('/auth/callback/'),
    )

    # Generate the Google OAuth 2.0 authorization URL
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')

    # Store the state in the Django session for later validation
    request.session['oauth_state'] = state

    # Redirect the user to the Google OAuth 2.0 authentication page
    return redirect(authorization_url)

def auth_callback(request):
    # Validate the OAuth 2.0 state parameter
    if 'oauth_state' not in request.session or request.GET.get('state', '') != request.session['oauth_state']:
        return render(request, 'error.html', {'error': 'Invalid state parameter'})

    # Exchange the authorization code for a Google OAuth 2.0 access token
    flow = Flow.from_client_secrets_file(
        os.path.join(BASE_DIR, 'last_nerd.json'),
        scopes=['https://www.googleapis.com/auth/gmail.readonly'],
        redirect_uri=request.build_absolute_uri('/auth/callback/'),
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    # Store the user's credentials in the Django session
    request.session['google_auth'] = credentials.to_json()

    # Redirect the user back to the home page
    return redirect('home')

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

def message_detail(request, message_id):
    # Get the user's credentials from the Django session
    credentials_dict = json.loads(request.session['google_auth'])
    credentials = Credentials.from_authorized_user_info(credentials_dict, scopes=['https://www.googleapis.com/auth/gmail.readonly'])

    try:
        # Authenticate and build the Gmail API client
        service = build('gmail', 'v1', credentials=credentials)

        

        # Call the Gmail API to retrieve the user's message
        message_data = service.users().messages().get(userId='me', id=message_id, format='full').execute()

        # Decode the message body and subject
        message_parts = message_data['payload']['parts']
        message_bytes = base64.urlsafe_b64decode(message_parts[0]['body']['data'] + '===')

        message = message_from_bytes(message_bytes)
        body = get_message_body(message)
        subject = get_decoded_header(str(message['Subject']))

        # Pass the message to the template for rendering
        return render(request, 'message_detail.html', {'body': body, 'subject': subject})
    except HttpError as error:
        # Handle any errors that occur during the API request
        return render(request, 'error.html', {'error': error})
