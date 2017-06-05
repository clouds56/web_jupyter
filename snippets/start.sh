#!/usr/bin/sh

export PATH=$HOME/.local/bin:$PATH
FLASK_APP=$(pwd)/main.py FLASK_DEBUG=1 flask run --port 5088
# sudo -u html nginx -p. -c nginx.conf [-s reload]
