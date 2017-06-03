 #!/usr/bin/python3
# FLASK_APP=main.py FLASK_DEBUG=1 flask run

import os
import fcntl
from flask import Flask, request, make_response, render_template_string, redirect, current_app
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import hmac
import json
import collections
import urllib
import secrets
import string

app = Flask(__name__)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
app.debug = True

import subprocess

def random_string(n, characters=string.ascii_letters + string.digits):
    return ''.join([secrets.choice(characters) for _ in range(n)])

def install_secret_key(filename='secret_key'):
    #filename = os.path.join(app.instance_path, filename)
    try:
        secret_key = open(filename, 'rb').read()
    except IOError:
        secret_key = None
    if secret_key:
        return secret_key
    print('create secret file')
    secret_key_string = random_string(24)
    with open(filename, 'wb') as secret_file:
        secret_file.write(secret_key_string.encode())
    secret_key = open(filename, 'rb').read()
    if not secret_key:
        print('still cannot read %s'%filename)
        sys.exit(1)
    return secret_key
app.config['SECRET_KEY'] = install_secret_key("%s.secret_key"%__name__)

class User(UserMixin):
    salt = install_secret_key("%s.salt"%__name__)
    users = {}
    def __init__(self, t):
        self.id = t['id']
        self.data = t
    def valid(self, password):
        message = password.encode() + self.salt
        h = hmac.new(message, digestmod='sha1')
        h.update(message)
        digest = h.hexdigest()
        if not hmac.compare_digest(self.data['password'], digest):
            print("Digest: ", digest)
            return False
        return True;
    # h = hmac.new(app.config['SECRET_KEY'], digestmod='sha256')
    # h.update(salt)
    # @classmethod
    # def valid_token(cls, message, token):
    #     h = cls.h.clone()
    #     h.update(message.decode())
    #     return hmac.compare_digest(token, h.hexdigest())

def load_users(filename='users'):
    users = {}
    with open(filename, 'r') as f:
        for line in f:
            user = User(json.loads(line))
            users[user.id] = user
    return users
User.users = load_users("%s.users"%__name__)

@login_manager.user_loader
def load_user(id):
    return User.users.get(id)

about_links = []
header_template = """
<div>
{% if not current_user.is_authenticated %}
    <span><a href='/login?next={{current_url}}'>/login</a></span>
{% else %}
    <span>{{current_user.data.id}} <a href='/logout'>/logout</a></span>
{% endif %}
{% for link in links %}
    <span><a href='{{link}}'>{{link}}</a></span>
{% endfor %}
</div>
{{body|safe}}
"""

about_message = """
GET  /about         show usage
GET  /list          show all list
GET  /add           show add form
POST /add {path}    new jupyter instance at path
GET  /kill          show kill form
POST /kill {pid}    kill the instance of pid
GET  /notebooks/<port>  redirect to /p/<id>/init/<port>
GET  /p/<id>/signup     Set-Cookie and redirect

PROXY /p/<id>/*     forward using jupyter_port cookie
"""

def render_template_string_with_header(*args, **kwargs):
    return render_template_string(header_template, links=about_links, body=render_template_string(*args, **kwargs))

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template_string_with_header('<div>CSRF Error: {{reason}}</div>', reason=e.description), 400

@app.errorhandler(401)
def unauthorized_error(e):
    return render_template_string_with_header('<div>Unauthorized: {{reason}}</div>', reason=e.description), 401

login_template = """
{% if message %}
<div>{{ message }}</div>
{% endif %}
{% if not current_user.is_authenticated %}
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <input type='text' name='username'>
    <input type='password' name='password'>
    <input type='submit' value='login'>
</form>
{% else %}
<div>
    Hello, {{ current_user.data.id }}
    <a href='/logout'>logout</a>
</div>
{% endif %}
"""

@app.route("/login", methods=("get", "post"))
def login():
    message = None
    if request.method.upper() == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.users.get(username)
        if not user:
            message = "username not exist"
        elif user.valid(password):
            login_user(user)
            next = request.args.get("next")
            if not next:
                next = '/list'
            return redirect(next)
        else:
            message = "wrong password"
    return render_template_string_with_header(login_template, message=message)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/about')
@login_required
def about_hello():
    if request.values.get('t') == 'json':
        return json.dumps({'text': about_message, 'api': about_links, 'options': request.query_string.decode()})
    return render_template_string_with_header("<div>{% for m in message.strip().splitlines() %}{{m}}<br>{% endfor %}</div>", message=about_message)

def run_command(*args, verbose=True, **kwargs):
    if verbose:
        print("RUN", args, kwargs)
    result = subprocess.run(*args, stdout=subprocess.PIPE, **kwargs)
    return result.stdout.decode('utf-8')

notebook_keys = ['base_url', 'hostname', 'notebook_dir', 'password', 'pid', 'port', 'secure', 'token', 'url']

