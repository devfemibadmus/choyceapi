from peupasswd import peupasswd
from pathlib import Path
from cryptography.fernet import Fernet
import imaplib, re, email, json, quopri, quopri, base64, os
from flask import Flask, redirect, request, render_template

BASE_DIR = Path(__file__).resolve().parent
secret = os.path.join(BASE_DIR, 'secret.json')
key = b'JHSVzLOcT9cdhIjZ0uWDNgfkOjnX7ELH6_us19Uszbo='

fernet = Fernet(key)

class SecretNotFoundException(Exception):
    pass

def add_secret(name, value):
    with open(secret, 'r') as f:
        secrets = json.load(f)
    
    encrypted_message = fernet.encrypt(value)
    secrets[name] = base64.urlsafe_b64encode(encrypted_message).decode()
    
    with open(secret, 'w') as f:
        json.dump(secrets, f)

def get_secret(name):
    with open(secret, 'r') as f:
        secrets = json.load(f)
    
    try:
        encrypted_message = base64.urlsafe_b64decode(secrets[name])
        decrypted_message = fernet.decrypt(encrypted_message).decode()  # Decode the decrypted bytes to string
    except KeyError:
        raise SecretNotFoundException(f'Secret "{name}" not found')
        
    return decrypted_message

def email_to_json(email_message):
    msg = email.message_from_string(email_message)
    msg_dict = {}
    for k, v in msg.items():
        msg_dict[k] = v
    msg_dict['body'] = msg.get_payload()
    return json.dumps(msg_dict)

def fetch_icloud_emails(username, password):
    # Connect to the iCloud IMAP server
    server = imaplib.IMAP4_SSL("imap.mail.me.com")

    # Login with the user's credentials
    server.login(username, password)

    # Select the INBOX mailbox
    server.select("inbox")

    # Search for all email messages
    status, messages = server.search(None, "ALL")

    data =[]

    if status == "OK":
        # Get the message IDs
        message_ids = messages[0].split()

        # Iterate over the message IDs
        for message_id in message_ids:
            # Fetch the email message by ID
            status, message_data = server.fetch(message_id, "(BODY.PEEK[HEADER])")
            statuss, message_bdy = server.fetch(message_id, "(BODY.PEEK[TEXT])")
            message_bdy = message_bdy[0][1]
            email_body = email.message_from_bytes(message_bdy).get_payload(decode=True)
            a = quopri.decodestring(email_body).decode('ISO-8859-1')
            #print(email_body)

            if status == "OK":
                # Get the raw email message data and print it
                if isinstance(message_data[0], tuple):
                    raw_email = message_data[0][1]
                else:
                    raw_email = message_data[0]
                if isinstance(raw_email, bytes):
                    raw_email = raw_email.decode('utf-8', errors='surrogateescape')
    
                # Parse the email message
                email_message = email_to_json(raw_email)

                email_message = json.loads(email_message)
                email_message['Body'] = a

                # Extract relevant information from the email message
                subject = email_message["Subject"]
                from_address = email_message["From"]
                to_address = email_message["To"]
                date = email_message["Date"]
                body = ""

                # Extract the body of the email message

                # Print the email details
                messages={
                    "subject": email_message['Subject'],
                    "from": email_message['From'],
                    "to": email_message['To'],
                    "date": email_message['Date'],
                    "body": email_message['Body'],
                }
                data.append(messages)
                #print(messages)

    # Logout and close the connection
    server.logout()
    return data



def icloud():
    return render_template('icloud.html')

def icloudmails():
    username = request.args.get('username')
    if request.args.get('username'):
        username = request.args.get('username')
        try:
            password = get_secret(username)
            print(password)
            data = fetch_icloud_emails(username, password)
        except SecretNotFoundException as e:
            if request.args.get('password'):
                password = request.args.get('password')
                add_secret(username, password.encode())
                print(password)
                data = fetch_icloud_emails(username, password)
            else:
                data = "404 user not found"
    else:
        data = "least username is required"
    return data

