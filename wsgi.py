#!/usr/bin/env python
import os
from flask import Flask


app = Flask(__name__)


# The '/' page is accessible to anyone
@app.route('/')
def home():
    return "Hello world!"


#
# Main
#
if __name__ == '__main__':
    ip = os.environ['OPENSHIFT_PYTHON_IP']
    port = int(os.environ['OPENSHIFT_PYTHON_PORT'])

    app.run(host=ip, port=port)
