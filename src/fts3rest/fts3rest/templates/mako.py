# pylint: skip-file
from mako.lookup import TemplateLookup
import tempfile

mylookup = TemplateLookup(
    directories=["/templates"], module_directory=tempfile.mkdtemp()
)


def render_template(template_name, **context):
    mytemplate = mylookup.get_template(template_name)
    return mytemplate.render(**context)
