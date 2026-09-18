#!/usr/bin/env python3
"""
PreToolUse hook: a path listed in the global gitignore can never enter git.

The policy is absolute, so the hook does not look for a force flag. It blocks
every route that could stage a protected path:
  - `git add` naming a protected path, with or without --force
  - `git add` whose operands cannot be proven safe (`.`, `-A`, a glob, a
    directory, a shell variable, --pathspec-from-file), because their contents
    are unknown here
  - `git update-index --add`, which stages without going through `git add`
  - `git -c core.excludesfile=...`, which disables the ignore file for one call
  - `git commit <path>`, `git commit -a` and `git mv` on a protected path, which
    is how an already-tracked protected file keeps moving forward
  - a Bash write to ~/.gitignore_global, or a `!` negation written into a
    repository .gitignore
  - a Write or Edit tool call whose target is ~/.gitignore_global

A path is protected the way git decides it: the last matching pattern wins, a
`!` pattern re-includes the path, and a path under an excluded directory stays
excluded. Paths are resolved against the `git -C` directory.

Matching is scoped to the command it belongs to, never the raw command text, and
option values such as a `-m` message are skipped, so a commit message that names
a protected path does not block the commit. Heredoc bodies are dropped for the
same reason. Any parse failure exits 0.
"""
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

SETTINGS_KEY = "hookProtectGitignore"
GITIGNORE_GLOBAL = "~/.gitignore_global"

OPERATORS = {"|", "||", "&&", ";", ";;", "&", "(", ")", "{", "}", "!", "\n"}
OPERATOR_CHARS = set("|&;()")
OPERATOR_RUN = re.compile(r"\|\||&&|;;|[|&;()]")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
HEREDOC = re.compile(r"<<-?\s*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?")
WRAPPERS = {"sudo", "command", "env", "time", "nice", "nohup", "builtin", "exec"}

FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
STAGE_ALL_FLAGS = {"-A", "--all", "-u", "--update", "--no-ignore-removal"}
MUTATORS = {"rm", "mv", "cp", "tee", "truncate", "install", "dd", "ln", "sed", "gsed"}
GLOB_CHARS = "*?["
GIT_TIMEOUT_SECONDS = 5

# Options that take the next token as their value, per subcommand. The value is
# a message, a commit or a mode, never a path to check.
SHORT_VALUE_OPTS = {
    "add": "",
    "commit": "mFCct",
    "mv": "",
}
LONG_VALUE_OPTS = {
    "add": {"chmod", "pathspec-from-file"},
    "commit": {
        "message", "file", "reuse-message", "reedit-message", "fixup", "squash",
        "author", "date", "template", "cleanup", "trailer", "pathspec-from-file",
        "inter-hunk-context",
    },
    "mv": set(),
}

ADVICE = (
    "A path in the global gitignore can never enter git. Remove the pattern from "
    "{ignore} if the file really must be tracked; never work around the ignore "
    "file. If the path is already tracked from before, untrack it with "
    "`git rm --cached <path>` instead of staging it again."
)


