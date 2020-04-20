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
from flask import request
import logging

log = logging.getLogger(__name__)


def accept(html_template=None, html_redirect=None, json=True):
    """
    Depending on the Accept headers returns a different representation of the data
    returned by the decorated method
    """
    assert (html_template and not html_redirect) or (
        not html_template and html_redirect
    )

    # We give a higher server quality to json, so */* matches it best
    offers = [("text/html", 1)]
    if json:
        offers.append(("application/json", 1.1))

    def accept_inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                best_match = request.accept_mimetypes.best_match(
                    offers, default="application/json"
                )
            except Exception:
                best_match = "application/json"
            log.debut("best_match {}".format(best_match))
            if not best_match:
                raise NotAcceptable("Available: %s" % ", ".join(offers))

            data = func(*args, **kwargs)
            if best_match == "text/html":
                if html_template:
                    return render(
                        html_template,
                        extra_vars={
                            "data": data,
                            "config": pylons.config,
                            "user": pylons.request.environ["fts3.User.Credentials"],
                        },
                    )
                else:
                    return redirect(html_redirect, code=303)
            else:
                pylons.response.headers["Content-Type"] = "application/json"
                return to_json(data)

        return wrapper

    return accept_inner
