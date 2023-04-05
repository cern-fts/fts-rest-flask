#   Copyright Members of the EMI Collaboration, 2013.
#   Copyright 2013-2020 CERN
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
import logging

import io
from flask import request, Response, send_file
from werkzeug.exceptions import BadRequest, NotFound

from fts3rest.model import *
from fts3rest.lib.helpers.accept import accept
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3rest.lib.middleware.fts3auth.authorization import (
    authorize,
    require_certificate,
)
from fts3rest.lib.middleware.fts3auth.constants import CONFIG
from fts3rest.model.meta import Session

log = logging.getLogger(__name__)


"""
Configuration of cloud storages
"""


@require_certificate
@authorize(CONFIG)
@accept(html_template="/config/cloud_storage.html")
def get_cloud_storages():
    """
    Get a list of cloud storages registered
    """
    storages_s3 = Session.query(CloudStorageS3).all()
    for storage_s3 in storages_s3:
        users = Session.query(CloudStorageUser).filter(
            CloudStorageUser.cloudStorage_name == storage_s3.cloudStorage_name
            )
        setattr(storage_s3, "users", list(users))
        setattr(storage_s3, "cloud_type", "S3")

    storages_gcloud = Session.query(CloudStorageGcloud).all()
    for storage_gcloud in storages_gcloud:
        users = Session.query(CloudStorageUser).filter(
            CloudStorageUser.cloudStorage_name == storage_gcloud.cloudStorage_name
            )
        setattr(storage_gcloud, "users", list(users))
        setattr(storage_gcloud, "cloud_type", "gcloud")

        if getattr(storage_gcloud,'auth_file') is None:
            setattr(storage_gcloud, "auth_file", False)
        else:
            setattr(storage_gcloud, "auth_file", True)

    storages_swift = Session.query(CloudStorageSwift).all()
    for storage_swift in storages_swift:
        users = Session.query(CloudStorageUser).filter(
            CloudStorageUser.cloudStorage_name == storage_swift.cloudStorage_name
            )
        setattr(storage_swift, "users", list(users))
        setattr(storage_swift, "cloud_type", "swift")

    return storages_s3, storages_gcloud, storages_swift


@require_certificate
@authorize(CONFIG)
@jsonify
def set_cloud_storage_s3():
    """
    Add or modify a cloud storage entry for S3 implementation
    """
    input_dict = get_input_as_dict(request)
    if "cloudstorage_name" not in input_dict:
        raise BadRequest("Missing storage name")

    storage = CloudStorageS3(
        cloudStorage_name=input_dict.get("cloudstorage_name"),
        alternate=input_dict.get("alternate"),
        region=input_dict.get("region"),
        )
    try:
        Session.merge(storage)
        Session.commit()
    except Exception:
        Session.rollback()
        raise
    return Response(storage, status=201)


@require_certificate
@authorize(CONFIG)
@jsonify
def set_cloud_storage_swift():
    """
    Add or modify a cloud storage entry for Swift implementation
    """
    input_dict = get_input_as_dict(request)
    if "cloudstorage_name" not in input_dict:
        raise BadRequest("Missing storage name")
    storage = CloudStorageSwift(
        cloudStorage_name=input_dict.get("cloudstorage_name"),
        os_project_id=input_dict.get("os_project_id"),
        os_token=input_dict.get("os_token"),
        )
    try:
        Session.merge(storage)
        Session.commit()
    except Exception:
        Session.rollback()
        raise
    return Response(storage, status=201)


@require_certificate
@authorize(CONFIG)
@jsonify
def set_cloud_storage_gcloud():
    """
    Add or modify a cloud storage entry for Gcloud implementation
    """

    input_cloudstorage_name = request.form['cloudstorage_name']
    input_auth_file = request.files['auth_file']
    if not input_cloudstorage_name or input_cloudstorage_name.isspace():
        raise BadRequest("The storage name cannot be null or contain spaces")
    storage = CloudStorageGcloud(
        cloudStorage_name=input_cloudstorage_name,
        auth_file=input_auth_file.read(),
        )
    try:
        Session.merge(storage)
        Session.commit()
    except Exception:
        Session.rollback()
        raise
    return Response([""], status=201)


@require_certificate
@authorize(CONFIG)
@jsonify
def get_cloud_storage_s3(cloudstorage_name):
    """
    Get a list of users registered for a given storage name for S3 implementation
    """
    storage = Session.query(CloudStorageS3).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    users = Session.query(CloudStorageUser).filter(
        CloudStorageUser.cloudStorage_name == cloudstorage_name
        )
    return users


