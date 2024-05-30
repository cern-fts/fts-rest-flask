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


def _parse_provider(parser, provider_name):
    """
    Parses the FTS configuration file in order to return a tuple of the
    specified provider's url and its parsed options.
    """

    # Construct option names
    provider_url_option_name = provider_name
    client_id_option_name = provider_name + "_ClientId"
    client_secret_option_name = provider_name + "_ClientSecret"
    oauth_scope_fts_option_name = provider_name + "_OauthScopeFts"
    vo_option_name = provider_name + "_VO"

    mandatory_option_names = [
        provider_url_option_name,
        client_id_option_name,
        client_secret_option_name,
    ]
    for mandatory_option_name in mandatory_option_names:
        if not parser.has_option("providers", mandatory_option_name):
            raise ValueError(f"Failed to find the {mandatory_option_name} option")

    # Get option values
    provider_url = parser.get("providers", provider_url_option_name, fallback=None)
    client_id = parser.get("providers", client_id_option_name, fallback=None)
    client_secret = parser.get("providers", client_secret_option_name, fallback=None)
    oauth_scope_fts = parser.get(
        "providers", oauth_scope_fts_option_name, fallback=None
    )
    vo = parser.get("providers", vo_option_name, fallback=None)

    # Sanitize provider URL
    if not provider_url.endswith("/"):
        provider_url += "/"

    # Sanity check values
    if not provider_url:
        raise ValueError(f"The {provider_name} option has an empty value")
    if not client_id:
        raise ValueError(f"The {client_id_option_name} option has an empty value")
    if not client_secret:
        raise ValueError(f"The {client_secret_option_name} option has an empty value")
    if oauth_scope_fts:  # oauth_scope_fts is optional
        nb_oauth_scopes_fts = len(oauth_scope_fts.split())
        if nb_oauth_scopes_fts != 1:
            raise ValueError(
                f"{oauth_scope_fts_option_name} can only contain a single scope: nb_scopes_found={nb_oauth_scopes_fts}"
            )

    parsed_provider = {}
    parsed_provider["client_id"] = client_id
    parsed_provider["client_secret"] = client_secret
    parsed_provider["oauth_scope_fts"] = oauth_scope_fts
    parsed_provider["vo"] = vo

    # Add custom configuration items for this provider
    parsed_provider["custom"] = {}
    custom_options_filter = filter(
        lambda op: provider_name + "_" in op
        and "_Client" not in op
        and provider_name + "_OauthScopeFts" != op,
        parser.options("providers"),
    )
    for item in list(custom_options_filter):
        parsed_provider["custom"][item.lstrip(provider_name + "_")] = parser.get(
            "providers", item
        )

    return (provider_url, parsed_provider)


def _parse_providers(parser):
    """
    Parse the providers section of the specified FTS configuration.
    """

    parsed_providers = {}

    if not parser.has_section("providers"):
        return parsed_providers

    providers_options = parser.options("providers")

    provider_names = [n for n in providers_options if "_" not in n]

    for provider_name in provider_names:
        provider_url, parsed_provider = _parse_provider(parser, provider_name)

        if provider_url in parsed_providers:
            raise ValueError(
                f"Duplicate provider URL found in providers section: provider_url = {provider_url}"
            )

        parsed_providers[provider_url] = parsed_provider

    return parsed_providers


def fts3_config_load(path="/etc/fts3/fts3restconfig", test=False):
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

    # Authorized JWT audiences
    if fts3cfg.get("fts3.AuthorizedAudiences"):
        fts3cfg["fts3.AuthorizedAudiences"] = fts3cfg["fts3.AuthorizedAudiences"].split(
            ";"
        )
    else:
        fts3cfg["fts3.AuthorizedAudiences"] = "https://wlcg.cern.ch/jwt/v1/any"

    # DbType always lowercase
    fts3cfg["fts3.DbType"] = fts3cfg["fts3.DbType"].lower()

    # JobMetadataSizeLimit is an integer
    fts3cfg["fts3.JobMetadataSizeLimit"] = parser.getint(
        "fts3", "JobMetadataSizeLimit", fallback=1024
    )
    # FileMetadataSizeLimit is an integer
    fts3cfg["fts3.FileMetadataSizeLimit"] = parser.getint(
        "fts3", "FileMetadataSizeLimit", fallback=1024
    )
    # StagingMetadataSizeLimit is an integer
    fts3cfg["fts3.StagingMetadataSizeLimit"] = parser.getint(
        "fts3", "StagingMetadataSizeLimit", fallback=1024
    )
    # ArchiveMetadataSizeLimit is an integer
    fts3cfg["fts3.ArchiveMetadataSizeLimit"] = parser.getint(
        "fts3", "ArchiveMetadataSizeLimit", fallback=1024
    )

    # Convert options to boolean
    options = {"Optimizer": True, "AutoSessionReuse": False, "OAuth2": False}

    for key in options:
        try:
            fts3cfg["fts3." + key] = parser.getboolean("fts3", key)
        except NoOptionError:
            fts3cfg["fts3." + key] = options[key]

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
    # SQLAlchemy configuration
    try:
        for name, value in parser.items("sqlalchemy"):
            fts3cfg["sqlalchemy." + name] = value
    except:
        pass

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
    fts3cfg["fts3.Providers"] = _parse_providers(parser)
    try:
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