def list_notebooks():
    return [json.loads(x) for x in run_command(['jupyter', 'notebook', 'list', '--json'], verbose=False).splitlines()]

list_template = """
{% if message %}
<div>{{ message }}</div>
{% endif %}
<table>
    <thead>
        <th>open</th>
        {% for key in keys %}<th>{{key}}</th>{% endfor %}
        <th>kill</th>
    </thead>
    <tbody>
    {% for notebook in notebooks %}
        <tr>
            <td><a href='/notebooks/{{notebook.port}}'>@</a></td>
            {% for value in notebook._values %}<td>{{value}}</td>{% endfor %}
            <td>
                <form action='/kill' method='post' style='margin-bottom: 0'>
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <input name='pid' type='text' value='{{notebook.pid}}' hidden>
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
@login_required
def api_list():
    notebooks = list_notebooks()
    if request.values.get('t') == 'json':
        return json.dumps(list_notebooks())
    message = request.args.get('m')
    if message:
        try:
            message = message.format(**request.form.to_dict())
        except:
            message = 'build message "%s" failed' % message
    return render_template_string_with_header(list_template,
                message = message,
                keys = notebook_keys,
                notebooks = [{'_values':[x[k] for k in notebook_keys], **x} for x in notebooks])

def redirect_to_list(message):
    return redirect('/list?' + urllib.parse.urlencode({'m': message}), code=307)

kill_template = """
<form method='post'>
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <input name='pid' type='text'>
    <input type='submit' value='kill'>
</form>
"""

@app.route('/kill', methods=('get', 'post'))
@login_required
def api_kill():
    pid = request.form.get('pid')
    if not pid:
        return render_template_string_with_header(kill_template)
    notebooks = list_notebooks()
    pid = int(pid)
    result = "failed, notebook for the pid not found"
    for notebook in notebooks:
        if pid == notebook['pid']:
            result = run_command(['kill', '%d'%pid])
            if result == "":
                result = "successfully"
            break

    if request.values.get('t') == 'json':
        return json.dumps({'result': result})
    return redirect_to_list('kill {pid} %s'%result)

add_template = """
{% if message %}
<div>{{ message }}</div>
{% endif %}
<form method='post'>
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <input name='path' type='text' placeholder='path' autofocus
    {% if path %}value="{{path}}"{% endif %}
    >
    <input type='submit' value='add'>
</form>
"""

def non_block_read(output):
    # Note: only works in linux
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read().decode('utf-8')
    except:
        return ""

@app.route('/add', methods=('get', 'post'))
@login_required
def api_add():
    path = request.form.get('path')
    orig_path = path
    if path and not os.path.isabs(path):
        path = os.path.join(os.path.expanduser('~'), path)
    if not path or not os.path.exists(path):
        message = orig_path and "%s is not a valid path" % orig_path
        return render_template_string_with_header(add_template, message = message, path = orig_path)
    result = "failed"
    prefix = random_string(6, string.ascii_lowercase + string.digits)
    add_args = ['jupyter', 'lab', '--no-browser', '--LabApp.base_url=/p/%s'%prefix]
    print("RUN", add_args)
    proc = subprocess.Popen(add_args, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        proc.wait(0.5)
        result = "failed"
    except subprocess.TimeoutExpired:
        result = "successfully"
    if request.values.get('t') == 'json':
        out, err = non_block_read(proc.stdout), non_block_read(proc.stderr)
        return json.dumps({'result': result, 'pid': proc.pid, 'returncode': proc.returncode, 'args': proc.args, 'stdout': out, 'stderr': err})
    return redirect_to_list('add {path} %s'%result)

@app.route('/notebooks/<int:port>')
@login_required
def api_notebook(port):
    notebooks = list_notebooks()
    for notebook in notebooks:
        if port == notebook['port']:
            base_url = notebook['base_url']
            if not base_url.startswith('/'):
                base_url = '/' + base_url
            return redirect('%s'%base_url+"signup")
    return redirect_to_list('open %d failed, notebook for the pid not found'%port)

@app.route('/p/<notebook_id>/signup')
@login_required
def api_signup(notebook_id):
    notebooks = list_notebooks()
    base_url = '/p/%s/' % notebook_id
    for notebook in notebooks:
        if base_url == notebook['base_url']:
            response = make_response(redirect('%s?'%base_url+urllib.parse.urlencode({'token': notebook['token']})))
            response.set_cookie('jupyter_port', "%d"%notebook['port'], path=base_url)
            return response
    return redirect_to_list('signup %d failed, notebook for the pid not found'%port)

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

with app.app_context():
    adapter = current_app.url_map.bind('')
    about_links = [adapter.build(rule.endpoint, **(rule.defaults or {})) for rule in current_app.url_map.iter_rules() if "GET" in rule.methods and has_no_empty_params(rule)]
    about_links = [link for link in about_links if link != '/login' and link != '/logout']
