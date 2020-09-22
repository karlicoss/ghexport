#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Iterator, Sequence, Dict

import pytz


from .exporthelpers import dal_helper, logging_helper
from .exporthelpers.dal_helper import PathIsh, Json


logger = logging_helper.logger('ghexport')


# TODO move DAL bits from mypkg?
class DAL:
    """
    Github only seems to give away last 300 events via the API, so we need to merge them
    """
    def __init__(self, sources: Sequence[PathIsh]) -> None:
        # TODO rely on external sort?
        pathify = lambda s: s if isinstance(s, Path) else Path(s)
        self.sources = list(map(pathify, sources))

    # todo error handling?
    def events(self) -> Iterator[Json]:
        emitted: Dict[str, Json] = {}
        for src in self.sources:
            jj = json.loads(src.read_text())
            # quick hack to adapt for both old & new formats
            if 'events' in jj:
                jj = jj['events']

            # by default they come in descending order
            jj = list(sorted(jj, key=lambda e: e['id']))

            before = len(emitted)

            for e in jj:
                eid = e['id']
                prev = emitted.get(eid, None)
                if prev is None:
                    emitted[eid] = e
                    yield e
                elif prev != e:
                    # never actually encountered the so just a warning..
                    logger.warning('Mismatch: %s vs %s', prev, e)

            after = len(emitted)

            logger.info('%s: added %d out of %d events', src, (after - before), len(jj))
            # TODO merging by id could be sort of generic


def demo(dal: DAL):
    # TODO
    print("Your events:")
    from collections import Counter
    c = Counter(e['type'] for e in dal.events())
    from pprint import pprint
    pprint(c)


if __name__ == '__main__':
    dal_helper.main(DAL=DAL, demo=demo)