def isEnabled(settingsFile):
    """Return True unless the settings file explicitly turns the guard off."""
    try:
        data = json.loads(settingsFile.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return True
    if not isinstance(data, dict) or SETTINGS_KEY not in data:
        return True
    value = data.get(SETTINGS_KEY)
    if value is True or value is False:
        return value
    print(
        f"git-protect: {SETTINGS_KEY} must be true or false, got {value!r}; guard stays on",
        file=sys.stderr,
    )
    return True


def stripHeredocs(command):
    """Drop heredoc bodies so a commit message cannot look like a command."""
    lines = command.splitlines()
    out = []
    index = 0
    while index < len(lines):
        out.append(lines[index])
        match = HEREDOC.search(lines[index])
        index += 1
        if not match:
            continue
        delimiter = match.group(1)
        while index < len(lines) and lines[index].strip() != delimiter:
            index += 1
        index += 1
    return "\n".join(out)


def splitStatements(command):
    """Turn unquoted newlines into `;` so each line stays its own command."""
    out = []
    quote = ""
    escaped = False
    for char in command:
        if escaped:
            out.append(char)
            escaped = False
        elif char == "\\" and quote != "'":
            out.append(char)
            escaped = True
        elif quote:
            out.append(char)
            quote = "" if char == quote else quote
        elif char in "'\"":
            quote = char
            out.append(char)
        else:
            out.append(" ; " if char == "\n" else char)
    return "".join(out)


def splitOperators(tokens):
    """Split a run of operator characters that shlex returns as one token.

    shlex joins adjacent punctuation, so `(cd sub); git add x` yields `);`,
    which is no operator; without the split, the git call would be missed.
    """
    out = []
    for token in tokens:
        if token and token not in OPERATORS and set(token) <= OPERATOR_CHARS:
            out.extend(OPERATOR_RUN.findall(token))
        else:
            out.append(token)
    return out


def tokenize(command):
    """Return shell tokens with operators separated, or None when unparseable."""
    normalized = splitStatements(stripHeredocs(command))
    lexer = shlex.shlex(normalized, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return splitOperators(list(lexer))
    except ValueError:
        return None


def segments(tokens):
    """Split tokens into (command, words) pairs, one per shell command."""
    groups = []
    current = []
    for token in tokens:
        if token in OPERATORS:
            if current:
                groups.append(current)
            current = []
            continue
        current.append(token)
    if current:
        groups.append(current)

    parsed = []
    for words in groups:
        index = 0
        while index < len(words) and (
            ASSIGNMENT.match(words[index]) or os.path.basename(words[index]) in WRAPPERS
        ):
            index += 1
        if index < len(words):
            parsed.append((os.path.basename(words[index]), words[index:]))
    return parsed


def readIgnoredEntries():
    """Return the patterns of the global gitignore in file order, negations included."""
    path = os.path.expanduser(GITIGNORE_GLOBAL)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except (OSError, UnicodeDecodeError) as err:
        print(f"git-protect: cannot read {path}: {err}", file=sys.stderr)
        return []
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def matchKind(path, entry):
    """Return "path" when the entry covers the path itself, "parent" when it
    covers a parent directory, else ""."""
    pattern = entry.rstrip("/")
    if not pattern:
        return ""
    # Strip only a leading "./", never with lstrip, which would also eat the
    # leading dot of a path like ".factory/settings.json".
    normalized = path
    while normalized.startswith("./"):
        normalized = normalized[2:]
    parts = [part for part in normalized.split("/") if part not in ("", ".", "..")]
    if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(path, pattern):
        return "path"
    if parts and fnmatch.fnmatch(parts[-1], pattern):
        return "path"
    if any(fnmatch.fnmatch(part, pattern) for part in parts[:-1]):
        return "parent"
    return ""


def protectedEntry(path, entries):
    """Return the gitignore entry that excludes this path, else ''.

    The last matching pattern wins. A `!` pattern re-includes the path, but a
    path under an excluded directory stays excluded, as in git.
    """
    byPath = ""
    byParent = ""
    for entry in entries:
        negated = entry.startswith("!")
        kind = matchKind(path, entry[1:] if negated else entry)
        if kind == "parent":
            byParent = "" if negated else entry
        elif kind == "path":
            byPath = "" if negated else entry
    return byParent or byPath


def unprovableReason(operand, cwd):
    """Return why an operand's contents cannot be proven safe, else ''."""
    if operand in (".", "..", ":/", ":", "*"):
        return f"`{operand}` stages whatever it contains"
    if any(char in operand for char in GLOB_CHARS):
        return f"the glob `{operand}` can expand onto a protected path"
    if "$" in operand or "`" in operand:
        return f"`{operand}` is expanded by the shell and cannot be checked here"
    if operand.endswith("/") or os.path.isdir(os.path.join(cwd, operand)):
        return f"the directory `{operand}` stages whatever it contains"
    return ""


def gitSubcommand(words, cwd):
    """Return (subcommand, args, cwd) for a git invocation.

    git's own options are skipped, and every `-C <dir>` moves the directory the
    path operands are resolved against, as git does.
    """
    rest = words[1:]
    cursor = 0
    while cursor < len(rest) and rest[cursor].startswith("-"):
        option = rest[cursor]
        if option == "-C" and cursor + 1 < len(rest):
            cwd = os.path.join(cwd, os.path.expanduser(rest[cursor + 1]))
        cursor += 2 if option in GIT_VALUE_OPTS else 1
    if cursor >= len(rest):
        return "", [], cwd
    return rest[cursor], rest[cursor + 1:], cwd


def shortOption(arg, shortValues):
    """Return (flag letters, consumesNext) for one short option cluster.

    A value letter ends the cluster: its value is the rest of the token, or the
    next token when the letter is last.
    """
    letters = arg[1:]
    for index, letter in enumerate(letters):
        if letter in shortValues:
            return letters[:index], index == len(letters) - 1
    return letters, False


def parseArgs(subcommand, args):
    """Return (operands, flags) of a git subcommand, skipping option values."""
    shortValues = SHORT_VALUE_OPTS.get(subcommand, "")
    longValues = LONG_VALUE_OPTS.get(subcommand, set())
    operands = []
    flags = set()
    index = 0
    while index < len(args):
        arg = args[index]
        index += 1
        if arg == "--":
            operands.extend(args[index:])
            break
        if arg.startswith("--"):
            name = arg[2:].split("=")[0]
            flags.add("--" + name)
            index += 1 if name in longValues and "=" not in arg else 0
        elif arg.startswith("-") and len(arg) > 1:
            letters, consumes = shortOption(arg, shortValues)
            flags.update("-" + letter for letter in letters)
            index += 1 if consumes else 0
        else:
            operands.append(arg)
    return operands, flags


def checkExcludesOverride(words):
    """Block `git -c core.excludesfile=...`, which disables the ignore file."""
    for word in words:
        if word.lower().startswith("core.excludesfile="):
            return f"`{word}` disables the global gitignore for this call"
    return ""


def checkOperands(subcommand, operands, entries):
    """Return the reason one operand names a protected path, else ''."""
    for operand in operands:
        entry = protectedEntry(operand, entries)
        if entry:
            return f"`git {subcommand}` touches `{operand}`, covered by the gitignore entry `{entry}`"
    return ""


def checkStagingPaths(args, entries, cwd):
    """Block a `git add` that names a protected or unprovable path."""
    operands, flags = parseArgs("add", args)
    if "--pathspec-from-file" in flags:
        return "`git add --pathspec-from-file` reads its paths from a file that cannot be checked here"
    if not operands and flags & STAGE_ALL_FLAGS:
        return "`git add` with a stage-all flag stages whatever is present"
    reason = checkOperands("add", operands, entries)
    if reason:
        return reason
    for operand in operands:
        reason = unprovableReason(operand, cwd)
        if reason:
            return reason
    return ""


def trackedChanges(cwd):
    """Return the tracked files with changes, which `git commit -a` stages."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or f"git diff exited {result.returncode}")
    return result.stdout.splitlines()


def checkCommit(args, entries, cwd):
    """Block a commit that moves a protected path forward."""
    operands, flags = parseArgs("commit", args)
    if "--pathspec-from-file" in flags:
        return "`git commit --pathspec-from-file` reads its paths from a file that cannot be checked here"
    if not flags & {"-a", "--all"}:
        return checkOperands("commit", operands, entries)
    try:
        changed = trackedChanges(cwd)
    except (OSError, subprocess.TimeoutExpired) as err:
        return f"`git commit -a` stages every tracked change, and they cannot be listed here ({err})"
    return checkOperands("commit -a", operands + changed, entries)


def checkGit(words, entries, cwd):
    """Return the reason a git invocation must be blocked, else ''."""
    override = checkExcludesOverride(words)
    if override:
        return override
    subcommand, args, cwd = gitSubcommand(words, cwd)
    if subcommand == "add":
        return checkStagingPaths(args, entries, cwd)
    if subcommand == "update-index" and "--add" in args:
        return "`git update-index --add` stages without going through `git add`"
    if subcommand == "commit":
        return checkCommit(args, entries, cwd)
    if subcommand == "mv":
        return checkOperands("mv", parseArgs("mv", args)[0], entries)
    return ""


def touchesGlobalIgnore(words):
    """True when a word names the global gitignore file."""
    return any(".gitignore_global" in word for word in words)


def isWriting(command, words):
    """True when this segment writes a file rather than reading one."""
    return command in MUTATORS or any(word in (">", ">>") for word in words)


def checkGlobalIgnoreWrite(command, words):
    """Block a Bash write to the global gitignore file itself."""
    if touchesGlobalIgnore(words) and isWriting(command, words):
        return f"this command rewrites {GITIGNORE_GLOBAL}"
    return ""


def checkGitignoreNegation(command, words, entries):
    """Block a `!` negation of a protected path written into a .gitignore."""
    if not any(word.endswith(".gitignore") for word in words):
        return ""
    if not isWriting(command, words):
        return ""
    for word in words:
        if word.startswith("!") and protectedEntry(word[1:].strip(), entries):
            return f"`{word}` would un-ignore a protected path in a .gitignore"
    return ""


def checkIgnoreFileWrite(command, words, entries):
    """Block any Bash route that weakens the ignore rules themselves."""
    return checkGlobalIgnoreWrite(command, words) or checkGitignoreNegation(
        command, words, entries
    )


def analyzeBash(command, entries, cwd):
    """Return every reason this Bash command must be blocked."""
    tokens = tokenize(command)
    if tokens is None:
        return []
    reasons = []
    for name, words in segments(tokens):
        reason = checkGit(words, entries, cwd) if name == "git" else ""
        if not reason:
            reason = checkIgnoreFileWrite(name, words, entries)
        if reason and reason not in reasons:
            reasons.append(reason)
    return reasons


def analyzeFileTool(toolInput):
    """Block a Write or Edit call whose target is the global gitignore."""
    path = toolInput.get("file_path", "")
    if not isinstance(path, str) or not path:
        return ""
    target = os.path.realpath(os.path.expanduser(GITIGNORE_GLOBAL))
    if os.path.realpath(os.path.expanduser(path)) == target:
        return f"this edit rewrites {GITIGNORE_GLOBAL}"
    return ""


def collectReasons(data):
    """Return every reason this tool call must be blocked."""
    toolInput = data.get("tool_input", {})
    if not isinstance(toolInput, dict):
        return []
    toolName = data.get("tool_name", "")
    if toolName in FILE_TOOLS:
        reason = analyzeFileTool(toolInput)
        return [reason] if reason else []
    if toolName != "Bash":
        return []
    command = toolInput.get("command", "")
    if not isinstance(command, str) or not command.strip():
        return []
    cwd = data.get("cwd") or os.getcwd()
    return analyzeBash(command, readIgnoredEntries(), cwd)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return 0
    if not isinstance(data, dict):
        return 0

    if not isEnabled(Path.home() / ".factory" / "settings.json"):
        return 0

    reasons = collectReasons(data)
    if not reasons:
        return 0

    # Exit code 2 forces a PreToolUse block: Droid ignores stdout, feeds
    # stderr back to the model as the reason, and aborts the tool call. A
    # {"decision": {"behavior": "block"}} JSON object is not a recognized
    # PreToolUse outcome and is silently ignored, so the action proceeds.
    print(
        "BLOCKED by git-protect: {}.\n\n{}".format(
            "; ".join(reasons), ADVICE.format(ignore=GITIGNORE_GLOBAL)
        ),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
