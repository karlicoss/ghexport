from __future__ import annotations

import argparse
import json
import warnings
from typing import Optional

import github
from github.Repository import Repository

# github.enable_console_debug_logging()
from .exporthelpers.export_helper import Json, Parser, setup_parser

_ALL_FIELDS = [
    'profile',
    'events',
    'gists',
    'followers',
    'following',
    'orgs',
    # TODO not convinced it really works? returns empty results for me
    # but seems like github projects are a bit of a mess
    # there are some 'classic' ones and 'new' ones for which graphql is recommended?
    'projects',
    'received_events',
    'repos',
    'starred',
    'subscriptions',
    'watched',
]


_TRAFFIC = 'traffic'


class Exporter:
    def __init__(
        self,
        *args,
        token: str,
        include: Optional[list[str]] = None,
        include_repos_traffic: Optional[bool] = None,
        **kwargs,
    ) -> None:
        kwargs['login_or_token'] = token
        self.api = github.Github(*args, **kwargs)
        self.fields_to_export = _ALL_FIELDS if include is None else include
        assert len(self.fields_to_export) > 0  # just in case
        # for now including repos traffic by default, might change in the future?
        self.include_repos_traffic = True if include_repos_traffic is None else include_repos_traffic

    def export_json(self) -> Json:
        login = self.api.get_user().login
        user = self.api.get_user(login)  # need to get NamedUser first

        ## check that ghexport handles all avaiable data
        for method in dir(user):
            if not method.startswith('get_'):
                continue
            if method in [
                'get__repr__',
                'get_repo',  # takes name and returns one repo
                'get_organization_membership',  # only checks membership
                'get_keys',  # these are public keys, but still not convinced it shoud be included..
                'get_public_events',  # subset of events
                'get_public_received_events',  # subset of received_events
            ]:
                continue
            field = method[len('get_') :]
            if field not in _ALL_FIELDS:
                warnings.warn(f"'{field}' data isn't handled -- please report this https://github.com/karlicoss/ghexport/issues")
        ##

        json_data = {}
        for f in self.fields_to_export:
            if f == 'profile':
                res = getattr(user, '_rawData')  # getattr makes mypy happy
            else:
                args = {}
                if f == 'projects':
                    args = {'state': 'all'}
                objects = getattr(user, f'get_{f}')(**args)
                res = [o._rawData for o in objects]
                if f == 'repos' and self.include_repos_traffic:
                    # populate repo with traffic data
                    for repo, jr in zip(objects, res):
                        assert _TRAFFIC not in jr, jr  # just in case..
                        # TODO not sure if this is a good way to keep it...
                        jr[_TRAFFIC] = self._fetch_traffic(repo=repo)
            json_data[f] = res

        return json_data

    def _fetch_traffic(self, *, repo: Repository) -> Optional[Json]:
        ##  get traffic (it's only kept for 14 days :( )
        if repo.archived:
            # since approx. August 2022 it started failing with
            # github.GithubException.GithubException: 403 {"message": "Must have push access to repository",
            # 'Traffic' tab also isn't present in the web so I guess they just arent' keeping it anymore
            return None

        traffic_fields = ['views', 'clones', 'popular/referrers', 'popular/paths']

        # todo ugh. this vvv doesn't quite work because returned types are different (lists vs github. objects)
        # [x._rawData for x in getattr(repo, 'get_' + f)()]
        # and pygithub library doesn't expose raw api properly...
        def fetch(f: str) -> Json:
            path = repo.url + '/traffic/' + f
            ge = None  # type: ignore[var-annotated]
            attempts = 5
            # NOTE: ugh. sometimes it just throws 500 on this endpoint for no reason, and then immediately after it works??
            # started happening around 20220305 :shrug:
            for _attempt in range(attempts):
                try:
                    return repo._requester.requestJsonAndCheck('GET', path)[1]
                except github.GithubException as ge:
                    if ge.status != 500:
                        raise ge
            assert ge is not None
            raise ge

        traffic = {f: fetch(f) for f in traffic_fields}
        return traffic


def get_json(**kwargs) -> Json:
    return Exporter(**kwargs).export_json()  # ty: ignore[missing-argument]


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(
        token=params['token'],
        include=args.include,
        include_repos_traffic=args.include_repos_traffic,
    )
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


def make_parser() -> argparse.ArgumentParser:
    parser = Parser(
        '''
Export your Github personal data: issues, PRs, comments, followers and followings, etc.

*Note*: this only deals with metadata. If you want a download of actual git repositories, I recommend using [[https://github.com/josegonzalez/python-github-backup][python-github-backup]].
'''.strip()
    )
    # TODO repositories?
    setup_parser(
        parser=parser,
        params=['token'],
        extra_usage='''
You can also import ~ghexport.export~ as a module and call ~get_json~ function directly to get raw JSON.
        ''',
    )
    parser.add_argument('--include', nargs='+', choices=_ALL_FIELDS, help='Only include specific export fields (exports all by default).')

    tgroup = parser.add_mutually_exclusive_group()
    tgroup.add_argument('--include-repos-traffic', dest='include_repos_traffic', action='store_true')
    tgroup.add_argument('--exclude-repos-traffic', dest='include_repos_traffic', action='store_false')
    parser.set_defaults(include_repos_traffic=None)

    return parser


if __name__ == '__main__':
    main()
