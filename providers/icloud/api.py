from peupasswd import peupasswd
from pathlib import Path
import imaplib, re, email, json, quopri, quopri, base64, os
from flask import Flask, redirect, request, render_template
from main import get_db, app

BASE_DIR = Path(__file__).resolve().parent
secret = os.path.join(BASE_DIR, 'secret.json')

class SecretNotFoundException(Exception):
    pass


def add_secret(name, value):
    db = get_db()

    insert_query = '''
        INSERT OR REPLACE INTO providers (type, user, value)
        VALUES (?, ?, ?)
    '''
    db.execute(insert_query, ('icloud', name, value))
    db.commit()

def get_secret(name):
    db = get_db()

    select_query = '''
        SELECT value FROM providers
        WHERE type = 'icloud' AND user = ?
    '''
    result = db.execute(select_query, (name,)).fetchone()

    if result is None:
        raise SecretNotFoundException(f'Secret "{name}" not found')

    secret = result['value']
    return secret


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

def icloudmails(email, app_pass=None):
    username = email
    try:
        password = get_secret(username).decode()
        data = fetch_icloud_emails(username, password)
    except Exception as e:
        if app_pass != None:
            password = request.args.get('password')
            add_secret(username, password.encode())
            data = fetch_icloud_emails(username, password)
        else:
            data = "404 user not found"
    return data

