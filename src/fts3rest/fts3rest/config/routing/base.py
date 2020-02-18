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

from fts3rest.controllers import (
    api,
    delegation,
    jobs,
    files,
    archive,
    config,
    optimizer,
    datamanagement,
    autocomplete,
    banning,
    serverstatus,
)
from fts3rest.controllers.config import (
    drain,
    audit,
    global_,
    links,
    shares,
    se,
    authz,
    activities,
    cloud,
)


def do_connect(app):
    """
    Base urls
    """

    # Root
    app.add_url_rule("/", view_func=api.api_version)

    # OPTIONS handler
    # Commented out because Flask automatically generates an OPTIONS response
    # app.add_url_rule("/<path:.*?>", view_func=api.options_handler, methods=["OPTIONS"])

    # Delegation and self-identification
    app.add_url_rule("/whoami", view_func=delegation.whoami, methods=["GET"])
    app.add_url_rule(
        "/whoami/certificate", view_func=delegation.certificate, methods=["GET"]
    )
    app.add_url_rule("/delegation/<dlg_id>", view_func=delegation.view, methods=["GET"])
    app.add_url_rule(
        "/delegation/<dlg_id>", view_func=delegation.delete, methods=["DELETE"]
    )
    app.add_url_rule(
        "/delegation/<dlg_id>/request", view_func=delegation.request, methods=["GET"]
    )
    app.add_url_rule(
        "/delegation/<dlg_id>/credential",
        view_func=delegation.credential,
        methods=["PUT", "POST"],
    )
    app.add_url_rule(
        "/delegation/<dlg_id>/voms", view_func=delegation.voms, methods=["POST"]
    )

    # Delegation HTML view
    app.add_url_rule(
        "/delegation", view_func=delegation.delegation_page, methods=["GET"]
    )

    # Jobs
    app.add_url_rule("/jobs", view_func=jobs.index, methods=["GET"])
    app.add_url_rule("/jobs/", view_func=jobs.index, methods=["GET"])
    app.add_url_rule("/jobs/<job_list>", view_func=jobs.get, methods=["GET"])
    app.add_url_rule("/jobs/<job_id>/files", view_func=jobs.get_files, methods=["GET"])
    app.add_url_rule(
        "/jobs/<job_id>/files/<file_ids>",
        view_func=jobs.cancel_files,
        methods=["DELETE"],
    )
    app.add_url_rule(
        "/jobs/vo/<vo_name>", view_func=jobs.cancel_all_by_vo, methods=["DELETE"]
    )
    app.add_url_rule("/jobs/all", view_func=jobs.cancel_all, methods=["DELETE"])
    app.add_url_rule(
        "/jobs/<job_id>/files/<file_id>/retries",
        view_func=jobs.get_file_retries,
        methods=["GET"],
    )
    app.add_url_rule("/jobs/<job_id>/dm", view_func=jobs.get_dm, methods=["GET"])
    app.add_url_rule(
        "/jobs/<job_id>/<field>", view_func=jobs.get_field, methods=["GET"]
    )
    app.add_url_rule("/jobs/<job_id_list>", view_func=jobs.cancel, methods=["DELETE"])
    app.add_url_rule("/jobs/<job_id_list>", view_func=jobs.modify, methods=["POST"])
    app.add_url_rule("/jobs", view_func=jobs.submit, methods=["PUT", "POST"])

    # Query directly the transfers
    app.add_url_rule("/files", view_func=files.index, methods=["GET"])
    app.add_url_rule("/files/", view_func=files.index, methods=["GET"])

    # Archive
    app.add_url_rule("/archive", view_func=archive.index, methods=["GET"])
    app.add_url_rule("/archive/", view_func=archive.index, methods=["GET"])
    app.add_url_rule("/archive/<job_id>", view_func=archive.get, methods=["GET"])
    app.add_url_rule(
        "/archive/<job_id>/<field>", view_func=archive.get_field, methods=["GET"]
    )

    # Schema definition
    app.add_url_rule(
        "/api-docs/schema/submit", view_func=api.submit_schema, methods=["GET"]
    )
    app.add_url_rule("/api-docs", view_func=api.api_docs, methods=["GET"])
    app.add_url_rule(
        "/api-docs/<resource>", view_func=api.resource_doc, methods=["GET"]
    )

    # Config entry point
    app.add_url_rule("/config", view_func=config.index, methods=["GET"])

    # Set/unset draining mode
    app.add_url_rule(
        "/config/drain", view_func=config.drain.set_drain, methods=["POST"]
    )

    # Configuration audit
    app.add_url_rule("/config/audit", view_func=config.audit.audit, methods=["GET"])

    # Global settings
    app.add_url_rule(
        "/config/global", view_func=config.global_.set_global_config, methods=["POST"]
    )
    app.add_url_rule(
        "/config/global", view_func=config.global_.get_global_config, methods=["GET"]
    )
    app.add_url_rule(
        "/config/global",
        view_func=config.global_.delete_vo_global_config,
        methods=["DELETE"],
    )

    # Link config (SE or Group)
    app.add_url_rule(
        "/config/links", view_func=config.links.set_link_config, methods=["POST"]
    )
    app.add_url_rule(
        "/config/links", view_func=config.links.get_all_link_configs, methods=["GET"]
    )
    app.add_url_rule(
        "/config/links/<sym_name>",
        view_func=config.links.get_link_config,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/links/<sym_name>",
        view_func=config.links.delete_link_config,
        methods=["DELETE"],
    )

    # Shares
    app.add_url_rule(
        "/config/shares", view_func=config.shares.set_share, methods=["POST"]
    )
    app.add_url_rule(
        "/config/shares", view_func=config.shares.get_shares, methods=["GET"]
    )
    app.add_url_rule(
        "/config/shares", view_func=config.shares.delete_share, methods=["DELETE"]
    )

    # Per SE
    app.add_url_rule("/config/se", view_func=config.se.set_se_config, methods=["POST"])
    app.add_url_rule("/config/se", view_func=config.se.get_se_config, methods=["GET"])
    app.add_url_rule(
        "/config/se", view_func=config.se.delete_se_config, methods=["DELETE"]
    )

    # Grant special permissions to given DNs
    app.add_url_rule(
        "/config/authorize", view_func=config.authz.add_authz, methods=["POST"]
    )
    app.add_url_rule(
        "/config/authorize", view_func=config.authz.list_authz, methods=["GET"]
    )
    app.add_url_rule(
        "/config/authorize", view_func=config.authz.remove_authz, methods=["DELETE"]
    )

    # Configure activity shares
    app.add_url_rule(
        "/config/activity_shares",
        view_func=config.activities.get_activity_shares,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/activity_shares",
        view_func=config.activities.set_activity_shares,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/activity_shares/<vo_name>",
        view_func=config.activities.get_activity_shares_vo,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/activity_shares/<vo_name>",
        view_func=config.activities.delete_activity_shares,
        methods=["DELETE"],
    )

    # Configure cloud storages
    app.add_url_rule(
        "/config/cloud_storage",
        view_func=config.cloud.get_cloud_storages,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/cloud_storage",
        view_func=config.cloud.set_cloud_storages,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/cloud_storage/<storage_name>",
        view_func=config.cloud.get_cloud_storage,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/cloud_storage/<storage_name>",
        view_func=config.cloud.remove_cloud_storage,
        methods=["DELETE"],
    )
    app.add_url_rule(
        "/config/cloud_storage/<storage_name>",
        view_func=config.cloud.add_user_to_cloud_storage,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/cloud_storage/<storage_name>/<id>",
        view_func=config.cloud.remove_user_from_cloud_storage,
        methods=["DELETE"],
    )

    # Optimizer
    app.add_url_rule("/optimizer", view_func=optimizer.is_enabled, methods=["GET"])
    app.add_url_rule(
        "/optimizer/evolution", view_func=optimizer.evolution, methods=["GET"]
    )
    app.add_url_rule(
        "/optimizer/current", view_func=optimizer.get_optimizer_values, methods=["GET"]
    )
    app.add_url_rule(
        "/optimizer/current", view_func=optimizer.set_optimizer_values, methods=["POST"]
    )

    # GFAL2 bindings
    app.add_url_rule("/dm/list", view_func=datamanagement.list, methods=["GET"])
    app.add_url_rule("/dm/stat", view_func=datamanagement.stat, methods=["GET"])
    app.add_url_rule("/dm/mkdir", view_func=datamanagement.mkdir, methods=["POST"])
    app.add_url_rule("/dm/unlink", view_func=datamanagement.unlink, methods=["POST"])
    app.add_url_rule("/dm/rmdir", view_func=datamanagement.rmdir, methods=["POST"])
    app.add_url_rule("/dm/rename", view_func=datamanagement.rename, methods=["POST"])

    # Banning
    app.add_url_rule("/ban/se", view_func=banning.ban_se, methods=["POST"])
    app.add_url_rule("/ban/se", view_func=banning.unban_se, methods=["DELETE"])
    app.add_url_rule("/ban/se", view_func=banning.list_banned_se, methods=["GET"])
    app.add_url_rule("/ban/dn", view_func=banning.ban_dn, methods=["POST"])
    app.add_url_rule("/ban/dn", view_func=banning.unban_dn, methods=["DELETE"])
    app.add_url_rule("/ban/dn", view_func=banning.list_banned_dn, methods=["GET"])

    # Autocomplete
    app.add_url_rule(
        "/autocomplete/dn", view_func=autocomplete.autocomplete_dn, methods=["GET"]
    )
    app.add_url_rule(
        "/autocomplete/source",
        view_func=autocomplete.autocomplete_source,
        methods=["GET"],
    )
    app.add_url_rule(
        "/autocomplete/destination",
        view_func=autocomplete.autocomplete_destination,
        methods=["GET"],
    )
    app.add_url_rule(
        "/autocomplete/storage",
        view_func=autocomplete.autocomplete_storage,
        methods=["GET"],
    )
    app.add_url_rule(
        "/autocomplete/vo", view_func=autocomplete.autocomplete_vo, methods=["GET"]
    )

    # State check
    app.add_url_rule(
        "/status/hosts", view_func=serverstatus.hosts_activity, methods=["GET"]
    )
