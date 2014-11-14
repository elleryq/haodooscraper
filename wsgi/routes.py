# -*- coding: utf-8 -*-
import os
from flask import Flask, Response, url_for, render_template, jsonify
import json
from haodooscraper.model import Volume


instancepath = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instancepath)
app.config['PROPAGATE_EXCEPTIONS'] = True


# The '/' page is accessible to anyone
@app.route('/')
def home():
    volumes = Volume.query_all()
    return render_template("index.html", count=len(volumes))


@app.route('/query')
def query():
    return jsonify(results=[])
