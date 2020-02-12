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

import json
from urllib.parse import quote


class Ban:
    def __init__(self, context):
        self.context = context

    def ban_dn(self, dn):
        answer = self.context.post_json("/ban/dn", {"user_dn": dn})
        return json.loads(answer)

    def ban_se(self, se, status, timeout, allow_submit):
        answer = self.context.post_json(
            "/ban/se",
            {
                "storage": se,
                "status": status,
                "timeout": timeout,
                "allow_submit": allow_submit,
            },
        )
        return json.loads(answer)

    def unban_dn(self, dn):
        self.context.delete("/ban/dn?user_dn=%s" % quote(dn, ""))

    def unban_se(self, se):
        self.context.delete("/ban/se?storage=%s" % quote(se, ""))
