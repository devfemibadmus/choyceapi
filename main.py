import os
from flask import Flask, render_template, request
from providers.gmail.api import auth, auth_callback, getMail, getMails, create_file
app = Flask(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'
app.config['SECRET_KEY'] = 'django-insecure-^lcm&1+@pm&7q4i-tq0i^yrvgtlg1gxjbrq)o13al%+m^5c3b%'

@app.route('/')
def home():
    return render_template('index.html')

# =================================================== #
#                     GMAIL API START                 #
# =================================================== #

@app.route('/gmail')
@app.route('/gmail/auth')
def auth_user():
    return auth()

@app.route('/auth/callback/')
@app.route('/gmail/auth/callback/')
def callback():
    return auth_callback()

@app.route('/gmail/<email>/<length>')
def getmails(email, length):
    if length.isdigit():
        length = int(length)
        return getMails(email, length)
    else:
        id = length
        return getMail(email, id)

@app.route('/gmail/<email>')
def getmail(email):
    return getMails(email, None)

# =================================================== #
#                     GMAIL API END                   #
# =================================================== #




if __name__ == '__main__':
    app.run(port=8000)

