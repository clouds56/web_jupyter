import hmac
from getpass import getpass
import json

__name__ = "main"
salt = secret_key = open('%s.salt'%__name__, 'rb').read()

def generate(user_data, password):
    message = password.encode() + salt
    h = hmac.new(message, digestmod='sha1')
    h.update(message)
    digest = h.hexdigest()
    user_data['password'] = digest
    return json.dumps(user_data)

def make_user(filename, user_data=None):
    hint = user_data and "(%s)"%user_data or ""
    _user_data = input("user_data%s: "%hint)
    if _user_data.strip():
        user_data = json.loads(_user_data)
    if not isinstance(user_data, dict):
        raise Exception("Expecting dict: user_data is not dict")
    password = getpass()
    if len(password) < 6:
        print("password too simple")
        return (False, user_data)
    with open(filename, 'a') as f:
        print(generate(user_data, password), file=f)
        return (True, None)

output_filename = '%s.user'%__name__
user_data = None
success = False
while True:
    try:
        result, user_data = make_user(output_filename, user_data)
        if result:
            success = True
            print("write success")
    except (KeyboardInterrupt, EOFError) as e:
        print(e)
        break
    except Exception as e:
        print("!", e)
        continue
if success:
    print('please manually run "cat {0} >> {1}.users && rm {0}"'.format(output_filename, __name__))
