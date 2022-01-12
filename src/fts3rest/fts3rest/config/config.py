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

from configparser import ConfigParser, NoOptionError, NoSectionError
from urllib.parse import quote_plus
import os
import logging

log = logging.getLogger(__name__)


def fts3_config_load(path="/etc/fts3/ftsrestconfig", test=False):
    """
    Read the configuration from the FTS3 configuration file
    """
    fts3cfg = {}

    parser = ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read_file(path)

    # Map all options
    for name, value in parser.items("fts3"):
        fts3cfg["fts3." + name] = value

    # AuthorizedVO is an array
    fts3cfg["fts3.AuthorizedVO"] = fts3cfg["fts3.AuthorizedVO"].split(";")

    # DbType always lowercase
    fts3cfg["fts3.DbType"] = fts3cfg["fts3.DbType"].lower()

    # Optimizer is a boolean
    try:
        fts3cfg["fts3.Optimizer"] = parser.getboolean("fts3", "Optimizer")
    except NoOptionError:
        fts3cfg["fts3.Optimizer"] = True

    # Put something in SiteName
    if "fts3.SiteName" not in fts3cfg:
        fts3cfg["fts3.SiteName"] = ""

    # Prepare database connection url
    if len(fts3cfg["fts3.DbConnectString"]) > 0:
        if (
            fts3cfg["fts3.DbConnectString"][0] == '"'
            and fts3cfg["fts3.DbConnectString"][-1] == '"'
        ):
            fts3cfg["fts3.DbConnectString"] = fts3cfg["fts3.DbConnectString"][1:-1]

    if fts3cfg["fts3.DbType"] == "mysql":
        fts3cfg["sqlalchemy.url"] = "mysql://%s:%s@%s" % (
            fts3cfg["fts3.DbUserName"],
            quote_plus(fts3cfg["fts3.DbPassword"]),
            fts3cfg["fts3.DbConnectString"],
        )
    elif fts3cfg["fts3.DbType"] == "sqlite":
        if fts3cfg["fts3.DbConnectString"] and not fts3cfg[
            "fts3.DbConnectString"
        ].startswith("/"):
            fts3cfg["fts3.DbConnectString"] = os.path.abspath(
                fts3cfg["fts3.DbConnectString"]
            )
        fts3cfg["sqlalchemy.url"] = "sqlite:///%s" % fts3cfg["fts3.DbConnectString"]
    elif fts3cfg["fts3.DbType"] == "oracle":
        fts3cfg["sqlalchemy.url"] = "oracle://%s:%s@%s" % (
            fts3cfg["fts3.DbUserName"],
            quote_plus(fts3cfg["fts3.DbPassword"]),
            fts3cfg["fts3.DbConnectString"],
        )
    else:
        raise ValueError(
            "Database type '%s' is not recognized" % fts3cfg["fts3.DbType"]
        )
    # SQLAlquemy configuration
    fts3cfg["sqlalchemy.pool_timeout"] = fts3cfg["fts3.pool_timeout"]
    fts3cfg["sqlalchemy.pool_size"] = fts3cfg["fts3.pool_size"]

    # Initialize roles
    fts3cfg["fts3.Roles"] = {}
    for role in parser.options("roles"):
        granted_array = parser.get("roles", role).split(";")
        for granted in granted_array:
            if granted.find(":") == -1:
                level = ""
                operation = granted
            else:
                (level, operation) = granted.split(":")
            if role.lower() not in fts3cfg["fts3.Roles"]:
                fts3cfg["fts3.Roles"][role.lower()] = {}
            fts3cfg["fts3.Roles"][role.lower()][operation.lower()] = level.lower()

    # Initialize providers
    fts3cfg["fts3.Providers"] = {}
    try:
        for option in parser.options("providers"):
            if "_" not in option:
                provider_name = option
                provider_url = parser.get("providers", provider_name)
                if test and not provider_url.endswith("/"):
                    provider_url += "/"

                fts3cfg["fts3.Providers"][provider_url] = {}
                client_id = parser.get("providers", option + "_ClientId")
                fts3cfg["fts3.Providers"][provider_url]["client_id"] = client_id
                client_secret = parser.get("providers", option + "_ClientSecret")
                fts3cfg["fts3.Providers"][provider_url]["client_secret"] = client_secret
        fts3cfg["fts3.ValidateAccessTokenOffline"] = parser.getboolean(
            "fts3", "ValidateAccessTokenOffline", fallback=True
        )
        fts3cfg["fts3.JWKCacheSeconds"] = parser.getint(
            "fts3", "JWKCacheSeconds", fallback=86400
        )
        fts3cfg["fts3.TokenRefreshDaemonIntervalInSeconds"] = parser.getint(
            "fts3", "TokenRefreshDaemonIntervalInSeconds", fallback=600
        )
    except NoSectionError:
        pass
    if test:
        if "xdc_ClientId" in os.environ:  # for open id tests
            provider_url = "https://iam.extreme-datacloud.eu/"
            fts3cfg["fts3.Providers"][provider_url] = {}
            fts3cfg["fts3.Providers"][provider_url]["client_id"] = os.environ[
                "xdc_ClientId"
            ]
            fts3cfg["fts3.Providers"][provider_url]["client_secret"] = os.environ[
                "xdc_ClientSecret"
            ]
        else:
            fts3cfg["fts3.Providers"] = {}
    return fts3cfg
