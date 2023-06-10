from flask import Blueprint, g

from main import get_db

# Create a Blueprint for providers
provider_bp = Blueprint('provider', __name__, url_prefix='/providers')

@provider_bp.route('/')
def get_providers():
    db = get_db()
    providers = db.execute('SELECT * FROM providers').fetchall()
    return {'providers': [dict(row) for row in providers]}
