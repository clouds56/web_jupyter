 #!/usr/bin/python3
# FLASK_APP=main.py FLASK_DEBUG=1 flask run

from flask import Flask
app = Flask(__name__)
app.debug = True

@app.route('/about')
def about_hello():
    return 'Hello, world'
