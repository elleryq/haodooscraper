#!/usr/bin/env python
import os


#def execfile(afile, globalz=None, localz=None):
#    with open(afile, "r") as fh:
#        exec(fh.read(), globalz, localz)
#
#virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
#virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
#try:
#    execfile(virtualenv, dict(__file__=virtualenv))
#except IOError:
#    pass


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
