from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path

from .exporthelpers import dal_helper, logging_helper
from .exporthelpers.dal_helper import Json, PathIsh, json_items, pathify

logger = logging_helper.make_logger(__name__)


# todo move DAL bits from hpi?
class DAL:
    """
    Github only seems to give away last 300 events via the API, so we need to merge them
    """

    def __init__(self, sources: Sequence[PathIsh]) -> None:
        self.sources = list(map(pathify, sources))

    def _sources(self) -> Iterator[Path]:
        pbar = logging_helper.get_enlighten().counter(total=len(self.sources), desc=f'{__name__}', unit='files')

        # hmm. this is a bit meh, but will trial it for now and if it suits us, come up with some proper encapsulation
        terminal = getattr(getattr(pbar, 'manager', object()), 'companion_term', object())
        # if we're using tty or a Mock (no enlighten, or it's turned off), this will be False
        use_enlighten = terminal.__class__.__name__ == 'Terminal'
        log_src = logger.debug if use_enlighten else logger.info

        for src in self.sources:
            log_src(f'{src} : processing...')
            pbar.update()
            yield src

    # todo error handling?
    def events(self) -> Iterator[Json]:
        emitted: dict[str, Json] = {}
        # todo maybe info level should be a bit smarter? e.g. log that we're processing every few seconds or something, at least in interactive mode?
        for src in self._sources():
            with src.open(mode='rb') as fo:
                first = fo.read(1)
            old_format = first == b'['
            extractor = None if old_format else 'events'
            jj = list(json_items(src, extractor))

            # by default they come in descending order
            jj = sorted(jj, key=lambda e: e['id'])

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

            logger.debug('%s: added %d out of %d events', src, (after - before), len(jj))
            # TODO how to configure logger via hpi?
            # TODO merging by id could be sort of generic


def demo(dal: DAL) -> None:
    from collections import Counter
    from pprint import pprint

    print("Your events:")
    c = Counter(e['type'] for e in dal.events())
    pprint(c)


if __name__ == '__main__':
    dal_helper.main(DAL=DAL, demo=demo)
