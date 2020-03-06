from flask import Flask, jsonify
from werkzeug.exceptions import NotFound

from fts3rest.config.routing import base
from fts3.util.config import fts3_config_load


def create_app(default_config_filename):
    app = Flask(__name__)

    # Load configuration
    fts3cfg = fts3_config_load(default_config_filename)
    app.config.update(fts3cfg)

    # Add routes
    base.do_connect(app)

    # Setup the SQLAlchemy database engine
    kwargs = dict()
    if app.config['sqlalchemy.url'].startswith('mysql://'):
        import MySQLdb.cursors
        kwargs['connect_args'] = {'cursorclass': MySQLdb.cursors.SSCursor}
    engine = engine_from_config(config, 'sqlalchemy.', pool_recycle=7200, **kwargs)
    init_model(engine)

    # Disable for sqlite the isolation level to work around issues with savepoints
    if config['sqlalchemy.url'].startswith('sqlite'):
        @event.listens_for(engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            dbapi_connection.isolation_level = None

    # Catch dead connections
    event.listens_for(engine, 'checkout')(connection_validator)
    event.listens_for(engine, 'connect')(connection_set_sqlmode)


    @app.errorhandler(NotFound)
    def handle_invalid_usage(error):
        response = jsonify(error=error.code, description=error.description)
        response.status_code = error.code
        return response

    return app
