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

import sys

from fts3.rest.client import Inquirer
from fts3.rest.client import JobActiveStates, JobTerminalStates, JobStates
from .base import Base
from .utils import *


class JobLister(Base):
    def __init__(self):
        super(JobLister, self).__init__(
            description="This command can be used to list the running jobs, allowing various filters: user dn, VO name, source SE, destination SE and/or job status",
            example="""
            $ %(prog)s -s https://fts3-devel.cern.ch:8446 -o atlas
            Request ID: ff294db7-655a-4c0a-9efb-44a994677bb3
            Status: ACTIVE
            Client DN: /DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=ddmadmin/CN=531497/CN=Robot: ATLAS Data Management
            Reason: None
            Submission time: 2014-04-15T07:05:38
            Priority: 3
            VO Name: atlas

            Request ID: a2e4586c-760a-469e-8303-d0f3d5aadc73
            Status: READY
            Client DN: /DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=ddmadmin/CN=531497/CN=Robot: ATLAS Data Management
            Reason: None
            Submission time: 2014-04-15T07:07:33
            Priority: 3
            VO Name: atlas
            """,
        )
        # Specific options
        self.opt_parser.add_option(
            "-u", "--userdn", dest="user_dn", help="query only for the given user"
        )
        self.opt_parser.add_option(
            "-o", "--voname", dest="vo_name", help="query only for the given VO"
        )
        self.opt_parser.add_option(
            "--source",
            dest="source_se",
            help="query only for the given source storage element",
        )
        self.opt_parser.add_option(
            "--destination",
            dest="dest_se",
            help="query only for the given destination storage element",
        )

        self.opt_parser.add_option(
            "--status",
            dest="job_status",
            help="query only for the given job states (comma-separated list)",
        )

        self.opt_parser.add_option(
            "--timewindow",
            dest="time_window",
            help="restrict query to jobs finished within the given time window (HH:MM). "
            "Mandatory when querying terminal job states",
        )

    def run(self):
        context = self._create_context()
        inquirer = Inquirer(context)
        job_list = inquirer.get_job_list(
            self.options.user_dn,
            self.options.vo_name,
            self.options.source_se,
            self.options.dest_se,
            state_in=self.options.job_status,
            time_window=self.options.time_window,
        )
        if not self.options.json:
            self.logger.info(job_list_human_readable(job_list))
        else:
            self.logger.info(job_list_as_json(job_list))

    def validate(self):
        self._validate_time_window()
        self.options.job_status, terminal = self._validate_job_status()

        if terminal and not self.options.time_window:
            self.logger.critical(
                f"--timewindow is needed when querying terminal job states: [{', '.join(JobTerminalStates)}]"
            )
            sys.exit(1)

        if self.options.time_window and not terminal:
            self.logger.warning(
                "--timewindow only applies to terminal job states (will be ignored)"
            )
            self.options.time_window = None

        return super().validate()

    def _validate_time_window(self):
        if not self.options.time_window:
            return
        try:
            hours, minutes = map(int, self.options.time_window.split(":"))
            if hours < 0 or minutes < 0 or minutes > 59:
                raise ValueError
        except ValueError:
            self.logger.critical(
                'Invalid --timewindow value: must be in "HH:MM" format (e.g. 01:00)'
            )
            sys.exit(1)

    def _validate_job_status(self):
        if not self.options.job_status:
            return None, []
        states = [
            state.strip().upper()
            for state in self.options.job_status.split(",")
            if state.strip()
        ]
        if not states:
            self.logger.critical(f'Invalid --status value: "{self.options.job_status}"')
            sys.exit(1)

        invalid = [state for state in states if state not in JobStates]
        if invalid:
            self.logger.critical(
                f"Invalid job state(s) in --status: {', '.join(invalid)} (allowed: [{', '.join(JobStates)}])"
            )
            sys.exit(1)

        terminal = [state for state in states if state in JobTerminalStates]
        active = [state for state in states if state in JobActiveStates]

        if terminal and active:
            self.logger.critical(
                f"Cannot mix terminal ({', '.join(terminal)}) and non-terminal job states ({', '.join(active)}) in --status!"
            )
            sys.exit(1)

        return states, terminal
