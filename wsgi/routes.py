# -*- coding: utf-8 -*-
import os
from flask import Flask, Response, url_for

instancepath = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instancepath)
app.config['PROPAGATE_EXCEPTIONS'] = True

db_url = os.environ.get('OPENSHIFT_MYSQL_DB_URL', None)
if db_url:
    db_url = db_url.replace("mysql", "mysql+mysqldb")
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    print(db_url)
else:
    print("OPENSHIFT_MYSQL_DB_URL not found.")

db = SQLAlchemy(app)


# The '/' page is accessible to anyone
@app.route('/')
def home():
    return "Hello world!"
