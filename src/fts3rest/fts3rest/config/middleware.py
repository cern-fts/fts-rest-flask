from flask import Flask, jsonify
from fts3rest.config.routing import base
from werkzeug.exceptions import NotFound


def create_app(config_filename):
    app = Flask(__name__)
    base.do_connect(app)

    @app.errorhandler(NotFound)
    def handle_invalid_usage(error):
        response = jsonify(error=error.code, description=error.description)
        response.status_code = error.code
        return response

    return app
