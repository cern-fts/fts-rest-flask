#   Copyright notice:
#   Copyright  Members of the EMI Collaboration, 2013.
#
#   See www.eu-emi.eu for details on the copyright holders
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
from datetime import datetime

from keystoneauth1 import session
from keystoneauth1.identity import v3
from keystoneclient.v3 import client
from fts3rest.model.meta import Session
from fts3rest.model import Credential, Job, CloudCredentialCache, CloudStorage, CloudStorageUser

log = logging.getLogger(__name__)


def set_swift_credential_cache(cred, user_dn, storage_name, os_token, os_project_id):
    cred['user_dn'] = user_dn
    cred['os_project_id'] = os_project_id
    cred['storage_name'] = storage_name
    cred['os_token'] = os_token
    cred['os_token_recvtime'] = datetime.utcnow()
    return cred


def get_os_token(user_dn, access_token, cloud_storage, project_id):
    """
    Get an OS token using an OIDC access token for the Swift user
    """
    cloudcredential = dict()

    keystone_auth = v3.oidc.OidcAccessToken(auth_url=cloud_storage.keystone_url,
                                            identity_provider=cloud_storage.keystone_idp,
                                            protocol="openid",
                                            access_token=access_token,
                                            project_id=project_id)
    sess = session.Session(auth=keystone_auth)
    try:
        os_token = sess.get_token()
        cloudcredential = set_swift_credential_cache(cloudcredential, user_dn,
                                                     cloud_storage.storage_name,
                                                     os_token, project_id)
        log.debug("Retrieved OS token %s" % os_token)
    except Exception as ex:
        log.warning("Failed to retrieve OS token because: %s" % str(ex))
    return cloudcredential


def refresh_os_token(job, se_url, id_count):
    storage_name = "SWIFT:" + se_url[se_url.rfind('/') + 1:]
    os_project_id = job.os_project_id.split(':')[id_count]

    credential_cache = (
        Session.query(CloudCredentialCache)
               .get({"os_project_id": os_project_id,
                     "user_dn": job.user_dn,
                     "storage_name": storage_name})
    )
    if not credential_cache or not credential_cache.os_token_is_expired():
        log.debug("No credential cache to refresh")
        return

    credentials = (
        Session.query(Credential)
               .filter((Credential.proxy.notilike("%CERTIFICATE%")) &
                       (Credential.dn == job.user_dn))
               .all()
    )
    cloud_storage = Session.query(CloudStorage).get(storage_name)

    if cloud_storage:
        for credential in credentials:
            access_token = credential.proxy[:credential.proxy.find(':')]
            cloud_credential = get_os_token(job.user_dn, access_token,
                                            cloud_storage, os_project_id)
            if cloud_credential:
                try:
                    log.debug("OK refresh_os_token")
                    Session.merge(CloudCredentialCache(**cloud_credential))
                    Session.commit()
                    return
                except Exception as ex:
                    log.warning(
                        "Failed to save credentials for dn: %s because: %s"
                        % (job.user_dn, str(ex))
                    )
                    Session.rollback()
                    raise
    log.warning(
        "Cannot refresh OS token for user %s at storage %s"
        % (job.user_dn, storage_name)
    )


def verified_swift_storage_user(user_dn, storage_name):
    try:
        cloud_user = Session.query(CloudStorageUser).filter_by(
            user_dn=user_dn,
            storage_name=storage_name
        ).first()
    except Exception as ex:
        log.warning("Failed to query cloud storage user because: %s" % str(ex))
        return False
    if not cloud_user:
        return False
    return True


def _project_accessible(projects, project_id):
    for project in projects:
        if project.id == project_id:
            return True
    return False


def verified_swift_project_user(cloud_storage, cloud_credential):
    token_auth = v3.token.Token(auth_url=cloud_storage.keystone_url,
                                token=cloud_credential['os_token'])
    sess = session.Session(auth=token_auth)
    try:
        user_id = sess.get_user_id()
        keystone_client = client.Client(session=sess, interface="public")
        projects = keystone_client.projects.list(user=user_id)
        if _project_accessible(projects, cloud_credential['os_project_id']):
            return True
    except Exception as ex:
        log.warning("Failed to verify user have access to project because: %s" % str(ex))
    return False