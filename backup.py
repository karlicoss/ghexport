#!/usr/bin/env python3
import json
import sys
from typing import Dict, NamedTuple, List, Any

from github import Github # type: ignore

Json = Dict[str, Any]


class GithubData(NamedTuple):
    profile: Json

    events: List[Json]
    followers: List[Json]
    following: List[Json]
    # TODO keys? not sure if worth keeping?
    orgs: List[Json]
    received_events: List[Json]
    repos: List[Json]
    starred: List[Json]
    subscriptions: List[Json]
    watched: List[Json]


class Exporter:
    def __init__(self, *args, **kwargs) -> None:
        self.api = Github(*args, **kwargs)

    def export_json(self) -> Json:
        login = self.api.get_user().login
        user = self.api.get_user(login) # need to get NamedUser first

        fields = list(GithubData._fields)
        fields.remove('profile')

        gd = GithubData(
            profile=user._rawData,
            **{f: [x._rawData for x in getattr(user, 'get_' + f)()] for f in fields},
        )
        return gd._asdict()


from github_secrets import GITHUB_TOKEN_2 as login_or_token


def main():
    e = Exporter(login_or_token=login_or_token)
    json.dump(e.export_json(), sys.stdout, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
