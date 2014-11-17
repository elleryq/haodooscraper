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


PAGE_SIZE = 20
instancepath = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instancepath)
app.json_encoder = DynamicJSONEncoder
app.config['PROPAGATE_EXCEPTIONS'] = True
Bootstrap(app)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


# The '/' page is accessible to anyone
@app.route('/')
def home():
    q = request.args.get('q', '')
    page_str = request.args.get('page', '1')
    try:
        page = int(page_str)
    except ValueError:
        page = 0
    volumes = Volume.query(q)
    return render_template("index.html",
                           volumes=volumes,
                           q=q,
                           pagination=Pagination(page, PAGE_SIZE, volumes))


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
