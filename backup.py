#!/usr/bin/env python3

import datetime
import json
from sys import stdout

from config import USER, TOKEN


from github import Github
from github import GithubObject
from github import NamedUser
from github import PaginatedList


class JsonDummy(GithubObject.NonCompletableGithubObject):
    def __repr__(self):
        return self.get__repr__(self.attributes)

    def _initAttributes(self):
        self.attributes = GithubObject.NotSet

    def _useAttributes(self, attributes):
        self.attributes = attributes


api = Github(login_or_token=TOKEN)
user = api.get_user(USER)  # type: NamedUser

# ev = user.get_events()
ev = PaginatedList.PaginatedList(
    JsonDummy,
    user._requester,
    user.url + "/events",
    None
)

l = [e.attributes for e in ev]

json.dump(l, stdout, ensure_ascii=False, indent=4, sort_keys=True)
