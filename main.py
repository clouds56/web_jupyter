 #!/usr/bin/python3
# FLASK_APP=main.py FLASK_DEBUG=1 flask run

from flask import Flask, request, render_template_string
import json
import collections
app = Flask(__name__)
app.debug = True

import subprocess

def run_command(*args, **kargs):
    result = subprocess.run(*args, stdout=subprocess.PIPE, **kargs)
    return result.stdout.decode('utf-8')


@app.route('/about')
def about_hello():
    return 'Hello, world'


notebook_keys = ['base_url', 'hostname', 'notebook_dir', 'password', 'pid', 'port', 'secure', 'token', 'url']

def list_notebooks():
    return [json.loads(x) for x in run_command(['jupyter', 'notebook', 'list', '--json']).splitlines()]

list_template = """
<table>
    <thead>
        {% for key in keys %}<th>{{key}}</th>{% endfor %}
    </thead>
    <tbody>
    {% for notebook in notebooks %}
        <tr>
            {% for value in notebook._values %}<td>{{value}}</td>{% endfor %}
        </tr>
    {% endfor %}
    </tbody>
</table>
"""

@app.route('/list')
def api_list():
    notebooks = list_notebooks()
    if request.args.get('t') == 'json':
        return json.dumps(list_notebooks())
    return render_template_string(list_template,
                                  keys = notebook_keys,
                                  notebooks = [{'_values':[x[k] for k in notebook_keys], **x} for x in notebooks])
