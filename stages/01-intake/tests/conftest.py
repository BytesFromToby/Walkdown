import subprocess
import sys
from pathlib import Path

import pytest

STAGE = Path(__file__).resolve().parents[1]
if str(STAGE) not in sys.path:
    sys.path.insert(0, str(STAGE))

def git(*args, cwd=None):
    """git for building a local origin: a fixed identity, no signing, no prompts."""
    p = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "commit.gpgsign=false", *args], cwd=cwd, capture_output=True,
                       text=True, check=True)
    return p.stdout.strip()


class Origin:
    """A local git repository standing in for a remote. `url` is a file:// URL ending in .git,
    so Walkdown takes it for a URL, as it would a remote's."""

    def __init__(self, root: Path):
        self.work = root / "origin-work"
        self.work.mkdir()
        self.bare = root / "origin.git"
        self.url = self.bare.as_uri()
        git("init", "-q", "--bare", "-b", "main", str(self.bare))
        git("init", "-q", "-b", "main", cwd=self.work)
        git("remote", "add", "origin", str(self.bare), cwd=self.work)

    def commit(self, name: str, text: str, branch: str = "main") -> str:
        """Write one file on `branch`, commit it, publish it; returns the commit."""
        try:
            git("checkout", "-q", branch, cwd=self.work)
        except subprocess.CalledProcessError:  # a new branch starts where the work folder is
            git("checkout", "-q", "-b", branch, cwd=self.work)
        path = self.work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        git("add", "-A", cwd=self.work)
        git("commit", "-q", "-m", f"change {name}", cwd=self.work)
        git("push", "-q", "-f", "origin", branch, cwd=self.work)
        return git("rev-parse", "HEAD", cwd=self.work)


@pytest.fixture
def origin(tmp_path):
    """A local origin holding one commit (SKILL.md, "version one")."""
    o = Origin(tmp_path)
    o.commit("SKILL.md", "version one\n")
    return o
