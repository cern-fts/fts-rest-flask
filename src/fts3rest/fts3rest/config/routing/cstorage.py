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

from fts3rest.controllers import cloudStorage


def do_connect(app):
    """
    Cloud Storage
    """
    bp = cloudStorage.cstorage_blueprint

    bp.add_url_rule(
        "/cs/registered/<service>",
        view_func=cloudStorage.is_registered,
        methods=["GET"],
    )

    bp.add_url_rule(
        "/cs/access_request/<service>/",
        view_func=cloudStorage.is_access_requested,
        methods=["GET"],
        strict_slashes=False,
    )

    bp.add_url_rule(
        "/cs/access_grant/<service>",
        view_func=cloudStorage.remove_token,
        methods=["DELETE"],
    )

    bp.add_url_rule(
        "/cs/access_request/<service>/request",
        view_func=cloudStorage.get_access_requested,
        methods=["GET"],
    )
    bp.add_url_rule(
        "/cs/access_grant/<service>",
        view_func=cloudStorage.get_access_granted,
        methods=["GET"],
    )

    bp.add_url_rule(
        "/cs/remote_content/<service>",
        view_func=cloudStorage.get_folder_content,
        methods=["GET"],
    )

    bp.add_url_rule(
        "/cs/file_urllink/<service>/<path>",
        view_func=cloudStorage.get_file_link,
        methods=["GET"],
    )

    app.register_blueprint(bp)