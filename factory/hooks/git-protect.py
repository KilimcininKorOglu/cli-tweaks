#!/usr/bin/env python3
"""
PreToolUse hook: blocks `git add -f` / `git add --force` on files
listed in the global gitignore. Prevents Claude from bypassing
gitignore protection with force-add.

Matching is scoped to the `git add` invocation itself, never the whole command
string. An earlier version searched the raw text, so a commit message that
merely mentioned a force flag or a protected directory name blocked the commit.
Heredoc bodies are dropped for the same reason.
"""
import fnmatch
import json
import os
import re
import shlex
import sys

OPERATORS = {"|", "||", "&&", ";", ";;", "&", "(", ")", "{", "}", "!", "\n"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
HEREDOC = re.compile(r"<<-?\s*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?")
WRAPPERS = {"sudo", "command", "env", "time", "nice", "nohup", "builtin", "exec"}
FORCE_FLAGS = {"--force"}


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
        index += 1  # skip the closing delimiter line
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
            continue
        if char == "\\" and quote != "'":
            out.append(char)
            escaped = True
            continue
        if quote:
            out.append(char)
            if char == quote:
                quote = ""
            continue
        if char in "'\"":
            quote = char
            out.append(char)
            continue
        out.append(" ; " if char == "\n" else char)
    return "".join(out)


def gitAddArguments(command):
    """Return the argument list of every `git add` invocation in the command."""
    normalized = splitStatements(stripHeredocs(command))
    normalized = normalized.replace("$(", " ( ").replace("`", " ( ")
    lexer = shlex.shlex(normalized, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return []

    invocations = []
    current = []
    for token in tokens:
        if token in OPERATORS:
            if current:
                invocations.append(current)
            current = []
            continue
        current.append(token)
    if current:
        invocations.append(current)

    found = []
    for words in invocations:
        index = 0
        while index < len(words) and (
            ASSIGNMENT.match(words[index]) or os.path.basename(words[index]) in WRAPPERS
        ):
            index += 1
        if index >= len(words) or os.path.basename(words[index]) != "git":
            continue
        rest = words[index + 1:]
        # Skip git's own options (`-C path`, `--no-pager`) to reach the subcommand.
        cursor = 0
        while cursor < len(rest) and rest[cursor].startswith("-"):
            cursor += 2 if rest[cursor] in ("-C", "-c", "--git-dir", "--work-tree") else 1
        if cursor < len(rest) and rest[cursor] == "add":
            found.append(rest[cursor + 1:])
    return found


def hasForceFlag(args):
    """True when this `git add` carries -f or --force, bundled forms included."""
    for arg in args:
        if arg == "--":
            return False
        if arg in FORCE_FLAGS:
            return True
        if arg.startswith("--"):
            continue
        if arg.startswith("-") and len(arg) > 1 and "f" in arg[1:]:
            return True
    return False


def pathOperands(args):
    """Return the non-option operands of a `git add` invocation."""
    operands = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            operands.extend(args[index + 1:])
            break
        if arg.startswith("-") and len(arg) > 1:
            index += 1
            continue
        operands.append(arg)
        index += 1
    return operands


def matchesEntry(path, entry):
    """True when a staged path is covered by one gitignore entry."""
    pattern = entry.rstrip("/")
    if not pattern:
        return False
    # Strip only a leading "./", never with lstrip, which would also eat the
    # leading dot of a path like ".claude/settings.json".
    normalized = path
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(path, pattern):
        return True
    parts = [part for part in normalized.split("/") if part not in ("", ".", "..")]
    return any(fnmatch.fnmatch(part, pattern) for part in parts)


def readIgnoredEntries():
    gitignorePath = os.path.expanduser("~/.gitignore_global")
    if not os.path.isfile(gitignorePath):
        return []
    try:
        with open(gitignorePath, "r") as handle:
            return [
                line.strip()
                for line in handle
                if line.strip()
                and not line.startswith("#")
                and not line.startswith("!")
            ]
    except OSError:
        return []


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return 0
    if data.get("tool_name") != "Bash":
        return 0

    command = data.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or "add" not in command:
        return 0

    forced = [args for args in gitAddArguments(command) if hasForceFlag(args)]
    if not forced:
        return 0

    entries = readIgnoredEntries()
    if not entries:
        return 0

    matched = []
    for args in forced:
        for path in pathOperands(args):
            for entry in entries:
                if matchesEntry(path, entry) and entry not in matched:
                    matched.append(entry)

    if not matched:
        return 0

    # Exit code 2 forces a PreToolUse block: Droid ignores stdout, feeds
    # stderr back to the model as the reason, and aborts the tool call. A
    # {"decision": {"behavior": "block"}} JSON object is not a recognized
    # PreToolUse outcome and is silently ignored, so the force-add proceeds.
    print(
        "BLOCKED: force-add on protected file(s): {}. "
        "These files are in the global gitignore for a reason. "
        "Analyze the root cause of the error instead of forcing them in.".format(
            ", ".join(matched)
        ),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
