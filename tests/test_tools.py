import tempfile
from pathlib import Path

from agent.tools import dispatch, grep, list_dir, read_file, write_file


def test_read_write_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file("foo.txt", "hello", root)
        result = read_file("foo.txt", root)
        assert result.ok
        assert result.output == "hello"


def test_grep_finds_pattern():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file("code.py", "def add(a, b):\n    pass\n", root)
        result = grep("def add", root)
        assert result.ok
        assert "code.py" in result.output


def test_list_dir():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file("a.py", "", root)
        result = list_dir(".", root)
        assert result.ok
        assert "a.py" in result.output


def test_path_escape_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            read_file("../../etc/passwd", root)
            assert False, "should raise"
        except ValueError:
            pass


def test_dispatch_read():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file("x.py", "1", root)
        result = dispatch("read", {"path": "x.py"}, root)
        assert result.ok
