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

from configparser import ConfigParser
from optparse import OptionParser, IndentedHelpFormatter, SUPPRESS_HELP
import logging
import os
import socket
import sys

from fts3.rest.client import Context
from fts3 import __version__ as CLIENT_VERSION


CONFIG_FILENAME = os.path.expanduser("~/.fts3client.cfg")

CONFIG_DEFAULTSECTION = "Main"
CONFIG_DEFAULTS = {
    "verbose": "false",
    "endpoint": "None",
    "json": "false",
    "ukey": "None",
    "ucert": "None",
}


class _Formatter(IndentedHelpFormatter):
    def format_epilog(self, epilog):
        if not epilog:
            return ""
        else:
            lines = ["Example:"]
            indent = (self.current_indent + self.indent_increment) * " "
            for l in epilog.splitlines():
                nl = l.strip() % {"prog": sys.argv[0]}
                if len(nl) > 0:
                    lines.append(indent + nl)
            return "\n" + "\n".join(lines) + "\n\n"


def _get_local_endpoint():
    """
    Generate an endpoint using the machine hostname
    """
    return "https://%s:8446" % socket.getfqdn()


class Base:
    def __init__(self, extra_args=None, description=None, example=None):
        self.logger = logging.getLogger("fts3")

        # Common CLI options
        usage = None
        if extra_args:
            usage = "usage: %prog [options] " + extra_args

        config = ConfigParser(defaults=CONFIG_DEFAULTS)

        section = CONFIG_DEFAULTSECTION
        config.read(CONFIG_FILENAME)

        # manually set the section in edge cases
        if not config.has_section("Main"):
            section = "DEFAULT"

        # manually get values for which we need to support None
        opt_endpoint = config.get(section, "endpoint")
        if opt_endpoint == "None":
            opt_endpoint = None
        opt_ukey = config.get(section, "ukey")
        if opt_ukey == "None":
            opt_ukey = None
        opt_ucert = config.get(section, "ucert")
        if opt_ucert == "None":
            opt_ucert = None

        self.opt_parser = OptionParser(
            usage=usage, description=description, epilog=example, formatter=_Formatter()
        )

        self.opt_parser.add_option(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="verbose output.",
            default=config.getboolean(section, "verbose"),
        )
        self.opt_parser.add_option(
            "-s",
            "--endpoint",
            dest="endpoint",
            help="FTS3 REST endpoint.",
            default=opt_endpoint,
        )
        self.opt_parser.add_option(
            "-j",
            "--json",
            dest="json",
            action="store_true",
            help="print the output in JSON format.",
            default=config.getboolean(section, "json"),
        )
        self.opt_parser.add_option(
            "--key",
            dest="ukey",
            help="the user certificate private key.",
            default=opt_ukey,
        )
        self.opt_parser.add_option(
            "--cert", dest="ucert", help="the user certificate.", default=opt_ucert
        )
        self.opt_parser.add_option(
            "--capath",
            dest="capath",
            default=None,
            help="use the specified directory to verify the peer",
        )
        self.opt_parser.add_option(
            "--insecure",
            dest="verify",
            default=True,
            action="store_false",
            help="do not validate the server certificate",
        )
        self.opt_parser.add_option(
            "--access-token",
            dest="access_token",
            help="Single OAuth2 access-token for FTS submission plus source and destination tokens.",
            # help="deprecated: Single OAuth2 access-token for FTS submission plus source and destination tokens.",
            default=None,
        )
        self.opt_parser.add_option(
            "--fts-access-token",
            dest="fts_access_token",
            help=SUPPRESS_HELP,
            # help="OAuth2 access-token for FTS submission.  Source and destination tokens must be specified separately.",
            default=None,
        )

    def __call__(self, argv=sys.argv[1:]):
        (self.options, self.args) = self.opt_parser.parse_args(argv)
        if self.options.endpoint is None:
            self.options.endpoint = _get_local_endpoint()
        if self.options.verbose:
            self.logger.setLevel(logging.DEBUG)
        self._access_token_compatibility()
        self.validate()
        return self.run()

    def validate(self):
        """
        Should be implemented by inheriting classes to validate the command line arguments.
        The implementation is assumed to call sys.exit() to abort if needed
        """
        pass

    def run(self):
        """
        Implementation of the command
        """
        raise NotImplementedError(
            "Run method not implemented in %s" % type(self).__name__
        )

    def _create_context(self):
        user_agent = "fts-rest-cli/" + CLIENT_VERSION
        return Context(
            self.options.endpoint,
            ukey=self.options.ukey,
            ucert=self.options.ucert,
            verify=self.options.verify,
            fts_access_token=self.options.fts_access_token,
            capath=self.options.capath,
            user_agent=user_agent,
        )

    def _access_token_compatibility(self):
        if self.options.access_token and self.options.fts_access_token:
            self.opt_parser.error(
                "Cannot use both '--access-token' and '--fts-access-token' simultaneously. (prefer new '--fts-access-token' handle)"
            )
        if self.options.access_token:
            self.options.fts_access_token = self.options.access_token
