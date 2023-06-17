from pathlib import Path
import imaplib, re, email, json, quopri, quopri, base64, os
from flask import Flask, redirect, request, render_template
from database.db import get_db
from email import policy
from email.parser import BytesParser

BASE_DIR = Path(__file__).resolve().parent
secret = os.path.join(BASE_DIR, 'secret.json')

class SecretNotFoundException(Exception):
    pass


def add_secret(user, value):
    db = get_db()

    select_query = '''
        SELECT * FROM providers WHERE type = 'icloud' AND user = ?
    '''
    row = db.execute(select_query, (user,)).fetchone()

    if row is None:
        insert_query = '''
            INSERT INTO providers (type, user, value) VALUES (?, ?, ?)
        '''
        db.execute(insert_query, ('icloud', user, value))
    else:
        update_query = '''
            UPDATE providers SET value = ? WHERE type = 'icloud' AND user = ?
        '''
        db.execute(update_query, (value, user))
    
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


def get_text_plain(email_message):
    if email_message.is_multipart():
        for part in email_message.iter_parts():
            if part.get_content_type() == 'text/plain':
                return part.get_content()
    else:
        return email_message.get_content()

def fetch_icloud_emails(username, password):
    # Connect to the iCloud IMAP server
    server = imaplib.IMAP4_SSL("imap.mail.me.com")

    # Login with the user's credentials
    server.login(username, password)

    # Select the INBOX mailbox
    server.select("inbox")

    # Search for all email messages
    status, messages = server.search(None, "ALL")

    data = []

    if status == "OK":
        # Get the message IDs
        message_ids = messages[0].split()

        # Iterate over the message IDs
        for message_id in message_ids:
            # Fetch the email message by ID
            status, message_bdy = server.fetch(message_id, "(BODY[])")
            status, message_data = server.fetch(message_id, "(BODY.PEEK[HEADER])")
            raw_email = message_bdy[0][1]
            email_message = email.message_from_bytes(raw_email, policy=policy.default)
            body = get_text_plain(email_message)
            if body is not None:
                body = ' '.join(body.splitlines())
            #print(body)

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

                # Extract the body of the email message

                # Print the email details
                #print("No Error")
                messages={
                    "subject": email_message['Subject'],
                    "from": email_message['From'],
                    "to": email_message['To'],
                    "date": email_message['Date'],
                    "body": body,
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
        print(e)
        print("ERROR")
        if app_pass != None:
            password = request.args.get('password')
            add_secret(username, password.encode())
            data = fetch_icloud_emails(username, password)
        else:
            data = "404 user not found, Signin"
    return data

