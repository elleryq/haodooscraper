# -*- coding: utf-8 -*-
import os
from flask import (Flask, Response, url_for, render_template,
                   request, jsonify, Blueprint)
from flask_bootstrap import Bootstrap
from flask_jsontools import jsonapi, DynamicJSONEncoder
from flask_restplus import Resource, Api, reqparse
from werkzeug.datastructures import MultiDict
from haodooscraper.model import Volume
from restplus import api


def url_for_other_page(page):
    args = MultiDict(list(
        request.args.items()) + list(request.view_args.items()))
    args['page'] = page
    return url_for(request.endpoint, **args)


PAGE_SIZE = 10

query_arguments = reqparse.RequestParser()
query_arguments.add_argument('page', type=int, required=False, default=1)
query_arguments.add_argument('per_page', type=int, required=False,
                                  choices=[5, 10, 20, 30, 40, 50], default=10)
query_arguments.add_argument('q', type=str, required=True, default='')

instance_path = os.path.join(os.environ['OPENSHIFT_PYTHON_DIR'], 'instance')
app = Flask(__name__, instance_path=instance_path)
app.json_encoder = DynamicJSONEncoder
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['RESTPLUS_JSON'] = {
    'cls': DynamicJSONEncoder,
}

if "DEBUG" in os.environ:
    app.debug = os.environ['DEBUG'].lower() == "true"
else:
    app.debug = False
Bootstrap(app)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

blueprint = Blueprint('api', __name__, url_prefix='/api')
api.init_app(blueprint)


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


@app.route('/debug/')
@jsonapi
def test_encoding():
    """Test encoding."""
    page = 1
    q = None
    result = Volume.query_as_pagination(q, page, PAGE_SIZE).items()
    return {'result': list(result)}


#  @api_v1.route('/search/')
#  def api_search():
    #  """API - Search."""
    #  q = request.args.get('q', None)
    #  page = get_page()
    #  return jsonify({'result': list(Volume.query_as_pagination(
        #  q, page, PAGE_SIZE).items())})


ns = api.namespace('book', description='Operations related to books')


@ns.route('/search/')
class HaodooScraperAPI(Resource):
    """API for HaodooScraper books."""

    @api.expect(query_arguments, validate=True)
    def get(self):
        args = query_arguments.parse_args(request)
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        q = args.get('q', '')
        return {'result': list(Volume.query_as_pagination(
            q, page, PAGE_SIZE).items())}


api.add_namespace(ns)
app.register_blueprint(blueprint)
