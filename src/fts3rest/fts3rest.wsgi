from fts3rest.config.middleware import create_app

default_config_filename = '/etc/fts3/fts3config'
application = create_app(default_config_filename)
