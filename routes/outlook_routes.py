from flask import Blueprint

from providers.outlook.api import o_auth, o_auth_callback, o_getMail, o_getMails

outlook_bp = Blueprint('outlook', __name__, url_prefix='/outlook')

@outlook_bp.route('/')
def o_auth_user():
    return o_auth()

@outlook_bp.route('/redirect/')
def o_callback():
    return o_auth_callback()

@outlook_bp.route('/<email>')
def o_getmail(email):
    return o_getMails(email, length='10')

@outlook_bp.route('/<email>/<length>')
def o_getmails(email, length):
    if length.isdigit():
        return o_getMails(email, length)
    else:
        id = length
        return o_getMail(email, id)
