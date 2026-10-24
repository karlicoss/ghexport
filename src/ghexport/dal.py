from __future__ import annotations

from collections.abc import Iterator, Sequence
from concurrent.futures import Executor
from pathlib import Path

import hpikit.cli.dal as cli
import koncurrent
from hpikit.json import Json, loads
from hpikit.paths import as_paths
from kloggy import get_logger
from kloggy.progress import progress

logger = get_logger(__name__)


def _process_path(path: Path) -> list[Json]:
    """
    Helper function to process one file -- needs to be on the top level in case ProcessPoolExecutor is used.
    """
    j = loads(path.read_bytes())
    # in old format we just dumped the list of events directly
    items = j if isinstance(j, list) else j['events']

    # by default they come in descending order
    return sorted(items, key=lambda e: e['id'])


# TODO expose subscriptions, falling back to watched for old exports.
# todo move DAL bits from hpi?
class DAL:
    """
    Github only seems to give away last 300 events via the API, so we need to merge them
    """

    def __init__(self, sources: Sequence[Path | str]) -> None:
        self.sources = as_paths(sources)

        # where to parse the files -- None means koncurrent's shared default, serial unless configured otherwise
        # set these before iterating to override, e.g. dal.executor = ThreadPoolExecutor(4)
        self.executor: Executor | None = None
        self.buffersize: int | None = None  # None: twice the executor's number of workers, or 1 when running serially

    # Yield file-loading errors so later sources can still be processed.
    def _raw(self) -> Iterator[tuple[Path, list[Json] | Exception]]:
        with koncurrent.map_results(
            _process_path, self.sources, executor=self.executor, buffersize=self.buffersize
        ) as results:
            # Track results as they are consumed, so queued executor work doesn't advance the bar prematurely.
            # Log each path before waiting for its result, including before parsing in serial mode.
            files = progress(self.sources, logger=logger, unit='files')
            for path, result in zip(files, results, strict=True):
                if isinstance(result, Exception):
                    result.add_note(f'^ while processing {path}')
                yield path, result

    def events(self) -> Iterator[Json | Exception]:
        emitted: dict[str, Json] = {}
        for path, group in self._raw():
            if isinstance(group, Exception):
                yield group
                continue
            # todo maybe info level should be a bit smarter? e.g. log that we're processing every few seconds or something, at least in interactive mode?
            before = len(emitted)

            for e in group:
                eid = e['id']
                prev = emitted.get(eid)
                if prev is None:
                    emitted[eid] = e
                    yield e
                elif prev != e:
                    # never actually encountered this, so just a warning..
                    logger.warning(f'{path}: mismatch {prev} vs {e}')

            after = len(emitted)

            logger.debug(f'{path}: added {after - before} out of {len(group)} events')
            # TODO how to configure logger via hpi?
            # TODO merging by id could be sort of generic


def demo(dal: DAL) -> None:
    from collections import Counter
    from pprint import pprint

    print("Your events:")
    c: Counter[str] = Counter()
    for event in dal.events():
        if isinstance(event, Exception):
            logger.error(event, exc_info=event)
            continue
        c[event['type']] += 1
    pprint(c)


if __name__ == '__main__':
    cli.main(DAL=DAL, demo=demo)
