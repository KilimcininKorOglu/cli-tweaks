"""
Shared reading of the global instruction files for the hooks.

session-start.py injects these files once per session start, and
memory-reinject.py repeats them in long sessions. Both read the same
`globalInjectFiles` list of ~/.factory/settings.json, so the two never disagree
about which files are the user's global instructions.
"""
import json
import os
from pathlib import Path

SETTINGS_FILE = Path.home() / ".factory" / "settings.json"


def globalInjectFiles(errors: list[str]) -> list[str]:
    """Return the `globalInjectFiles` list of the user settings."""
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        errors.append(f"cannot read {SETTINGS_FILE}: {err}")
        return []
    files = data.get("globalInjectFiles", []) if isinstance(data, dict) else None
    if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
        errors.append(f"globalInjectFiles in {SETTINGS_FILE} is not a list of paths")
        return []
    return files


def readInstructions(fileList: list[str], errors: list[str]) -> list[str]:
    """Return one block per readable, non-empty instruction file."""
    contents = []
    for filePath in fileList:
        path = Path(os.path.expanduser(filePath))
        try:
            content = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError) as err:
            errors.append(f"cannot read global instruction file {filePath}: {err}")
            continue
        if content:
            contents.append(f"# From {filePath}\n{content}")
    return contents
