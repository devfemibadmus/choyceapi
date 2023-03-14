from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(host='37.221.193.135', port=80)

