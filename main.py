import os
from markupsafe import escape
from flask import Flask, render_template, request
from providers.gmail.api import auth, auth_callback, getMail, getMails
from providers.outlook.api import o_auth, o_auth_callback, o_getMail, o_getMails
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


# ===================================================== #
#                      OUTLOOK API START                #
# ===================================================== #

@app.route('/outlook')
def o_auth_user():
    return o_auth()

@app.route('/outlook/redirect/')
def o_callback():
    return o_auth_callback()

@app.route('/outlook/<email>')
def o_getmail(email):
    return o_getMails(email, length='10')

@app.route('/outlook/<email>/<length>')
def o_getmails(email, length):
    if length.isdigit():
        return o_getMails(email, length)
    else:
        id = length
        return o_getMail(email, id)

# ===================================================== #
#                       OUTLOOK API end                 #
# ===================================================== #




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=443, ssl_context=('/home/choyce/choyce_cert/cert.pem', '/home/choyce/choyce_cert/privkey.pem'))

