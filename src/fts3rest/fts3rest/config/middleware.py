from flask import Flask
from fts3rest.config import routing


def create_app(config_filename):
    app = Flask(__name__)
    routing.base.do_connect(app)

    return app
