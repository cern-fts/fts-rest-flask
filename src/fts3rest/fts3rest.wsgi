from fts3rest.config.middleware import create_app

default_config_filename = '/etc/fts3/fts3restconfig'

application = create_app(default_config_filename)
