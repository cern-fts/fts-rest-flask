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

import glob

from flask.views import View
from fts3rest.model import SchemaVersion


from fts3rest.model.meta import Session


from fts3rest.lib.api.submit_schema import SubmitSchema
from werkzeug.exceptions import NotFound
from fts3rest.lib.helpers.jsonify import jsonify

API_VERSION = dict(major=3, minor=12, patch=1)


# TODO migrate correctly if necessary.
# Some of this code may have not been converted to Flask yet


def _get_fts_core_version():
    versions = []
    for match in glob.glob("/usr/share/doc/fts-libs-*"):
        try:
            major, minor, patch = match.split("-")[-1].split(".")
            versions.append(dict(major=major, minor=minor, patch=patch))
        except Exception:
            pass
    if len(versions) == 0:
        return None
    elif len(versions) == 1:
        return versions[0]
    else:
        return versions


class Api(View):
    """
    API documentation
    """

    def __init__(self):
        super().__init__()
        # self.resources, self.apis, self.models = introspect()
        # self.resources.sort(key=lambda res: res["id"])
        # for r in self.apis.values():
        #     r.sort(key=lambda a: a["path"])
        # # Add path to each resource
        # for r in self.resources:
        #     r["path"] = "/" + r["id"]

        self.fts_core_version = _get_fts_core_version()


class api_version(Api):
    @jsonify
    def dispatch_request(self):
        schema_v = (
            Session.query(SchemaVersion)
            .order_by(
                SchemaVersion.major.desc(),
                SchemaVersion.minor.desc(),
                SchemaVersion.patch.desc(),
            )
            .first()
        )
        return {
            "delegation": dict(major=1, minor=0, patch=0),
            "api": API_VERSION,
            "core": self.fts_core_version,
            "schema": schema_v,
            "_links": {
                "curies": [{"name": "fts", "href": "https://gitlab.cern.ch/fts/fts3"}],
                "fts:whoami": {"href": "/whoami", "title": "Check user certificate"},
                "fts:joblist": {
                    "href": "/jobs{?vo_name,user_dn,dlg_id,state_in}",
                    "title": "List of active jobs",
                    "templated": True,
                },
                "fts:job": {
                    "href": "/jobs/{id}",
                    "title": "Job information",
                    "templated": True,
                    "hints": {"allow": ["GET", "DELETE"]},
                },
                "fts:configaudit": {"href": "/config/audit", "title": "Configuration"},
                "fts:submitschema": {
                    "href": "/api-docs/schema/submit",
                    "title": "JSON schema of messages",
                },
                "fts:apidocs": {"href": "/api-docs/", "title": "API Documentation"},
                "fts:jobsubmit": {
                    "href": "/jobs",
                    "hints": {
                        "allow": ["POST"],
                        "representations": ["fts:submitschema"],
                    },
                },
                "fts:optimizer": {"href": "/optimizer/", "title": "Optimizer"},
                "fts:archive": {"href": "/archive/", "title": "Archive"},
            },
        }


class submit_schema(Api):
    @jsonify
    def dispatch_request(self):
        """
        Json-schema for the submission operation

        This can be used to validate the submission. For instance, in Python,
        jsonschema.validate
        """
        return SubmitSchema


class api_docs(Api):
    @jsonify
    def dispatch_request(self):
        """
        Auto-generated API documentation

        Compatible with Swagger-UI
        """
        raise NotFound
        # return {
        #     "swaggerVersion": "1.2",
        #     "apis": self.resources,
        #     "info": {
        #         "title": "FTS3 RESTful API",
        #         "description": "FTS3 RESTful API documentation",
        #         "contact": "fts-devel@cern.ch",
        #         "license": "Apache 2.0",
        #         "licenseUrl": "http://www.apache.org/licenses/LICENSE-2.0.html",
        #     },
        # }


class resource_doc(Api):
    @jsonify
    def dispatch_request(self, resource):
        """
        Auto-generated API documentation for a specific resource
        """
        raise NotFound
        # if resource not in self.apis:
        #     raise NotFound("API not found: " + resource)
        # return {
        #     "basePath": "/",
        #     "swaggerVersion": "1.2",
        #     "produces": ["application/json"],
        #     "resourcePath": "/" + resource,
        #     "authorizations": {},
        #     "apis": self.apis.get(resource, []),
        #     "models": self.models.get(resource, []),
        # }
