# -*- coding: utf-8 -*-
import os
from flask import (Flask, Response, url_for, render_template,
                   request)
from flask.ext.jsontools import jsonapi, DynamicJSONEncoder
from haodooscraper.model import Volume


instancepath = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instancepath)
app.json_encoder = DynamicJSONEncoder
app.config['PROPAGATE_EXCEPTIONS'] = True


# The '/' page is accessible to anyone
@app.route('/')
def home():
    q = request.args.get('q', None)
    if q:
        volumes = Volume.query_by_title_or_author(q)
    else:
        volumes = Volume.query_all()
    return render_template("index.html",
                           volumes=volumes,
                           q=q)


@app.route('/query')
@jsonapi
def query():
    q = request.args.get('q', None)
    if q:
        volumes = Volume.query_by_title_or_author(q)
    else:
        volumes = Volume.query_all()
    return {'results': volumes}
    #return {'results': "Hello world"}
