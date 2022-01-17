from fts3rest.config.middleware import create_app

default_config_filename = '/etc/fts3/ftsrestconfig'

application = create_app(default_config_filename)
