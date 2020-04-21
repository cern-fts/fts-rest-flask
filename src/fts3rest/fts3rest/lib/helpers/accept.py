#   Copyright 2015-2020 CERN
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from werkzeug.exceptions import NotAcceptable
from fts3rest.lib.helpers.jsonify import to_json
import functools
from flask import request, Response
from fts3rest.templates.mako import render_template
import logging

log = logging.getLogger(__name__)
from flask import current_app as app


def accept(html_template):
    """
    Depending on the Accept headers returns a different representation of the data
    returned by the decorated method
    """
    # We give a higher server quality to json, so */* matches it best
    offers = [("text/html", 1), ("application/json", 1.1)]
    # todo: maybe we have to lstrip "/" from template name if it doesnt work
    def accept_inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                best_match = request.accept_mimetypes.best_match(
                    offers, default="application/json"
                )
            except Exception:
                best_match = "application/json"
            log.debug("best_match {}".format(best_match))
            if not best_match:
                raise NotAcceptable("Available: %s" % ", ".join(offers))

            data = func(*args, **kwargs)
            if best_match == "text/html":
                return render_template(
                    html_template,
                    **{
                        "data": data,
                        "config": app.config,
                        "user": request.environ["fts3.User.Credentials"],
                    },
                )
            else:
                return Response(to_json(data), mimetype="application/json")

        return wrapper

    return accept_inner
