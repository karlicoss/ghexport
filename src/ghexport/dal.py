from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from concurrent.futures import Executor
from pathlib import Path

from more_itertools import chunked

from .exporthelpers import dal_helper, logging_helper
from .exporthelpers.dal_helper import Json, json_items, pathify

logger = logging_helper.make_logger(__name__)


def _process_path(path: Path) -> list[Json]:
    """
    Helper function to process one file -- needs to be on the top level in case ProcessPoolExecutor is used.
    """
    with path.open(mode='rb') as fo:
        first = fo.read(1)
    # in old format we just dumped the list of events directly
    old_format = first == b'['
    extractor = None if old_format else 'events'
    items = json_items(path, extractor)

    # by default they come in descending order
    return sorted(items, key=lambda e: e['id'])


# TODO expose subscriptions, falling back to watched for old exports.
# todo move DAL bits from hpi?
class DAL:
    """
    Github only seems to give away last 300 events via the API, so we need to merge them
    """

    def __init__(self, sources: Sequence[Path | str], *, executor: Executor | None = None) -> None:
        """
        executor: optional Executor (e.g. ThreadPoolExecutor) to use for CPU-bound tasks (e.g. parsing json).
        """
        self.sources = list(map(pathify, sources))
        self.executor = executor
        self.enlighten = logging_helper.get_enlighten()

    # todo error handling?
    def _raw(self) -> Iterator[tuple[Path, list[Json]]]:
        progress_bar = self.enlighten.counter(total=len(self.sources), desc=f'{__name__}', unit='files')

        executor = self.executor
        _map = map if executor is None else executor.map
        workers = 1 if executor is None else getattr(executor, '_max_workers')

        total = len(self.sources)
        width = len(str(total))

        # hmm. this is a bit meh, but will trial it for now and if it suits us, come up with some proper encapsulation
        terminal = getattr(getattr(progress_bar, 'manager', object()), 'companion_term', object())
        # if we're using tty or a Mock (no enlighten, or it's turned off), this will be False
        use_enlighten = terminal.__class__.__name__ == 'Terminal'
        log_src = logger.debug if use_enlighten else logger.info

        def logged_sources() -> Iterable[Path]:
            # helper iterator to log source paths before passing to the executor
            # makes is a bit easier, e.g. don't have to pass log message to the function we run on executor
            # TODO on the other hand if the executor is busy might be a little misleading (since we'll log way before processing)
            # but on the other hand it also makes it a bit more obvious we're waiiting for it so idk
            for idx, path in enumerate(self.sources):
                log_src(f'processing [{idx:>{width}}/{total:>{width}}] {path}')
                yield path

        # Batch input data by the amount of available workers.
        # This is to make sure that in case of slow consumer, results don't build up and we won't run out of memory.
        for chunk in chunked(logged_sources(), n=workers):
            results = _map(_process_path, chunk)
            for path, group in zip(chunk, results, strict=True):
                progress_bar.update()
                yield path, group

    def events(self) -> Iterator[Json]:
        emitted: dict[str, Json] = {}
        for path, group in self._raw():
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
    c = Counter(e['type'] for e in dal.events())
    pprint(c)


if __name__ == '__main__':
    dal_helper.main(DAL=DAL, demo=demo)
