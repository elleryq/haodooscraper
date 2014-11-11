# -*- coding: utf-8 -*-
import os
from flask import Flask, Response, url_for

instancepath = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instancepath)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}'.format(
        os.environ['OPENSHIFT_MYSQL_DB_USERNAME'],
        os.environ['OPENSHIFT_MYSQL_DB_PASSWORD'],
        os.environ['OPENSHIFT_MYSQL_DB_HOST'],
        os.environ['OPENSHIFT_MYSQL_DB_PORT'])
db = SQLAlchemy(app)


# The '/' page is accessible to anyone
@app.route('/')
def home():
    return "Hello world!"
