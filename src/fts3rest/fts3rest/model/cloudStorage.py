#   Copyright 2014-2020 CERN
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
from sqlalchemy import Column, String, ForeignKey, Enum, Boolean, Index
from .base import Base
import enum


class CloudStorage(Base):
    __tablename__ = "t_cloudStorage"

    cloudstorage_name = Column(String(150),
                               primary_key=True,
                               name="cloudStorage_name")

    cloud_type = Column('cloud_type', Enum('S3', 'Gcloud', 'Swift'), default='S3', nullable=False)


class CloudStorageS3(Base):
    __tablename__ = "t_cloudStorage_s3"

    cloudStorage_name = Column(String(150),
                               # ForeignKey("t_cloudStorage.cloudStorage_name"),
                               primary_key=True,
                               name="cloudStorage_name")

    alternate = Column(Boolean, default=False, nullable=False)
    region = Column(String(255), nullable=False)


class CloudStorageGcloud(Base):
    __tablename__ = "t_cloudStorage_gcloud"

    cloudStorage_name = Column(String(150),
                               # ForeignKey("t_cloudStorage.cloudStorage_name"),
                               primary_key=True,
                               name="cloudStorage_name")

    auth_file = Column(String(255), nullable=False)


class CloudStorageSwift(Base):
    __tablename__ = "t_cloudStorage_swift"

    cloudStorage_name = Column(String(150),
                               # ForeignKey("t_cloudStorage.cloudStorage_name"),
                               primary_key=True,
                               name="cloudStorage_name")

    os_project_id = Column(String(255), nullable=False)
    os_token = Column(String(255), nullable=False)


class CloudStorageUser(Base):
    __tablename__ = "t_cloudStorage_user"

    user_dn = Column(String(700), primary_key=True)
    cloudStorage_name = Column(
        String(150),
        ForeignKey("t_cloudStorage.cloudStorage_name"),
        primary_key=True,
        name="cloudStorage_name",
        )
    access_key = Column(String(255))
    secret_key = Column(String(255))
    vo_name = Column(String(100), primary_key=True),
    Index('csname_userdn_voname_UNIQUE', 'cloudstorage_name', 'vo_name', 'user_dn', unique=True)

    def is_access_requested(self):
        return not (self.request_token is None or self.request_token_secret is None)

    def is_registered(self):
        return not (self.access_token is None or self.access_token_secret is None)
