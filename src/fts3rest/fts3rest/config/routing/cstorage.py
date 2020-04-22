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
    app.register_blueprint(bp)

    bp.add_url_rule(
        "/cs/registered/<service>", cloudStorage.is_registered, methods=["GET"],
    )

    bp.add_url_rule(
        "/cs/access_request/<service>",
        cloudStorage.is_access_requested,
        methods=["GET"],
    )
    bp.add_url_rule(
        "/cs/access_request/<service>/",
        cloudStorage.is_access_requested,
        methods=["GET"],
    )

    bp.add_url_rule(
        "/cs/access_grant/<service>", cloudStorage.remove_token, methods=["DELETE"],
    )

    bp.add_url_rule(
        "/cs/access_request/<service>/request",
        cloudStorage.get_access_requested,
        methods=["GET"],
    )
    bp.add_url_rule(
        "/cs/access_grant/<service>", cloudStorage.get_access_granted, methods=["GET"],
    )

    bp.add_url_rule(
        "/cs/remote_content/<service>",
        cloudStorage.get_folder_content,
        methods=["GET"],
    )

    bp.add_url_rule(
        "/cs/file_urllink/<service>/<path>",
        cloudStorage.get_file_link,
        methods=["GET"],
    )
