import json
from pathlib import Path

from ..dal import DAL


def test_events_continue_after_bad_file(tmp_path: Path) -> None:
    first = tmp_path / 'first.json'
    first.write_text(json.dumps([{'id': '2'}, {'id': '1'}]))
    broken = tmp_path / 'broken.json'
    broken.write_text('{')
    last = tmp_path / 'last.json'
    last.write_text(json.dumps({'events': [{'id': '3'}, {'id': '2'}]}))

    [one, two, error, three] = DAL([first, broken, last]).events()
    assert isinstance(error, Exception)
    assert [one, two, three] == [{'id': '1'}, {'id': '2'}, {'id': '3'}]
