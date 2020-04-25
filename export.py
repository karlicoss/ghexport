#!/usr/bin/env python3
import argparse
import json
from typing import NamedTuple, List, Any

from github import Github # type: ignore


from export_helper import Json


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
        kwargs['login_or_token'] = kwargs['token']
        del kwargs['token']
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

        ##  get traffic (it's only kept for 14 days :( )
        for r in gd.repos:
            # todo not ideal that we retrieve it all over again..
            repo = self.api.get_repo(r['full_name'])

            fields = ['views', 'clones', 'popular/referrers', 'popular/paths']
            # todo ugh. this vvv doesn't quite work because returned types are different (lists vs github. objects)
            # [x._rawData for x in getattr(repo, 'get_' + f)()]
            # ad github library doesn't expose raw api properly...
            traffic = {
                f: repo._requester.requestJsonAndCheck('GET', repo.url + '/traffic/' + f)[1]
                for f in fields
            }

            assert 'traffic' not in r # just in case..
            r['traffic'] = traffic
            # TODO not sure if this is a good way to keep it...
        ##

        return gd._asdict()


def get_json(**params):
    return Exporter(**params).export_json()


def main():
    parser = make_parser()
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


def make_parser():
    from export_helper import setup_parser, Parser
    parser = Parser('''
Export your Github personal data: issues, PRs, comments, followers and followings, etc.

*Note*: this only deals with metadata. If you want a download of actual git repositories, I recommend using [[https://github.com/josegonzalez/python-github-backup][python-github-backup]].
'''.strip())
    # TODO repositories?
    setup_parser(
        parser=parser,
        params=['token'],
        extra_usage='''
You can also import ~export.py~ as a module and call ~get_json~ function directly to get raw JSON.
        ''',
    )
    return parser



if __name__ == '__main__':
    main()
