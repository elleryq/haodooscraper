# -*- coding: utf-8 -*-
import os
from flask import (Flask, Response, url_for, render_template,
                   request)
from flask.ext.bootstrap import Bootstrap
from flask.ext.jsontools import jsonapi, DynamicJSONEncoder
from haodooscraper.model import Volume
from pagination import Pagination


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


PAGE_SIZE = 10
instancepath = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instancepath)
app.json_encoder = DynamicJSONEncoder
app.config['PROPAGATE_EXCEPTIONS'] = True
if "DEBUG" in os.environ:
    app.debug = os.environ['DEBUG'].lower() == "true"
else:
    app.debug = False
Bootstrap(app)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


def get_page():
    page_str = request.args.get('page', '1')
    try:
        page = int(page_str)
    except ValueError:
        page = 1
    return page


# The '/' page is accessible to anyone
@app.route('/')
def home():
    q = request.args.get('q', '')
    page = get_page()
    volumes = Volume.query(q)
    return render_template("index.html",
                           volumes=volumes,
                           q=q,
                           pagination=Pagination(page, PAGE_SIZE, volumes))


@app.route('/json')
@jsonapi
def query():
    q = request.args.get('q', None)
    page = get_page()
    volumes = Volume.query(q)
    pagination = Pagination(page, PAGE_SIZE, volumes)
    return {'results': list(pagination.items())}


@app.route('/api')
def api():
    return render_template("api.html")
