from flask import Flask, jsonify
from werkzeug.exceptions import NotFound
from sqlalchemy import engine_from_config, event
import MySQLdb
import os
import logging.config
from fts3rest.config.routing import base
from fts3.util.config import fts3_config_load
from fts3rest.model import init_model
from fts3rest.lib.helpers.connection_validator import (
    connection_validator,
    connection_set_sqlmode,
)
from fts3rest.model.meta import Session


def create_app(default_config_file=None, test=False):
    """
    Create a new fts-rest Flask app
    :param default_config_file: Config file to use if the environment variable
    FTS3CONFIG is not set
    :param test: True if testing. FTS3TESTCONFIG will be used instead of FTS3CONFIG
    :return: the app
    """
    if test:
        config_file = os.environ.get("FTS3TESTCONFIG", default_config_file)
    else:
        config_file = os.environ.get("FTS3CONFIG", default_config_file)

    logging.config.fileConfig(config_file)
    app = Flask(__name__)

    # Load configuration
    fts3cfg = fts3_config_load(config_file)
    app.config.update(fts3cfg)

    # Add routes
    base.do_connect(app)

    # Setup the SQLAlchemy database engine
    kwargs = dict()
    if app.config["sqlalchemy.url"].startswith("mysql://"):
        kwargs["connect_args"] = {"cursorclass": MySQLdb.cursors.SSCursor}
    engine = engine_from_config(app.config, "sqlalchemy.", pool_recycle=7200, **kwargs)
    init_model(engine)

    # Disable for sqlite the isolation level to work around issues with savepoints
    if app.config["sqlalchemy.url"].startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            dbapi_connection.isolation_level = None

    # Catch dead connections
    event.listens_for(engine, "checkout")(connection_validator)
    event.listens_for(engine, "connect")(connection_set_sqlmode)

    # Flask will automatically remove database sessions at the end of the request or when the application shuts down:
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()

    @app.errorhandler(NotFound)
    def handle_invalid_usage(error):
        response = jsonify(error=error.code, name=error.name)
        response.status_code = error.code
        return response

    return app
