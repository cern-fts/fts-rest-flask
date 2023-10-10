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
from datetime import datetime
from sqlalchemy import Column, DateTime, Text, String

from .base import Base


class Token(Base):
    __tablename__ = "t_token"

    token_id = Column(String(16), primary_key=True)
    access_token = Column(Text)
    refresh_token = Column(Text)
    issuer = Column(Text)
