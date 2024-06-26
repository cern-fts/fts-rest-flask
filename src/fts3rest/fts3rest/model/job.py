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
from sqlalchemy import Column, DateTime, Integer, String, Enum
from sqlalchemy.orm import relation, backref

from .base import Base, Flag, TernaryFlag, Json
from .file import ArchivedFile

JobActiveStates = [
    "STAGING",
    "SUBMITTED",
    "READY",
    "ACTIVE",
    "DELETE",
    "ARCHIVING",
    "QOS_TRANSITION",
    "QOS_REQUEST_SUBMITTED",
]
JobTerminalStates = ["FINISHED", "FAILED", "FINISHEDDIRTY", "CANCELED"]


class Job(Base):
    __tablename__ = "t_job"

    job_id = Column(String(36), primary_key=True)
    source_se = Column(String(255))
    dest_se = Column(String(255))
    job_state = Column(Enum(*(JobActiveStates + JobTerminalStates)))
    job_type = Column(String(1), default="N")
    cancel_job = Column(Flag(negative=None))
    submit_host = Column(String(255))
    user_dn = Column(String(1024))
    cred_id = Column(String(100))
    vo_name = Column(String(50))
    reason = Column(String(2048))
    submit_time = Column(DateTime)
    priority = Column(Integer)
    max_time_in_queue = Column(Integer)
    destination_spacetoken = Column(String(255), name="space_token")
    internal_job_params = Column(String(255))
    dst_file_report = Column(Flag)
    overwrite_flag = Column(String(1))
    job_finished = Column(DateTime)
    source_spacetoken = Column(String(255), name="source_space_token")
    copy_pin_lifetime = Column(Integer)
    verify_checksum = Column(String(1), name="checksum_method")
    bring_online = Column(Integer)
    archive_timeout = Column(Integer)
    target_qos = Column(String(255))
    job_metadata = Column(Json(255))
    retry = Column(Integer)
    retry_delay = Column(Integer, default=0)
    os_project_id = Column(String(512))

    files = relation("File", uselist=True, lazy=True, backref=backref("job", lazy=True))

    dm = relation(
        "DataManagement", uselist=True, lazy=True, backref=backref("job", lazy=True)
    )

    def isFinished(self):
        return self.job_state not in JobActiveStates

    def __str__(self):
        return self.job_id


class ArchivedJob(Base):
    __tablename__ = "t_job_backup"

    job_id = Column(String(36), primary_key=True)
    source_se = Column(String(255))
    dest_se = Column(String(255))
    job_state = Column(String(32))
    job_type = Column(String(1), default="N")
    cancel_job = Column(Flag(negative=None))
    submit_host = Column(String(255))
    user_dn = Column(String(1024))
    cred_id = Column(String(100))
    vo_name = Column(String(50))
    reason = Column(String(2048))
    submit_time = Column(DateTime)
    priority = Column(Integer)
    max_time_in_queue = Column(Integer)
    destination_spacetoken = Column(String(255), name="space_token")
    internal_job_params = Column(String(255))
    dst_file_report = Column(Flag)
    overwrite_flag = Column(String(1))
    job_finished = Column(DateTime)
    source_spacetoken = Column(String(255), name="source_space_token")
    copy_pin_lifetime = Column(Integer)
    verify_checksum = Column(String(1), name="checksum_method")
    bring_online = Column(Integer)
    archive_timeout = Column(Integer)
    target_qos = Column(String(255))
    job_metadata = Column(Json(255))
    retry = Column(Integer)

    files = relation(
        "ArchivedFile",
        uselist=True,
        lazy=True,
        backref=backref("job", lazy=True),
        primaryjoin=(ArchivedFile.job_id == job_id),
    )

    def __str__(self):
        return self.job_id
