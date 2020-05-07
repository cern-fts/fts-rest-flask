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


from fts3rest.model import Credential, LinkConfig, Job

from fts3rest.model.meta import Session
from flask import request
from fts3rest.lib.middleware.fts3auth.authorization import authorize
from fts3rest.lib.middleware.fts3auth.constants import *
from fts3rest.lib.helpers.jsonify import jsonify


@authorize(CONFIG)
@jsonify
def autocomplete_dn():
    """
    Autocomplete for users' dn
    """
    term = request.values.get("term", "/DC=cern.ch")
    matches = (
        Session.query(Credential.dn)
        .filter(Credential.dn.startswith(term))
        .distinct()
        .all()
    )
    return [r[0] for r in matches]


@authorize(CONFIG)
@jsonify
def autocomplete_source():
    """
    Autocomplete source SE
    """
    term = request.values.get("term", "srm://")
    matches = (
        Session.query(LinkConfig.source)
        .filter(LinkConfig.source.startswith(term))
        .distinct()
        .all()
    )
    return [r[0] for r in matches]


@authorize(CONFIG)
@jsonify
def autocomplete_destination():
    """
    Autocomplete destination SE
    """
    term = request.values.get("term", "srm://")
    matches = (
        Session.query(LinkConfig.destination)
        .filter(LinkConfig.destination.startswith(term))
        .distinct()
        .all()
    )
    return [r[0] for r in matches]


@authorize(CONFIG)
@jsonify
def autocomplete_storage():
    """
    Autocomplete a storage, regardless of it being source or destination
    """
    term = request.values.get("term", "srm://")
    src_matches = (
        Session.query(LinkConfig.source)
        .filter(LinkConfig.source.startswith(term))
        .distinct()
        .all()
    )
    dest_matches = (
        Session.query(LinkConfig.destination)
        .filter(LinkConfig.destination.startswith(term))
        .distinct()
        .all()
    )

    srcs = map(lambda r: r[0], src_matches)
    dsts = map(lambda r: r[0], dest_matches)

    return set(srcs).union(set(dsts))


@authorize(CONFIG)
@jsonify
def autocomplete_vo():
    """
    Autocomplete VO
    """
    term = request.values.get("term", "srm://")
    matches = (
        Session.query(Job.vo_name).filter(Job.vo_name.startswith(term)).distinct().all()
    )
    return [r[0] for r in matches]
