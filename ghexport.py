#!/usr/bin/env python3
import argparse
import json
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


def get_json(**params):
    return Exporter(**params).export_json()


def main():
    from export_helper import setup_parser
    parser = argparse.ArgumentParser("Exporter for you Github data")
    setup_parser(parser=parser, params=['login_or_token'])
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


if __name__ == '__main__':
    main()
