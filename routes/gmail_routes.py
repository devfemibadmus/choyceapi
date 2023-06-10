from flask import Blueprint

from providers.gmail.api import auth, auth_callback, getMail, getMails

gmail_bp = Blueprint('gmail', __name__, url_prefix='/gmail')

@gmail_bp.route('/')
def auth_user():
    return auth()

@gmail_bp.route('/auth/callback/')
def callback():
    return auth_callback()

@gmail_bp.route('/<email>')
def getmail(email):
    return getMails(email, None)

@gmail_bp.route('/<email>/<length>')
def getmails(email, length):
    if length.isdigit():
        length = int(length)
        return getMails(email, length)
    else:
        id = length
        return getMail(email, id)
