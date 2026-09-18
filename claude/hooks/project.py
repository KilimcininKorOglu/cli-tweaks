"""
Shared project identity for the hooks.

Every hook that keys data by project uses the same name, so that memory,
notifications and the session lock always agree. The name is the basename of
the primary repository, also inside a git worktree, else the cwd basename.

session-start.py writes the name to a lock file keyed by the Claude Code
process id (the hooks' parent). The other hooks read that lock, so the name
stays fixed for the whole session even when the cwd moves.
"""
import os
import re
import subprocess
from pathlib import Path

LOCK_DIR = Path.home() / ".cli-tweaks" / ".session-locks"
REINJECT_COUNTER_DIR = Path.home() / ".cli-tweaks" / ".reinject-counter"


def runGit(cwd: str, *args: str) -> str:
    """Return the stripped stdout of a git command, or "" when git fails.

    A directory outside a git repository is a normal case, not an error, so a
    failed command falls back to the next way of naming the project.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _nameFromGitCommonDir(cwd: str) -> str:
    """Return the primary repository basename from the git common dir.

    In a worktree, `--show-toplevel` names the worktree, while the common dir is
    `<repo>/.git` of the primary repository.
    """
    commonDir = runGit(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not commonDir:
        return ""
    path = Path(commonDir).resolve()
    if path.name == ".git":
        return path.parent.name
    if path.parent.name == "worktrees" and path.parent.parent.name == ".git":
        return path.parent.parent.parent.name
    return ""


def resolveProjectName(cwd: str) -> str:
    """Return the primary repository basename, else the git root basename, else the cwd basename."""
    name = _nameFromGitCommonDir(cwd)
    if name:
        return name
    top = runGit(cwd, "rev-parse", "--show-toplevel")
    return os.path.basename(top) if top else os.path.basename(cwd)


def isValidProjectName(name: str) -> bool:
    """Return whether a lock value is safe to use as a project key.

    Agent subprocesses can inherit a lock keyed by their agent id, so a value
    that starts with `agent-` is not a project name.
    """
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+", name)) and not name.startswith("agent-")


def sessionLockFile() -> Path:
    """Return the lock file of this Claude Code session."""
    return LOCK_DIR / str(os.getppid())


def sessionProjectName(cwd: str) -> str:
    """Return the name locked at session start, else a freshly resolved name."""
    try:
        locked = sessionLockFile().read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        locked = ""
    return locked if isValidProjectName(locked) else resolveProjectName(cwd)


def _isAlive(pid: int) -> bool:
    """Return whether a process with this id exists."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def removeStaleProcessFiles(directory: Path) -> list[str]:
    """Delete the per-process files of Claude Code processes that no longer run.

    A session lock or a reinject counter outlives its session, and a later
    process can get the same id and read the old value. A file of a reused id
    whose process runs again is not found here; session-start.py rewrites the
    lock and resets the counter of its own process for that case. A file whose name is
    not a process id is left alone, because this function cannot tell whether
    it is stale. Returns one message per file that could not be deleted; the
    rest are still checked.
    """
    if not directory.is_dir():
        return []
    errors = []
    for path in directory.iterdir():
        if not path.name.isdigit() or _isAlive(int(path.name)):
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError as err:
            errors.append(f"cannot delete stale file {path}: {err}")
    return errors
