#   Copyright  Members of the EMI Collaboration, 2013.
#   Copyright 2020 CERN
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

import json


class ErrorAsJson:
    """
    This middleware encodes an error as a json message if json was
    requested in the headers. Otherwise, let the error go and someone else catch it
    """

    def __init__(self, wrap_app):
        self.app = wrap_app

    def __call__(self, environ, start_response):
        accept = environ.get("HTTP_ACCEPT", "application/json")
        is_json_accepted = "application/json" in accept

        self._status_msg = None
        self._status_code = None

        def override_start_response(status, headers, exc_info=None):
            self._status_code = int(status.split()[0])
            if self._status_code >= 400 and is_json_accepted:
                headers = [
                    h
                    for h in headers
                    if h[0].lower() not in ("content-type", "content-length")
                ]
                headers.append(("Content-Type", "application/json"))
            self._status_msg = status
            return start_response(status, headers, exc_info)

        response = self.app(environ, override_start_response)

        if self._status_code >= 400 and is_json_accepted:
            # todo the problem is this contains html
            # check src/fts3rest/fts3rest/lib/JobBuilder.py:            raise BadRequest("Invalid value within the request: %s" % str(ex))
            err_msg = "".join(response.decode())
            json_error = {"status": self._status_msg, "message": err_msg}
            response = [json.dumps(json_error)]
        return response
