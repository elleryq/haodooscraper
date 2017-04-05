# -*- coding: utf-8 -*-
import os
from flask import (Flask, Response, url_for, render_template,
                   request, jsonify)
from flask_bootstrap import Bootstrap
from flask_jsontools import jsonapi, DynamicJSONEncoder
from flask_apiblueprint import APIBlueprint
from werkzeug.datastructures import MultiDict
from haodooscraper.model import Volume


def url_for_other_page(page):
    args = MultiDict(list(
        request.args.items()) + list(request.view_args.items()))
    args['page'] = page
    return url_for(request.endpoint, **args)


PAGE_SIZE = 10
instance_path = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instance_path)
app.json_encoder = DynamicJSONEncoder
app.config['PROPAGATE_EXCEPTIONS'] = True
if "DEBUG" in os.environ:
    app.debug = os.environ['DEBUG'].lower() == "true"
else:
    app.debug = False
Bootstrap(app)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

api_v1 = APIBlueprint('api_v1', __name__, url_prefix='/api/v1')


def get_page():
    """Get 'page' parameter."""
    page_str = request.args.get('page', '1')
    try:
        page = int(page_str)
    except ValueError:
        page = 1
    return page


# The '/' page is accessible to anyone
@app.route('/')
def home():
    """Home."""
    q = request.args.get('q', '')
    page = get_page()
    return render_template(
        "index.html",
        q=q,
        pagination=Volume.query_as_pagination(q, page, PAGE_SIZE))


@app.route('/api/')
def api():
    """Display API uasge."""
    return render_template("api.html")


@app.route('/debug/')
@jsonapi
def test_encoding():
    """Test encoding."""
    page = 1
    q = None
    result = Volume.query_as_pagination(q, page, PAGE_SIZE).items()
    return {'result': list(result)}


@api_v1.route('/search/')
def api_search():
    """API - Search."""
    q = request.args.get('q', None)
    page = get_page()
    return jsonify({'result': list(Volume.query_as_pagination(
        q, page, PAGE_SIZE).items())})


# print(api_v1.routes_to_views_map)
app.register_blueprint(api_v1)
