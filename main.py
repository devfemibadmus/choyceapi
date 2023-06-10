import os
from flask import Flask, g
import sqlite3

app = Flask(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'
app.config['SECRET_KEY'] = 'flask-insecure-^lcm&1+@pm&7q4i-tq0i^yrvgtlg1gxjbrq)o13al%+m^5c3b%'
app.config['DATABASE'] = 'database/db.sqlite3'
app.config['SCHEMA'] = 'database/schema.sql'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def initialize_database():
    with app.app_context():
        db = get_db()
        with app.open_resource(app.config['SCHEMA'], mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    initialize_database()
    print('Initialized the database.')



# Import and register routes
from routes.index_routes import index_bp
from routes.gmail_routes import gmail_bp
from routes.icloud_routes import icloud_bp
from routes.outlook_routes import outlook_bp
from routes.provider_routes import provider_bp

app.register_blueprint(provider_bp)
app.register_blueprint(index_bp)
app.register_blueprint(icloud_bp)
app.register_blueprint(gmail_bp)
app.register_blueprint(outlook_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=443, ssl_context=('/home/choyce/choyce_cert/cert.pem', '/home/choyce/choyce_cert/privkey.pem'))
