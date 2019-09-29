#!/usr/bin/env python3
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple, Sequence, Any, Iterator, Dict, Union
from glob import glob
import json
import logging

from kython import setup_logzero

import pytz

def get_logger():
    return logging.getLogger('ghexport')


PathIsh = Union[str, Path]
Json = Dict[str, Any]


class Model:
    """
    Github only seems to give away last 300 events via the API, so we need to merge them
    """
    def __init__(self, sources: Sequence[PathIsh]) -> None:
        # TODO rely on external sort?
        self.sources = list(map(Path, sources))

    # TODO rename to iter_?
    def events(self) -> Iterator[Json]:
        logger = get_logger()

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


# def main():
#     logger = get_logger()
#     setup_logzero(logger, level=logging.DEBUG)
#     import argparse
#     p = argparse.ArgumentParser()
#     p.add_argument('--source', type=str, required=True)
#     p.add_argument('--no-glob', action='store_true')
#     args = p.parse_args()
# 
#     if '*' in args.source and not args.no_glob:
#         sources = glob(args.source)
#     else:
#         sources = [args.source]
# 
#     src = Path(max(sources))
# 
#     logger.debug('using %s', src)
#     model = Model([src])
# 
# 
# 
# 
# if __name__ == '__main__':
#     main()
