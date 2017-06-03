 #!/usr/bin/python3
# FLASK_APP=main.py FLASK_DEBUG=1 flask run

import os
from flask import Flask, request, render_template_string, redirect
import json
import collections
import urllib
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
{% if message %}
<div>{{ message|e }}</div>
{% endif %}
<table>
    <thead>
        {% for key in keys %}<th>{{key|e}}</th>{% endfor %}
        <th>kill</th>
    </thead>
    <tbody>
    {% for notebook in notebooks %}
        <tr>
            {% for value in notebook._values %}<td>{{value|e}}</td>{% endfor %}
            <td>
                <form action='/kill' method='post'>
                    <input name='pid' type='text' value='{{notebook.pid|e}}' hidden>
                    <input type='submit' value='X'>
                </form>
            </td>
        </tr>
    {% endfor %}
    </tbody>
</table>
<div><a href='/add'>new instance</a></div>
"""

@app.route('/list', methods=('get', 'post'))
def api_list():
    notebooks = list_notebooks()
    if request.args.get('t') == 'json':
        return json.dumps(list_notebooks())
    message = request.args.get('m')
    if message:
        message = message.format(**request.form.to_dict())
    return render_template_string(list_template,
                                  message = message,
                                  keys = notebook_keys,
                                  notebooks = [{'_values':[x[k] for k in notebook_keys], **x} for x in notebooks])

def redirect_to_list(message):
    return redirect('/list?' + urllib.parse.urlencode({'m': message}), code=307)

kill_template = """
<form action='/kill' method='post'>
    <input name='pid' type='text'>
    <input type='submit' value='kill'>
</form>
"""

@app.route('/kill', methods=('get', 'post'))
def api_kill():
    pid = request.form.get('pid')
    print(pid)
    if not pid:
        return kill_template
    notebooks = list_notebooks()
    pid = int(pid)
    result = "failed"
    for notebook in notebooks:
        if pid == notebook['pid']:
            result = run_command(['kill', '%d'%pid])
            break
    return redirect_to_list('kill {pid} %s'%result)

add_template = """
{% if message %}
<div>{{ message|e }}</div>
{% endif %}
<form action='/add' method='post'>
    <input name='path' type='text' placeholder='path' autofocus
    {% if path %}value="{{path|e}}"{% endif %}
    >
    <input type='submit' value='add'>
</form>
"""

@app.route('/add', methods=('get', 'post'))
def api_add():
    path = request.form.get('path')
    orig_path = path
    if path and not os.path.isabs(path):
        path = os.path.join(os.path.expanduser('~'), path)
    if not path or not os.path.exists(path):
        message = orig_path and "%s is not a valid path" % orig_path
        return render_template_string(add_template, message = message, path = orig_path)
    result = "failed"
    proc = subprocess.Popen(['jupyter', 'lab', '--no-browser'], cwd=path)
    try:
        proc.wait(0.5)
        result = "failed"
    except subprocess.TimeoutExpired:
        result = "success"
    return redirect_to_list('add {path} %s'%result)
