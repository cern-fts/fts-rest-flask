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
    app.add_url_rule("/", view_func=api.api_version.as_view("api.api_version"))

    # Delegation and self-identification
    app.add_url_rule(
        "/whoami",
        view_func=delegation.whoami.as_view("delegation.whoami"),
        methods=["GET"],
    )
    app.add_url_rule(
        "/whoami/certificate",
        view_func=delegation.certificate.as_view("delegation.certificate"),
        methods=["GET"],
    )
    app.add_url_rule(
        "/delegation/<dlg_id>",
        view_func=delegation.view.as_view("delegation.view"),
        methods=["GET"],
    )
    app.add_url_rule(
        "/delegation/<dlg_id>",
        view_func=delegation.delete.as_view("delegation.delete"),
        methods=["DELETE"],
    )
    app.add_url_rule(
        "/delegation/<dlg_id>/request",
        view_func=delegation.request.as_view("delegation.request"),
        methods=["GET"],
    )
    app.add_url_rule(
        "/delegation/<dlg_id>/credential",
        view_func=delegation.credential.as_view("delegation.credential"),
        methods=["PUT", "POST"],
    )
    app.add_url_rule(
        "/delegation/<dlg_id>/voms",
        view_func=delegation.voms.as_view("delegation.voms"),
        methods=["POST"],
    )

    # Delegation HTML view
    app.add_url_rule(
        "/delegation",
        view_func=delegation.delegation_page.as_view("delegation.delegation_page"),
        methods=["GET"],
    )

    # Jobs
    app.add_url_rule("/jobs", "jobs.index", jobs.index, methods=["GET"])
    app.add_url_rule("/jobs/", "jobs.index", jobs.index, methods=["GET"])
    app.add_url_rule("/jobs/<job_list>", "jobs.get", jobs.get, methods=["GET"])
    app.add_url_rule(
        "/jobs/<job_id>/files", "jobs.get_files", jobs.get_files, methods=["GET"]
    )
    app.add_url_rule(
        "/jobs/<job_id>/files/<file_ids>",
        "jobs.cancel_files",
        jobs.cancel_files,
        methods=["DELETE"],
    )
    app.add_url_rule(
        "/jobs/vo/<vo_name>",
        "jobs.cancel_all_by_vo",
        jobs.cancel_all_by_vo,
        methods=["DELETE"],
    )
    app.add_url_rule(
        "/jobs/all", "jobs.cancel_all", jobs.cancel_all, methods=["DELETE"]
    )
    app.add_url_rule(
        "/jobs/<job_id>/files/<file_id>/retries",
        "jobs.get_file_retries",
        jobs.get_file_retries,
        methods=["GET"],
    )
    app.add_url_rule("/jobs/<job_id>/dm", "jobs.get_dm", jobs.get_dm, methods=["GET"])
    app.add_url_rule(
        "/jobs/<job_id>/<field>", "jobs.get_field", jobs.get_field, methods=["GET"]
    )
    app.add_url_rule(
        "/jobs/<job_id_list>", "jobs.cancel", jobs.cancel, methods=["DELETE"]
    )
    app.add_url_rule(
        "/jobs/<job_id_list>", "jobs.modify", jobs.modify, methods=["POST"]
    )
    app.add_url_rule("/jobs", "jobs.submit", jobs.submit, methods=["PUT", "POST"])

    # Query directly the transfers
    app.add_url_rule("/files", "files.index", files.index, methods=["GET"])
    app.add_url_rule("/files/", "files.index", files.index, methods=["GET"])

    # Archive
    app.add_url_rule("/archive", "archive.index", archive.index, methods=["GET"])
    app.add_url_rule("/archive/", "archive.index", archive.index, methods=["GET"])
    app.add_url_rule("/archive/<job_id>", "archive.get", archive.get, methods=["GET"])
    app.add_url_rule(
        "/archive/<job_id>/<field>",
        "archive.get_field",
        archive.get_field,
        methods=["GET"],
    )

    # Schema definition
    app.add_url_rule(
        "/api-docs/schema/submit",
        view_func=api.submit_schema.as_view("api.submit_schema"),
        methods=["GET"],
    )
    app.add_url_rule(
        "/api-docs", view_func=api.api_docs.as_view("api.api_docs"), methods=["GET"]
    )
    app.add_url_rule(
        "/api-docs/<resource>",
        view_func=api.resource_doc.as_view("api.resource_doc"),
        methods=["GET"],
    )

    # Config entry point
    app.add_url_rule("/config", "config.index", config.index, methods=["GET"])

    # Set/unset draining mode
    app.add_url_rule(
        "/config/drain",
        "config.drain.set_drain",
        config.drain.set_drain,
        methods=["POST"],
    )

    # Configuration audit
    app.add_url_rule(
        "/config/audit", "config.audit.audit", config.audit.audit, methods=["GET"]
    )

    # Global settings
    app.add_url_rule(
        "/config/global",
        "config.global_.set_global_config",
        config.global_.set_global_config,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/global",
        "config.global_.get_global_config",
        config.global_.get_global_config,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/global",
        "config.global_.delete_vo_global_config",
        config.global_.delete_vo_global_config,
        methods=["DELETE"],
    )

    # Link config (SE or Group)
    app.add_url_rule(
        "/config/links",
        "config.links.set_link_config",
        config.links.set_link_config,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/links",
        "config.links.get_all_link_configs",
        config.links.get_all_link_configs,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/links/<sym_name>",
        "config.links.get_link_config",
        config.links.get_link_config,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/links/<sym_name>",
        "config.links.delete_link_config",
        config.links.delete_link_config,
        methods=["DELETE"],
    )

    # Shares
    app.add_url_rule(
        "/config/shares",
        "config.shares.set_share",
        config.shares.set_share,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/shares",
        "config.shares.get_shares",
        config.shares.get_shares,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/shares",
        "config.shares.delete_share",
        config.shares.delete_share,
        methods=["DELETE"],
    )

    # Per SE
    app.add_url_rule(
        "/config/se",
        "config.se.set_se_config",
        config.se.set_se_config,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/se",
        "config.se.get_se_config",
        config.se.get_se_config,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/se",
        "config.se.delete_se_config",
        config.se.delete_se_config,
        methods=["DELETE"],
    )

    # Grant special permissions to given DNs
    app.add_url_rule(
        "/config/authorize",
        "config.authz.add_authz",
        config.authz.add_authz,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/authorize",
        "config.authz.list_authz",
        config.authz.list_authz,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/authorize",
        "config.authz.remove_authz",
        config.authz.remove_authz,
        methods=["DELETE"],
    )

    # Configure activity shares
    app.add_url_rule(
        "/config/activity_shares",
        "config.activities.get_activity_shares",
        config.activities.get_activity_shares,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/activity_shares",
        "config.activities.set_activity_shares",
        config.activities.set_activity_shares,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/activity_shares/<vo_name>",
        "config.activities.get_activity_shares_vo",
        config.activities.get_activity_shares_vo,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/activity_shares/<vo_name>",
        "config.activities.delete_activity_shares",
        config.activities.delete_activity_shares,
        methods=["DELETE"],
    )

    # Configure cloud storages
    app.add_url_rule(
        "/config/cloud_storage",
        "config.cloud.get_cloud_storages",
        config.cloud.get_cloud_storages,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/cloud_storage_s3",
        "config.cloud.set_cloud_storage_s3",
        config.cloud.set_cloud_storage_s3,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/cloud_storage_swift",
        "config.cloud.set_cloud_storage_swift",
        config.cloud.set_cloud_storage_swift,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/cloud_storage_gcloud",
        "config.cloud.set_cloud_storage_gcloud",
        config.cloud.set_cloud_storage_gcloud,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/cloud_storage_s3/<cloudstorage_name>",
        "config.cloud.get_cloud_storage_s3",
        config.cloud.get_cloud_storage_s3,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/cloud_storage_gcloud/<cloudstorage_name>",
        "config.cloud.get_cloud_storage_gcloud",
        config.cloud.get_cloud_storage_gcloud,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/cloud_storage_swift/<cloudstorage_name>",
        "config.cloud.cloud_storage_swift",
        config.cloud.get_cloud_storage_swift,
        methods=["GET"],
    )
    app.add_url_rule(
        "/config/cloud_storage/<storage_name>",
        "config.cloud.remove_cloud_storage",
        config.cloud.remove_cloud_storage,
        methods=["DELETE"],
    )
    app.add_url_rule(
        "/config/cloud_storage/<storage_name>",
        "config.cloud.add_user_to_cloud_storage",
        config.cloud.add_user_to_cloud_storage,
        methods=["POST"],
    )
    app.add_url_rule(
        "/config/cloud_storage/<storage_name>/<id>",
        "config.cloud.remove_user_from_cloud_storage",
        config.cloud.remove_user_from_cloud_storage,
        methods=["DELETE"],
    )

    # Optimizer
    app.add_url_rule(
        "/optimizer", "optimizer.is_enabled", optimizer.is_enabled, methods=["GET"]
    )
    app.add_url_rule(
        "/optimizer/evolution",
        "optimizer.evolution",
        optimizer.evolution,
        methods=["GET"],
    )
    app.add_url_rule(
        "/optimizer/current",
        "optimizer.get_optimizer_values",
        optimizer.get_optimizer_values,
        methods=["GET"],
    )
    app.add_url_rule(
        "/optimizer/current",
        "optimizer.set_optimizer_values",
        optimizer.set_optimizer_values,
        methods=["POST"],
    )

    # GFAL2 bindings
    app.add_url_rule(
        "/dm/list", "datamanagement.list", datamanagement.list, methods=["GET"]
    )
    app.add_url_rule(
        "/dm/stat", "datamanagement.stat", datamanagement.stat, methods=["GET"]
    )
    app.add_url_rule(
        "/dm/mkdir", "datamanagement.mkdir", datamanagement.mkdir, methods=["POST"]
    )
    app.add_url_rule(
        "/dm/unlink", "datamanagement.unlink", datamanagement.unlink, methods=["POST"]
    )
    app.add_url_rule(
        "/dm/rmdir", "datamanagement.rmdir", datamanagement.rmdir, methods=["POST"]
    )
    app.add_url_rule(
        "/dm/rename", "datamanagement.rename", datamanagement.rename, methods=["POST"]
    )

    # Banning
    app.add_url_rule("/ban/se", "banning.ban_se", banning.ban_se, methods=["POST"])
    app.add_url_rule(
        "/ban/se", "banning.unban_se", banning.unban_se, methods=["DELETE"]
    )
    app.add_url_rule(
        "/ban/se", "banning.list_banned_se", banning.list_banned_se, methods=["GET"]
    )
    app.add_url_rule("/ban/dn", "banning.ban_dn", banning.ban_dn, methods=["POST"])
    app.add_url_rule(
        "/ban/dn", "banning.unban_dn", banning.unban_dn, methods=["DELETE"]
    )
    app.add_url_rule(
        "/ban/dn", "banning.list_banned_dn", banning.list_banned_dn, methods=["GET"]
    )

    # Autocomplete
    app.add_url_rule(
        "/autocomplete/dn",
        "autocomplete.autocomplete_dn",
        autocomplete.autocomplete_dn,
        methods=["GET"],
    )
    app.add_url_rule(
        "/autocomplete/source",
        "autocomplete.autocomplete_source",
        autocomplete.autocomplete_source,
        methods=["GET"],
    )
    app.add_url_rule(
        "/autocomplete/destination",
        "autocomplete.autocomplete_destination",
        autocomplete.autocomplete_destination,
        methods=["GET"],
    )
    app.add_url_rule(
        "/autocomplete/storage",
        "autocomplete.autocomplete_storage",
        autocomplete.autocomplete_storage,
        methods=["GET"],
    )
    app.add_url_rule(
        "/autocomplete/vo",
        "autocomplete.autocomplete_vo",
        autocomplete.autocomplete_vo,
        methods=["GET"],
    )

    # State check
    app.add_url_rule(
        "/status/hosts",
        "serverstatus.hosts_activity",
        serverstatus.hosts_activity,
        methods=["GET"],
    )
