#!/usr/bin/env python3
"""
Usage: parallel -j8 '/path/to/split_traffic.py {}' ::: *.json.zst
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import kompress  # ty: ignore[unresolved-import]


def main() -> None:
    fname = Path(sys.argv[1])

    jdata = json.loads(kompress.CPath(fname).read_text())

    if isinstance(jdata, list):
        print("old format, no traffic data", fname)
        return

    repos = jdata['repos']
    has_traffic = any('traffic' in r for r in repos)
    if not has_traffic:
        # just leave intact
        print("new format, no traffic data", fname)
        return

    m = re.fullmatch(r'events_(\d+T\d+Z).json.zst', fname.name)
    assert m is not None, fname
    ts = m.group(1)

    stat = fname.stat()
    (atime_ns, mtime_ns) = stat.st_atime_ns, stat.st_mtime_ns

    traffic_file = fname.parent / 'traffic' / f'{ts}.json.zst'

    repos_with_traffic = json.dumps({'repos': repos}, ensure_ascii=False, indent=1)

    for r in repos:
        # modifies in place
        assert 'traffic' in r, r
        del r['traffic']

    data_without_traffic = json.dumps(jdata, ensure_ascii=False, indent=1)

    ZSTD = ['zstd', '-19', '--quiet', '--force', '-o']  # force to overwrite existing

    print("Writing out to ", fname, traffic_file)
    subprocess.run(
        [*ZSTD, traffic_file],
        check=True,
        input=repos_with_traffic.encode('utf8'),
    )
    os.utime(traffic_file, ns=(atime_ns, mtime_ns))

    subprocess.run(
        [*ZSTD, fname],
        check=True,
        input=data_without_traffic.encode('utf8'),
    )
    os.utime(fname, ns=(atime_ns, mtime_ns))


if __name__ == '__main__':
    main()
