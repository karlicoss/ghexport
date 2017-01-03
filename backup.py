import datetime

from config import USER, TOKEN, DIR

import json

from atomicwrites import atomic_write

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


today = datetime.date.today()
path = DIR.joinpath("events_" + today.strftime('%Y_%m_%d')).with_suffix('.json').as_posix()
print("Backing up to " + path)

with atomic_write(path, overwrite=True) as fo:
    json.dump(l, fo, ensure_ascii=False, indent=4)
