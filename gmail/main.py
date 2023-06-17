import os, sqlite3
from flask import Flask
from database.db import get_db, initialize_database, app

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'
app.config['SECRET_KEY'] = 'flask-insecure-^lcm&1+@pm&7q4i-tq0i^yrvgtlg1gxjbrq)o13al%+m^5c3b%'
app.config['DATABASE'] = 'database/db.sqlite3'
app.config['SCHEMA'] = 'database/schema.sql'

@app.cli.command('initdb')
def initdb_command():
    initialize_database()
    print('Initialized the database.')



# Import and register routes
from provider.index_routes import index_bp
from provider.gmail_routes import gmail_bp

app.register_blueprint(index_bp)
app.register_blueprint(gmail_bp)

if __name__ == '__main__':
    #app.run(host='localhost', port=80, debug=True)
    app.run(host='0.0.0.0', port=8080, debug=True)
    #app.run(host='0.0.0.0', debug=True, port=443, ssl_context=('/home/choyce/choyce_cert/cert.pem', '/home/choyce/choyce_cert/privkey.pem'))
