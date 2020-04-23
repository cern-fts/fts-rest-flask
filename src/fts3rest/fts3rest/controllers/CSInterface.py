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


from fts3rest.controllers.CSdropbox import DropboxConnector
from abc import ABC, abstractmethod


class Connector(ABC):
    def __init__(self, user_dn, service):
        self.user_dn = user_dn.strip()
        self.service = service.strip().upper()

    @staticmethod
    def factory(user_dn, service):
        if service == "DROPBOX":
            return DropboxConnector(user_dn, service)

    @abstractmethod
    def is_registered(self):
        raise NotImplementedError

    @abstractmethod
    def remove_token(self):
        raise NotImplementedError

    @abstractmethod
    def get_access_requested(self):
        raise NotImplementedError

    @abstractmethod
    def is_access_requested(self):
        raise NotImplementedError

    @abstractmethod
    def get_access_granted(self):
        raise NotImplementedError

    @abstractmethod
    def get_folder_content(self):
        raise NotImplementedError

    @abstractmethod
    def get_file_link(self, file_path):
        raise NotImplementedError
