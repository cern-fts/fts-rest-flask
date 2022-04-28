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

import copy
import hashlib
import logging
import re

from fts3rest.model import AuthorizationByDn
from fts3rest.model.meta import Session
from fts3rest.model.config import Gridmap
from fts3rest.lib.middleware.fts3auth.methods import Authenticator

log = logging.getLogger(__name__)


def vo_from_fqan(fqan):
    """
    Get the VO from a full FQAN

    Args:
        fqan: A single fqans (i.e. /dteam/cern/Role=lcgadmin)
    Returns:
        The vo + group (i.e. dteam/cern)
    """
    components = fqan.split("/")[1:]
    groups = []
    for c in components:
        if c.lower().startswith("role="):
            break
        groups.append(c)
    return "/".join(groups)


def generate_delegation_id(dn, fqans):
    """
    Generate a delegation ID from the user DN and FQANS
    Adapted from FTS3
    See https://svnweb.cern.ch/trac/fts3/browser/trunk/src/server/ws/delegation/GSoapDelegationHandler.cpp

    Args:
        dn:    The user DN
        fqans: A list of fqans
    Returns:
        The associated delegation id
    """
    d = hashlib.sha1()  # nosec
    d.update(dn.encode("utf-8"))

    for fqan in fqans:
        d.update(fqan.encode("utf-8"))

    # Original implementation only takes into account first 16 characters
    return d.hexdigest()[:16]


def gridmap_vo(user_dn):
    """
    Retrieves the pre-set VO for a given user DN from the Gridmap table
    """
    gridmap = Session.query(Gridmap).filter(Gridmap.dn == user_dn).first()
    if gridmap:
        log.debug("Gridmap: {} -- {}".format(gridmap.dn, gridmap.vo))
        return gridmap.vo
    return None


class InvalidCredentials(Exception):
    """
    Credentials have been provided, but they are invalid
    """

    pass


class UserCredentials:
    """
    Handles the user credentials and privileges
    """

    authenticator = Authenticator()
    role_regex = re.compile("(/.+)*/Role=(\\w+)(/.*)?", re.IGNORECASE)

    def _anonymous(self):
        """
        Not authenticated access
        """
        self.user_dn = "anon"
        self.method = "unauthenticated"
        self.dn.append(self.user_dn)

    def __init__(self, env, role_permissions=None, config=None):
        """
        Constructor

        Args:
            env:              Environment (i.e. os.environ)
            role_permissions: The role permissions as configured in the FTS3 config file
        """
        # Default
        self.user_dn = None
        self.dn = []
        self.base_id = []
        self.voms_cred = []
        self.vos = []
        self.vos_id = []
        self.roles = []
        self.level = []
        self.delegation_id = None
        self.method = None
        self.is_root = False

        got_creds = self.authenticator(self, env, config)

        # Last resort: anonymous access
        if not got_creds:
            self._anonymous()
        else:
            # Populate roles
            self.roles = self._populate_roles()
            # And granted level
            self.level = self._granted_level(role_permissions)

    def _populate_roles(self):
        """
        Get roles out of the FQANS
        """
        roles = []
        for fqan in self.voms_cred:
            match = UserCredentials.role_regex.match(fqan)
            if match and match.group(2).upper() != "NULL":
                roles.append(match.group(2))
        return roles

    def _granted_level(self, role_permissions):
        """
        Get all granted levels for this user out of the configuration
        (all levels authorized for public, plus those for the given Roles)
        """
        if self.is_root:
            return {
                "transfer": "all",
                "deleg": "all",
                "config": "all",
                "datamanagement": "all",
            }

        granted_level = dict()

        # Public apply to anyone
        if role_permissions is not None:
            if "public" in role_permissions:
                granted_level = copy.deepcopy(role_permissions["public"])

            # Roles from the proxy
            for grant in self.roles:
                if grant in role_permissions:
                    granted_level.update(copy.deepcopy(role_permissions[grant]))

        # DB Configuration
        for grant in (
            Session.query(AuthorizationByDn)
            .filter(AuthorizationByDn.dn == self.user_dn)
            .all()
        ):
            log.info(
                '%s granted to "%s" because it is configured in the database'
                % (grant.operation, self.user_dn)
            )
            granted_level[grant.operation] = "all"

        return granted_level

    def get_granted_level_for(self, operation):
        """
        Check if the user can perform the operation 'operation'

        Args:
            operation: The operation to check (see constants.py)

        Returns:
            None if the user can not perform the operation
            constants.VO if only can perform it on same VO resources
            constants.ALL if can perform on any resource
            constants.PRIVATE if can perform only on his/her own resources
        """
        if operation in self.level:
            return self.level[operation]
        elif "*" in self.level:
            return self.level["*"]
        else:
            return None

    def has_vo(self, vo):
        """
        Check if the user belongs to the given VO

        Args:
            vo: The VO name (i.e. dteam)

        Returns:
            True if the user credentials include the given VO
        """
        return vo in self.vos