@require_certificate
@authorize(CONFIG)
# @jsonify
def get_cloud_storage_gcloud(cloudstorage_name):
    """
    Get a list of users registered for a given storage name for Gcloud implementation
    """
    storage = Session.query(CloudStorageGcloud).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    users = Session.query(CloudStorageUser).filter(
        CloudStorageUser.cloudStorage_name == cloudstorage_name
        )
    return users


@require_certificate
@authorize(CONFIG)
def get_gcloud_auth_file(cloudstorage_name):
    """
    Get the authentication file for a given storage for Gcloud implementation
    """
    storage = Session.query(CloudStorageGcloud).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    return send_file(io.BytesIO(storage.auth_file), attachment_filename="auth_file.json", as_attachment=True)


@require_certificate
@authorize(CONFIG)
@jsonify
def get_cloud_storage_swift(cloudstorage_name):
    """
    Get a list of users registered for a given storage name for Swift implementation
    """
    storage = Session.query(CloudStorageSwift).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    users = Session.query(CloudStorageUser).filter(
        CloudStorageUser.cloudStorage_name == cloudstorage_name
        )
    return users


@require_certificate
@authorize(CONFIG)
def remove_cloud_storage_s3(cloudstorage_name):
    """
    Remove a registered cloud storage for S3 implementation
    """
    storage = Session.query(CloudStorageS3).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    try:
        Session.query(CloudStorageUser).filter(
            CloudStorageUser.cloudStorage_name == cloudstorage_name
        ).delete()
        Session.delete(storage)
        Session.commit()
        
        Session.query(CloudStorage).filter(
            CloudStorage.cloudStorage_name == cloudstorage_name
        ).delete()
        Session.delete(storage)
        Session.commit()
        
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=204)


@require_certificate
@authorize(CONFIG)
def remove_cloud_storage_gcloud(cloudstorage_name):
    """
    Remove a registered cloud storage for Gcloud implementation
    """
    storage = Session.query(CloudStorageGcloud).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    try:
        Session.query(CloudStorageUser).filter(
            CloudStorageUser.cloudStorage_name == cloudstorage_name
        ).delete()
        Session.delete(storage)
        Session.commit()
        
        Session.query(CloudStorage).filter(
            CloudStorage.cloudStorage_name == cloudstorage_name
        ).delete()
        Session.delete(storage)
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=204)


@require_certificate
@authorize(CONFIG)
def remove_cloud_storage_swift(cloudstorage_name):
    """
    Remove a registered cloud storage for Swift implementation
    """
    storage = Session.query(CloudStorageSwift).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    try:
        Session.query(CloudStorageUser).filter(
            CloudStorageUser.cloudStorage_name == cloudstorage_name
        ).delete()
        Session.delete(storage)
        Session.commit()
        
        Session.query(CloudStorage).filter(
            CloudStorage.cloudStorage_name == cloudstorage_name
        ).delete()
        Session.delete(storage)
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=204)


@require_certificate
@authorize(CONFIG)
@jsonify
def add_user_to_cloud_storage(cloudstorage_name):
    """
    Add a user or a VO credentials to the storage
    """
    storage = Session.query(CloudStorage).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    input_dict = get_input_as_dict(request)
    
    if storage.cloud_type == "Gcloud":    
        cuser = CloudStorageUser(
            user_dn=input_dict.get("user_dn"),
            cloudStorage_name=cloudstorage_name,
            vo_name=input_dict.get("vo_name"),
            secret_key="",
            access_key= ""
            )
    if storage.cloud_type == "S3":    
        cuser = CloudStorageUser(
            user_dn=input_dict.get("user_dn"),
            cloudStorage_name=cloudstorage_name,
            access_key=input_dict.get("access_key"),
            secret_key=input_dict.get("secret_key"),
            vo_name=input_dict.get("vo_name")
            )
    if storage.cloud_type == "Swift":   
        cuser = CloudStorageUser(
            user_dn=input_dict.get("user_dn"),
            cloudStorage_name=cloudstorage_name,
            vo_name=input_dict.get("vo_name"),
            secret_key="",
            access_key= ""
            )

    try:
        Session.merge(cuser)
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=201)

@require_certificate
@authorize(CONFIG)
def remove_user_from_cloud_storage(cloudstorage_name, id):
    """
    Delete credentials for a given user/vo
    """
    storage = Session.query(CloudStorage).get(cloudstorage_name)
    if not storage:
        raise NotFound("The storage does not exist")

    users = (
        Session.query(CloudStorageUser)
        .filter(CloudStorageUser.cloudStorage_name == cloudstorage_name)
        .filter((CloudStorageUser.vo_name == id) | (CloudStorageUser.user_dn == id))
    )

    try:
        for user in users:
            Session.delete(user)
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=204)
