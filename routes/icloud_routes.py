from flask import Blueprint

from providers.icloud.api import icloud, icloudmails

icloud_bp = Blueprint('icloud', __name__, url_prefix='/icloud')

@icloud_bp.route('/')
def icld():
    return icloud()

@icloud_bp.route('/<email>')
def icldreturn(email):
    return icloudmails(email, None)

@icloud_bp.route('/<email>/<app_pass>')
def icldreturns(email, app_pass):
    return icloudmails(email, app_pass)
