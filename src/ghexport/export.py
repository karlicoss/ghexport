#!/usr/bin/env python3
import argparse
import json
from typing import NamedTuple, List, Any

import github
#github.enable_console_debug_logging()

from .exporthelpers.export_helper import Json


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
        self.api = github.Github(*args, **kwargs)

    def export_json(self) -> Json:
        login = self.api.get_user().login
        user = self.api.get_user(login) # need to get NamedUser first

        fields = list(GithubData._fields)
        fields.remove('profile')

        gd = GithubData(
            profile=user._rawData, # type: ignore[attr-defined]
            **{f: [x._rawData for x in getattr(user, 'get_' + f)()] for f in fields},
        )

        ##  get traffic (it's only kept for 14 days :( )
        for r in gd.repos:
            # todo not ideal that we retrieve it all over again..
            repo = self.api.get_repo(r['full_name'])

            fields = ['views', 'clones', 'popular/referrers', 'popular/paths']
            # todo ugh. this vvv doesn't quite work because returned types are different (lists vs github. objects)
            # [x._rawData for x in getattr(repo, 'get_' + f)()]
            # and pygithub library doesn't expose raw api properly...
            def fetch(f: str) -> Json:
                path = repo.url + '/traffic/' + f
                ge = None  # type: ignore
                attempts = 5
                # NOTE: ugh. sometimes it just throws 500 on this endpoint for no reason, and then immediately after it works??
                # started happening around 20220305 :shrug:
                for attempt in range(attempts):
                    try:
                        return repo._requester.requestJsonAndCheck('GET', path)[1]  # type: ignore[attr-defined]
                    except github.GithubException as ge:
                        if ge.status != 500:
                            raise ge
                assert ge is not None
                raise ge

            traffic = {f: fetch(f) for f in fields}
            assert 'traffic' not in r # just in case..
            r['traffic'] = traffic
            # TODO not sure if this is a good way to keep it...
        ##

        return gd._asdict()


def get_json(**params) -> Json:
    return Exporter(**params).export_json()


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


def make_parser():
    from .exporthelpers.export_helper import setup_parser, Parser
    parser = Parser('''
Export your Github personal data: issues, PRs, comments, followers and followings, etc.

*Note*: this only deals with metadata. If you want a download of actual git repositories, I recommend using [[https://github.com/josegonzalez/python-github-backup][python-github-backup]].
'''.strip())
    # TODO repositories?
    setup_parser(
        parser=parser,
        params=['token'],
        extra_usage='''
You can also import ~ghexport.export~ as a module and call ~get_json~ function directly to get raw JSON.
        ''',
    )
    return parser



if __name__ == '__main__':
    main()
