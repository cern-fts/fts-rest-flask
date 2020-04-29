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

import functools
from flask import request
from fts3rest.templates.mako import render_template
import logging

log = logging.getLogger(__name__)
from flask import current_app as app


def accept(html_template):
    def accept_inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = func(*args, **kwargs)
            return render_template(
                html_template.lstrip("/"),
                **{
                    "data": data,
                    "config": app.config,
                    "user": request.environ["fts3.User.Credentials"],
                },
            )

        return wrapper

    return accept_inner
