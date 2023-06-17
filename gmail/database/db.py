from flask import g, Flask
import sqlite3

app = Flask(__name__, template_folder="../templates")

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

