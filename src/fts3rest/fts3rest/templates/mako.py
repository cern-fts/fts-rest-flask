# pylint: skip-file
from mako.lookup import TemplateLookup
import tempfile
import os

path = os.path.abspath(os.path.dirname(__file__))

mylookup = TemplateLookup(directories=[path], module_directory=tempfile.mkdtemp())

def render_template(template_name, **context):
    mytemplate = mylookup.get_template(template_name)
    return mytemplate.render(**context)
